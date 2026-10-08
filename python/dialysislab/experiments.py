"""Real experiment broker: immutable runs, external administration and bounded history."""
import argparse
import copy
import fcntl
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import hmac
import json
import math
import os
from pathlib import Path
import secrets
import shutil
import signal
import socket
import socketserver
import subprocess
import sys
import threading
import time
import zipfile
from . import experiment_rpc as wire
from .protocol import pause, wait_ready, rpc, expect
from .runner import ROOT, LocalCluster, build_identity, simulate, stop_plant, validate
from .trajectory import canonical, scan, strict_json

MAX_RUNS = 1024
MAX_EVENTS = 10000
MAX_STORED_JSON = 1048576
STATES = ('starting', 'running', 'pause_requested', 'paused', 'stopping')


def now(): return datetime.now(timezone.utc).isoformat()


def atomic(path, value):
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')
    temporary.replace(path)


def keys(value, expected):
    if not isinstance(value, dict) or set(value) != set(expected.split()): raise ValueError('request keys')


def bounded_json(path):
    with path.open('rb') as stream: raw = stream.read(MAX_STORED_JSON + 1)
    if len(raw) > MAX_STORED_JSON: raise ValueError('stored JSON size limit')
    return strict_json(raw)


def configuration(value):
    if len(canonical(value).encode()) > wire.MAX_JSON: raise ValueError('configuration size limit')
    validate(value)
    if value['schema_version'] != 5: raise ValueError('experiment requires schema 5')
    return json.loads(canonical(value))


class Broker:
    def __init__(self, build_dir, output, activation=None, runtime=None):
        self.build_dir, self.output = Path(build_dir).resolve(), Path(output).resolve()
        self.output.mkdir(parents=True, exist_ok=True)
        lock_path = self.output / '.broker.lock'
        self.owner_lock = os.open(lock_path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
        try: fcntl.flock(self.owner_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            os.close(self.owner_lock)
            raise ValueError('result directory already owned by a broker')
        self.activation = Path(activation).resolve() if activation else None
        self.runtime_root = Path(runtime).resolve() if runtime else None
        self.lock = threading.RLock()
        self.run_id, self.state, self.latest, self.received_at = '-', 'idle', None, None
        self.requested_pause, self.requested_stop = False, False
        self.worker, self.current_runtime, self.events = None, None, 0
        self.draft = configuration(bounded_json(ROOT / 'scenarios/machine_hd.json'))
        self.epoch = secrets.token_hex(16)
        # Exact opaque decimal: 128-bit incarnation and bounded 32-bit counter.
        self.revision = (int(self.epoch, 16) << 32) + 1
        self.revision_limit = (int(self.epoch, 16) << 32) + 2**32 - 1
        self.history, self.requests, self.incomplete = {}, {}, []
        self.closing = False
        self.job = dict(id='-', state='idle')
        self.job_thread = None
        for directory in sorted(self.output.glob('r*')):
            if not wire.IDENTIFIER.fullmatch(directory.name) or not directory.is_dir() or directory.is_symlink():
                continue
            try:
                meta = bounded_json(directory / 'experiment.json')
                if (meta['run_id'] != directory.name or meta['state'] not in (*STATES, 'completed', 'aborted', 'interrupted')
                        or not wire.REQUEST_ID.fullmatch(meta['request_id'])
                        or not isinstance(meta['request_fingerprint'], str)
                        or len(meta['request_fingerprint']) != 64
                        or datetime.fromisoformat(meta['created_at']).tzinfo is None):
                    raise ValueError('experiment metadata schema')
            except (OSError, ValueError, KeyError, TypeError, RecursionError) as exc:
                self.incomplete.append(dict(run_id=directory.name, error=type(exc).__name__ + ': ' + str(exc),
                                            state='quarantined_in_place', recovery='Preserve this directory; metadata is incomplete or invalid. No automatic run/replay.'))
                continue
            if meta['state'] in STATES:
                meta.update(state='interrupted', error='broker restart; prior stop unconfirmed', finished_at=now())
                atomic(directory / 'experiment.json', meta)
            self.history[directory.name] = meta
            self.requests[meta['request_id']] = (meta['request_fingerprint'], directory.name)
        if len(self.history) + len(self.incomplete) > MAX_RUNS:
            os.close(self.owner_lock); self.owner_lock = None
            raise ValueError('result inventory exceeds 1024 runs')
        if self.activation:
            self.activation.mkdir(parents=True, exist_ok=True)
            atomic(self.activation / 'active.json', {'schema_version': 1, 'run_id': None})

    def event(self, action):
        if self.events >= MAX_EVENTS: raise ValueError('event journal limit; stop remains available')
        self.events += 1
        data = dict(event=self.events, wall_at=now(), action=action,
                    next_sequence=0 if self.latest is None else self.latest['sequence'] + 1)
        with (self.output / self.run_id / 'events.jsonl').open('a') as stream:
            stream.write(canonical(data))

    def event_failure(self, exc):
        """Evidence failures cannot veto physical stop or terminal metadata."""
        meta = self.history[self.run_id]
        issue = meta.setdefault('journal_error', dict(count=0, last=None))
        issue['count'] += 1
        issue['last'] = type(exc).__name__ + ': ' + str(exc)

    def status(self):
        with self.lock:
            return copy.deepcopy(dict(schema_version=1, revision=self.revision, broker_epoch=self.epoch,
                        run_id=self.run_id, state=self.state,
                        sequence=-1 if self.latest is None else self.latest['sequence'],
                        virtual_time_ms=0 if self.latest is None else self.latest['time_ms'],
                        truth=self.latest, wall_sample_age_s=None if self.received_at is None else time.monotonic()-self.received_at,
                        job=self.job, experiment=self.history.get(self.run_id), simulation_only=True,
                        incomplete_runs=self.incomplete[-100:], incomplete_run_count=len(self.incomplete)))

    def directory(self, identifier):
        if not isinstance(identifier, str) or not wire.IDENTIFIER.fullmatch(identifier) or identifier not in self.history:
            raise ValueError('unknown run identifier')
        path = self.output / identifier
        if path.is_symlink() or not path.is_dir(): raise ValueError('unsafe run directory')
        return path

    def start(self, config, request_id, fingerprint, speed, replay_of=None):
        if self.closing: raise ValueError('broker stopping; new work rejected')
        if not isinstance(request_id, str) or not wire.REQUEST_ID.fullmatch(request_id): raise ValueError('request identifier')
        if request_id in self.requests:
            old, identifier = self.requests[request_id]
            if old != fingerprint: raise ValueError('request identifier reused with different arguments')
            return dict(run_id=identifier, duplicate=True)
        if self.state in STATES: raise ValueError('an experiment is active')
        if len(self.history) + len(self.incomplete) >= MAX_RUNS: raise ValueError('1024-run inventory limit; use a new result directory')
        if type(speed) not in (int, float) or not math.isfinite(speed) or not 0 <= speed <= 1000:
            raise ValueError('wall_speed range [0,1000]')
        config = configuration(config)
        identity = build_identity(self.build_dir)
        identifier = 'r' + secrets.token_hex(8)
        directory = self.output / identifier
        directory.mkdir()
        atomic(directory / 'configuration.json', config)
        meta = dict(schema_version=1, run_id=identifier, state='starting', created_at=now(),
                    request_id=request_id, request_fingerprint=fingerprint, replay_of=replay_of,
                    configuration_sha256=hashlib.sha256(canonical(config).encode()).hexdigest(),
                    build=identity, wall_speed=speed, pacing_owner='experiment_broker', scheduled=True,
                    stop=None, error=None)
        atomic(directory / 'experiment.json', meta)
        self.history[identifier] = meta
        self.requests[request_id] = (fingerprint, identifier)
        self.run_id, self.state, self.latest, self.received_at = identifier, 'starting', None, None
        self.requested_pause = self.requested_stop = False
        self.events = 0
        try:
            self.event('start')
            self.worker = threading.Thread(target=self.execute, args=(identifier, config, speed), daemon=False)
            self.worker.start()
        except (OSError, ValueError, RuntimeError) as exc:
            self.event_failure(exc)
            if self.worker and not self.worker.is_alive(): self.worker = None
            self.state = 'aborted'
            meta.update(state='aborted', error='start failed before activation: ' + str(exc), finished_at=now())
            atomic(directory / 'experiment.json', meta)
            raise
        return dict(run_id=identifier, duplicate=False)

    @contextmanager
    def cluster(self, identifier, directory):
        logs = directory / 'logs'
        logs.mkdir()
        if self.activation:
            # Role supervisors alone create fresh sockets; the broker only links
            # already authorised volumes into a short private runtime directory.
            runtime = self.runtime_root / 'sessions' / identifier
            runtime.mkdir(parents=True)
            for role in ('admin', 'control', 'protection', 'patient'):
                (runtime / role).symlink_to(self.runtime_root / role / identifier)
            (runtime / 'device').mkdir()
            for role in ('control', 'protection'):
                (runtime / 'device' / (role + '.sock')).symlink_to(
                    self.runtime_root / 'device' / role / identifier / 'service.sock')
            atomic(self.activation / 'active.json', {'schema_version': 1, 'run_id': identifier})
            try:
                wait_ready(runtime)
                yield runtime
            finally:
                atomic(self.activation / 'active.json', {'schema_version': 1, 'run_id': None})
                # Supervisors acknowledge exited children before copying complete logs.
                deadline = time.monotonic() + 5
                for role in ('plant', 'control', 'protection', 'patient'):
                    owner = 'admin' if role == 'plant' else role
                    target = self.runtime_root / owner / identifier
                    while not (target / 'exited.json').exists() and time.monotonic() < deadline:
                        time.sleep(.02)
                    for name in (role + '.log', 'exited.json'):
                        path = target / name
                        if path.is_file(): shutil.copyfile(path, logs / (role + '-' + name))
        else:
            with LocalCluster(self.build_dir) as cluster:
                try: yield cluster.runtime
                finally:
                    for process in cluster.processes.values():
                        if process.poll() is None: process.terminate()
                    for process in cluster.processes.values():
                        try: process.wait(timeout=3)
                        except subprocess.TimeoutExpired: process.kill(); process.wait(timeout=3)
                    for path in cluster.runtime.glob('*.log'):
                        shutil.copyfile(path, logs / path.name)

    def execute(self, identifier, config, speed):
        directory = self.output / identifier
        manifest = None
        try:
            with self.cluster(identifier, directory) as runtime:
                with self.lock: self.current_runtime = runtime
                deadline = time.monotonic()
                def barrier(n):
                    nonlocal deadline
                    while True:
                        with self.lock:
                            if self.requested_stop: raise InterruptedError('experiment stop requested')
                            paused = self.requested_pause
                            if paused:
                                if self.state != 'paused': self.state = 'paused'; self.event('paused')
                                deadline = time.monotonic()
                            else:
                                self.state = 'running'
                        remaining = deadline - time.monotonic() if speed else 0
                        if not paused and remaining <= 0: break
                        if paused:
                            reply=rpc(runtime/'control/service.sock','CHECK7')
                            if reply==['REJECT','external_stop']:
                                raise InterruptedError('device STOP during virtual pause')
                            expect(reply,'OK',1)
                        pause(runtime, .05 if paused else min(.05, remaining))
                    if speed: deadline = time.monotonic() + config['dt_ms'] / (1000 * speed)
                def record(value):
                    with self.lock: self.latest, self.received_at = value, time.monotonic()
                _, manifest = simulate(config, runtime, self.build_dir, directory / 'data',
                                       before_tick=barrier, after_record=record, scheduled=True, external_pacing_speed=speed)
                stop = manifest.get('stop') or stop_plant(runtime / 'admin/plant.sock', True)
                manifest['stop'] = stop
                if not stop['outputs_zero_observed']:
                    manifest['outcome'] = 'aborted'
                    manifest['errors'].append('final stop not observed')
                atomic(directory / 'data/manifest.json', manifest)
                with self.lock:
                    meta = self.history[identifier]
                    meta.update(state=manifest['outcome'], stop=stop, completed_ticks=manifest['completed_ticks'],
                                trajectory_sha256=manifest['trajectory_sha256'], error=manifest['errors'])
        except Exception as exc:
            with self.lock:
                self.history[identifier].update(state='aborted', error=type(exc).__name__ + ': ' + str(exc))
        finally:
            with self.lock:
                meta = self.history[identifier]
                meta['finished_at'] = now()
                self.state, self.current_runtime = meta['state'], None
                try:
                    self.event(self.state)
                except (OSError, ValueError) as exc:
                    self.event_failure(exc)
                try:
                    atomic(directory / 'experiment.json', meta)
                except OSError as exc:
                    self.state = 'aborted'
                    meta['error'] = 'evidence write failed: ' + str(exc)

    def verify(self, identifier):
        directory = self.directory(identifier)
        meta = bounded_json(directory / 'experiment.json')
        if meta['state'] in STATES: raise ValueError('run still active')
        config = configuration(bounded_json(directory / 'configuration.json'))
        manifest = bounded_json(directory / 'data/manifest.json')
        if config != manifest['configuration'] or meta['configuration_sha256'] != hashlib.sha256(canonical(config).encode()).hexdigest():
            raise ValueError('configuration evidence mismatch')
        if manifest['configuration_sha256'] != meta['configuration_sha256']: raise ValueError('manifest digest mismatch')
        for key in ('build', 'trajectory_sha256', 'completed_ticks', 'scheduled', 'stop', 'wall_speed', 'pacing_owner'):
            if key not in meta or key not in manifest or meta[key] != manifest[key]:
                raise ValueError('experiment/manifest identity mismatch: ' + key)
        if meta['run_id'] != identifier or meta['state'] != manifest['outcome']:
            raise ValueError('experiment/manifest outcome mismatch')
        if meta['state'] == 'completed':
            observed = manifest['stop'].get('observed_state') or {}
            if (manifest['completed_ticks'] != config['ticks'] or not manifest['scheduled']
                    or not manifest['stop'].get('outputs_zero_observed') or not observed.get('latched')
                    or not observed.get('clamp_closed') or observed.get('blood_mL_min') != 0
                    or observed.get('uf_mL_min') != 0 or observed.get('online', {}).get('replacement_mL_min') != 0):
                raise ValueError('completed experiment lacks observed stopped outputs')
        measured = scan(directory / 'data/trajectory.jsonl')
        if (measured['records'] != manifest['completed_ticks'] or measured['sha256'] != manifest['trajectory_sha256']
                or measured['complete_bytes'] != manifest['trajectory_bytes']): raise ValueError('trajectory evidence mismatch')
        return directory, meta, manifest, measured

    def compare(self, left, right):
        _, a, ma, sa = self.verify(left)
        _, b, mb, sb = self.verify(right)
        same_config = ma['configuration'] == mb['configuration']
        same_build = ma['build'] == mb['build']
        eligible = all(m['outcome'] == 'completed' and meta['state'] == 'completed' and m.get('scheduled')
                       and m['completed_ticks'] == m['configuration']['ticks'] for meta, m in ((a, ma), (b, mb)))
        delta = None
        if sa['last'] and sb['last']:
            delta = sb['last']['patient_volume_mL'] - sa['last']['patient_volume_mL']
        return dict(left=left, right=right, same_configuration=same_config, same_build=same_build,
                    exact_trajectory=sa['sha256'] == sb['sha256'], replay_eligible=eligible,
                    exact_replay=eligible and same_config and same_build and sa['sha256'] == sb['sha256'],
                    patient_volume_difference_mL=delta, records=[sa['records'], sb['records']])

    def export(self, identifier):
        directory = self.directory(identifier)
        meta = bounded_json(directory / 'experiment.json')
        if meta['state'] in STATES: raise ValueError('run still active')
        config = configuration(bounded_json(directory / 'configuration.json'))
        if hashlib.sha256(canonical(config).encode()).hexdigest() != meta['configuration_sha256']:
            raise ValueError('export configuration mismatch')
        manifest_path = directory / 'data/manifest.json'
        recovery = None
        if not manifest_path.exists() and meta['state'] in ('aborted', 'interrupted'):
            recovery = dict(status='no_run_manifest', outputs_zero_observed=None,
                            note='Failure before run artifacts were available; only existing evidence is exported.')
        elif meta['state'] in ('aborted', 'interrupted') and bounded_json(manifest_path)['outcome'] == 'running':
            measured = scan(directory / 'data/trajectory.jsonl', recover=True)
            recovery = dict(status='recovered_complete_prefix', outputs_zero_observed=None,
                            prefix={k:v for k,v in measured.items() if k not in ('first','last')},
                            note='Original interrupted bytes/manifest retained; this does not establish final outputs or completed-run integrity.')
        else:
            self.verify(identifier)
        exports = self.output / 'exports'
        exports.mkdir(exist_ok=True)
        target = exports / (identifier + '.zip')
        temporary = target.with_suffix('.tmp')
        names = ['configuration.json', 'experiment.json', 'events.jsonl', 'data/manifest.json', 'data/trajectory.jsonl']
        names += ['logs/' + role + '.log' for role in ('plant', 'control', 'protection', 'patient')]
        names += ['logs/' + role + '-' + name for role in ('plant', 'control', 'protection', 'patient') for name in (role+'.log', 'exited.json')]
        with zipfile.ZipFile(temporary, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=1) as archive:
            if recovery: archive.writestr('recovery.json', canonical(recovery))
            for name in names:
                source = directory / name
                if source.is_symlink(): raise ValueError('symlink in export')
                if source.is_file(): archive.write(source, name)
        temporary.replace(target)
        hasher = hashlib.sha256()
        with target.open('rb') as stream:
            for block in iter(lambda: stream.read(65536), b''): hasher.update(block)
        return dict(file='exports/' + target.name, bytes=target.stat().st_size, sha256=hasher.hexdigest(),
                    integrity='interrupted_available_evidence' if recovery else 'verified_manifest_and_trajectory')

    def begin_job(self, op, args):
        if self.job['state'] == 'running': raise ValueError('artifact job already active')
        for identifier in args.values():
            self.directory(identifier)
            if self.history[identifier]['state'] in STATES: raise ValueError('run still active')
        identifier = secrets.token_hex(8)
        self.job = dict(id=identifier, state='running', operation=op)
        def execute():
            try:
                result = self.compare(args['left'], args['right']) if op == 'COMPARE' else self.export(args['run_id'])
                status = dict(id=identifier, state='completed', operation=op, result=result)
            except Exception as exc: status = dict(id=identifier, state='failed', operation=op, error=str(exc))
            with self.lock: self.job = status
        self.job_thread = threading.Thread(target=execute, daemon=False)
        self.job_thread.start()
        return dict(job_id=identifier)

    def dispatch(self, op, args):
        with self.lock:
            if self.closing and op not in ('STATUS', 'RUNS', 'STOP'): raise ValueError('broker stopping; new work rejected')
            if op == 'STATUS': keys(args, ''); return self.status()
            if op == 'PRESETS':
                keys(args, '')
                return [p.stem for p in sorted((ROOT / 'scenarios').glob('machine_*.json')) if '100000' not in p.stem]
            if op == 'DRAFT': keys(args, ''); return self.draft
            if op == 'LOAD':
                keys(args, 'name revision')
                if type(args['revision']) is not int or args['revision'] != self.revision: raise ValueError('stale draft revision')
                if self.revision == self.revision_limit: raise ValueError('revision budget exhausted; restart broker')
                if args['name'] not in self.dispatch('PRESETS', {}): raise ValueError('unknown preset')
                self.draft = configuration(bounded_json(ROOT / 'scenarios' / (args['name'] + '.json')))
                self.revision += 1
                return self.draft
            if op == 'VALIDATE':
                keys(args, 'configuration revision')
                if type(args['revision']) is not int or args['revision'] != self.revision: raise ValueError('stale draft revision')
                if self.revision == self.revision_limit: raise ValueError('revision budget exhausted; restart broker')
                self.draft = configuration(args['configuration']); self.revision += 1
                return self.draft
            if op == 'START':
                keys(args, 'revision request_id wall_speed')
                fp = hashlib.sha256(canonical(dict(op=op, args=args)).encode()).hexdigest()
                if args['request_id'] not in self.requests and (type(args['revision']) is not int or args['revision'] != self.revision):
                    raise ValueError('stale draft revision')
                return self.start(self.draft, args['request_id'], fp, args['wall_speed'])
            if op == 'RUNS':
                keys(args, '')
                return [dict(run_id=identifier, state=meta['state'], created_at=meta['created_at'], replay_of=meta['replay_of'])
                        for identifier, meta in sorted(self.history.items(), key=lambda item:(datetime.fromisoformat(item[1]['created_at']),item[0]))[-100:]]
            if op in ('PAUSE', 'RESUME', 'STOP'):
                keys(args, 'run_id')
                if args['run_id'] != self.run_id or self.state not in STATES: raise ValueError('stale or inactive run')
                if op == 'STOP':
                    self.requested_stop, self.state = True, 'stopping'
                    try: self.event('stop_requested')
                    except (OSError, ValueError) as exc: self.event_failure(exc)
                    return dict(run_id=self.run_id, state=self.state, journal_error=self.history[self.run_id].get('journal_error'))
                self.event(op.lower())
                if op == 'PAUSE': self.requested_pause, self.state = True, 'pause_requested'
                elif op == 'RESUME': self.requested_pause, self.state = False, 'running'
                return dict(run_id=self.run_id, state=self.state)
            if op == 'REPLAY':
                keys(args, 'run_id request_id wall_speed')
                source = self.directory(args['run_id'])
                meta = self.history[args['run_id']]
                if meta['state'] != 'completed': raise ValueError('only a completed scheduled experiment can replay')
                config = bounded_json(source / 'configuration.json')
                # Full trajectory checks run in the artifact job before comparisons;
                # replay itself uses exactly the immutable accepted configuration.
                if hashlib.sha256(canonical(config).encode()).hexdigest() != meta['configuration_sha256']:
                    raise ValueError('replay configuration mismatch')
                fp = hashlib.sha256(canonical(dict(op=op, args=args)).encode()).hexdigest()
                return self.start(config, args['request_id'], fp, args['wall_speed'], args['run_id'])
            if op in ('COMPARE', 'EXPORT'):
                keys(args, 'left right' if op == 'COMPARE' else 'run_id')
                return self.begin_job(op, args)
            raise ValueError('unknown administrative operation')

    def close(self):
        with self.lock: self.closing, self.requested_stop = True, True
        if self.worker: self.worker.join(timeout=15)
        if self.job_thread: self.job_thread.join(timeout=30)
        if self.worker and self.worker.is_alive(): raise RuntimeError('experiment worker did not stop')
        if self.job_thread and self.job_thread.is_alive(): raise RuntimeError('artifact worker did not stop; output ownership retained')
        if self.owner_lock is not None:
            os.close(self.owner_lock)
            self.owner_lock = None


class Server(socketserver.ThreadingMixIn, socketserver.UnixStreamServer):
    daemon_threads = True
    request_queue_size = 4
    def __init__(self, directory, broker):
        self.broker = broker
        self.slots = threading.BoundedSemaphore(4)
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        if directory.is_symlink(): raise ValueError('unsafe administrative directory')
        self.path = directory / 'broker.sock'
        if self.path.exists() or self.path.is_symlink(): raise ValueError('existing broker socket; refuse implicit takeover')
        self.token = secrets.token_hex(32)
        token_path = directory / 'token'
        if token_path.is_symlink(): raise ValueError('unsafe credential file')
        fd = os.open(token_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, 'w') as stream: stream.write(self.token + '\n')
        super().__init__(str(self.path), Handler)
        os.chmod(self.path, 0o600)

    def process_request(self, request, address):
        if not self.slots.acquire(blocking=False): request.close(); return
        try: super().process_request(request, address)
        except BaseException: self.slots.release(); raise

    def process_request_thread(self, request, address):
        try: super().process_request_thread(request, address)
        finally: self.slots.release()

    def server_close(self):
        super().server_close()
        self.path.unlink(missing_ok=True)


class Handler(socketserver.BaseRequestHandler):
    def handle(self):
        self.request.settimeout(2)
        authenticated = False
        try:
            fields = wire.line(self.request).split(' ')
            if len(fields) != 4 or fields[0] != 'DX1': raise ValueError('request frame schema')
            if not wire.TOKEN.fullmatch(fields[1]) or not hmac.compare_digest(fields[1], self.server.token):
                raise ValueError('unauthorized')
            authenticated = True
            with self.server.broker.lock:
                result = self.server.broker.dispatch(fields[2], wire.decode(fields[3]))
                status = self.server.broker.status()
                if fields[2] in ('START', 'REPLAY'):
                    # A retried request may identify an older run; never attach
                    # an unrelated current run ID to its authoritative reply.
                    status['run_id'] = result['run_id']
            kind = 'OK'
        except (ValueError, OSError, KeyError, TypeError, OverflowError, RecursionError) as exc:
            result, kind = {'error': type(exc).__name__ + ': ' + str(exc)}, 'ERROR'
            status = (self.server.broker.status() if authenticated else
                      dict(revision=0,run_id='-',state='unauthorized',sequence=-1,virtual_time_ms=0))
        # Fixed metadata lets a tiny C++ console display the complete JSON without
        # a second independent model/configuration JSON parser.
        try:
            reply = 'DX1 {} {} {} {} {} {} {}\n'.format(kind, status['revision'], status['run_id'], status['state'],
                status['sequence'], status['virtual_time_ms'], wire.payload(result))
            self.request.sendall(reply.encode('ascii'))
        except (OSError, ValueError): pass


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build-dir', type=Path, default=ROOT / 'build/gui')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--api-dir', type=Path, required=True)
    parser.add_argument('--activation-dir', type=Path)
    parser.add_argument('--runtime-dir', type=Path)
    args = parser.parse_args()
    if bool(args.activation_dir) != bool(args.runtime_dir): parser.error('activation and runtime must be supplied together')
    broker = Broker(args.build_dir, args.output, args.activation_dir, args.runtime_dir)
    server = Server(args.api_dir, broker)
    server.timeout = .1
    stopping = threading.Event()
    def stop(_signal, _frame): stopping.set()
    signal.signal(signal.SIGTERM, stop); signal.signal(signal.SIGINT, stop)
    try:
        while not stopping.is_set(): server.handle_request()
    finally:
        try: broker.close()
        finally: server.server_close()


if __name__ == '__main__': main()
