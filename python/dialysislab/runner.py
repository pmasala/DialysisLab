"""Deterministic barrier scheduler and build/configuration-specific run records."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import resource
import signal
import subprocess
import sys
import tempfile
import time
from .protocol import expect, heartbeat, integer, observation, pause, real, rpc, state, wait_ready
from .trajectory import FORMAT, TrajectoryWriter, canonical, strict_json

ROOT = Path(__file__).resolve().parents[2]
FAULTS = {'none', 'invalid', 'missing', 'stale', 'future', 'replay'}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def validate(config):
    if isinstance(config, dict) and config.get('schema_version') == 5:
        from .machine import validate as validate_machine
        return validate_machine(config, validate)
    if isinstance(config, dict) and config.get('schema_version') == 4:
        from .treatment import validate as validate_treatment
        return validate_treatment(config, validate)
    if isinstance(config, dict) and config.get('schema_version') == 3:
        from .compartments import validate_scenario
        return validate_scenario(config, validate)
    if isinstance(config, dict) and config.get('schema_version') == 2:
        from .circuit import validate as validate_circuit
        return validate_circuit(config, validate)
    required = {'schema_version', 'model', 'seed', 'ticks', 'dt_ms', 'blood_mL_min', 'uf_mL_min',
                'resistance_mmHg_min_mL', 'pressure_limit_mmHg', 'patient_volume_mL', 'faults'}
    if not isinstance(config, dict) or set(config) != required:
        raise ValueError('configuration keys')
    if type(config['schema_version']) is not int or config['schema_version'] != 1 or config['model'] != 'm1-hd-1':
        raise ValueError('configuration version/model')
    for key, low, high in [('seed', 0, 2**32 - 1), ('ticks', 1, 100000), ('dt_ms', 1, 1000)]:
        if type(config[key]) is not int or not low <= config[key] <= high:
            raise ValueError('configuration integer: ' + key)
    for key, low, high in [('blood_mL_min', 0, 500), ('uf_mL_min', 0, 20),
                           ('resistance_mmHg_min_mL', 0.01, 100), ('pressure_limit_mmHg', 1, 1000),
                           ('patient_volume_mL', 1000, 100000)]:
        value = config[key]
        if type(value) not in (int, float) or not math.isfinite(value) or not low <= value <= high:
            raise ValueError('configuration range: ' + key)
    faults = config['faults']
    if not isinstance(faults, list):
        raise ValueError('fault timeline')
    seen = set()
    for fault in faults:
        if not isinstance(fault, dict) or set(fault) != {'tick', 'target', 'value'}:
            raise ValueError('fault schema')
        if type(fault['tick']) is not int or not 0 <= fault['tick'] < config['ticks']:
            raise ValueError('fault tick')
        pair = (fault['tick'], fault['target'])
        if pair in seen:
            raise ValueError('duplicate fault')
        seen.add(pair)
        if fault['target'] == 'resistance':
            if type(fault['value']) not in (int, float):
                raise ValueError('resistance type')
            real(fault['value'], 0.01, 100)
        elif fault['target'] in ('control_sensor', 'protection_sensor'):
            if fault['value'] not in FAULTS:
                raise ValueError('sensor fault')
        else:
            raise ValueError('fault target')
    return config


class LocalCluster:
    """Native integration fixture; process identities are NOT isolated by UID."""
    def __init__(self, build_dir):
        self.build_dir = Path(build_dir).resolve()
        self.temporary = None
        self.processes = {}
        self.logs = []

    def __enter__(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='dl-m1-')
        self.runtime = Path(self.temporary.name)
        for role in ('admin', 'control', 'protection', 'patient', 'device'):
            (self.runtime / role).mkdir()
        for role in ('control', 'protection'):
            (self.runtime / 'device' / role).mkdir()
            (self.runtime / 'device' / (role + '.sock')).symlink_to(Path(role) / 'service.sock')
        env = dict(os.environ, PYTHONPATH=str(ROOT / 'python'), PYTHONDONTWRITEBYTECODE='1')
        try:
            for role in ('plant', 'control', 'protection', 'patient'):
                command = ([sys.executable, '-m', 'dialysislab.patient'] if role == 'patient'
                           else [str(self.build_dir / role)])
                log = (self.runtime / (role + '.log')).open('w')
                self.logs.append(log)
                guarded = [str(self.build_dir / 'child-guard'), str(os.getpid())] + command
                self.processes[role] = subprocess.Popen(guarded + ['--runtime-dir', str(self.runtime)],
                                                       env=env, stdout=log, stderr=log)
            wait_ready(self.runtime)
            return self
        except BaseException:
            for path in sorted(self.runtime.glob('*.log')):
                print(path.name + ': ' + path.read_text(), file=sys.stderr)
            self.__exit__(*sys.exc_info())
            raise

    def kill(self, role):
        self.processes[role].kill()
        self.processes[role].wait(timeout=3)

    def __exit__(self, *_exc):
        for proc in self.processes.values():
            if proc.poll() is None:
                proc.terminate()
        for proc in self.processes.values():
            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=3)
        for log in self.logs:
            log.close()
        diagnostics = []
        if self.temporary:
            for path in self.runtime.glob('*.log'):
                content = path.read_text()
                if any(marker in content for marker in ('AddressSanitizer', 'LeakSanitizer', 'runtime error:')):
                    diagnostics.append(path.name + ': ' + content)
        if self.temporary:
            self.temporary.cleanup()
        if diagnostics:
            raise RuntimeError('Service sanitizer diagnostics:\n' + '\n'.join(diagnostics))


def build_identity(build_dir):
    path = Path(build_dir) / 'build_identity.json'
    if not path.is_file():
        raise ValueError('missing build identity; reconfigure CMake')
    identity = json.loads(path.read_text())
    identity['binary_sha256'] = {role: digest((Path(build_dir) / role).read_bytes())
                                 for role in ('plant', 'control', 'protection')}
    identity['child_guard_sha256'] = digest((Path(build_dir) / 'child-guard').read_bytes())
    # Identify the Python code actually executing, including native post-build edits.
    identity['python_sha256'] = {str(p.relative_to(ROOT)): digest(p.read_bytes())
                                 for p in sorted((ROOT / 'python/dialysislab').glob('*.py'))}
    return identity


def stop_plant(admin, online=False):
    """Keep HALT acknowledgment separate from an actual STATUS observation."""
    result = dict(command='HALT', requested=True, acknowledged=False,
                  request_error=None, observed_state=None, observation_error=None,
                  outputs_zero_observed=None, pending_tick_cancelled=None)
    try:
        expect(rpc(admin, 'HALT'), 'OK', 1)
        result['acknowledged'] = True
        result['pending_tick_cancelled'] = True
    except (OSError, ValueError) as exc:
        result['request_error'] = type(exc).__name__ + ': ' + str(exc)
    try:
        if online:
            from .treatment import live
            observed = live(rpc(admin, 'STATUS4'))
        else:
            observed = state(rpc(admin, 'STATUS'))
        result['observed_state'] = observed
        result['outputs_zero_observed'] = (observed['latched'] and observed['clamp_closed']
                                          and observed['blood_mL_min'] == 0 and observed['uf_mL_min'] == 0
                                          and (not online or observed['online']['replacement_mL_min'] == 0))
    except (OSError, ValueError) as exc:
        result['observation_error'] = type(exc).__name__ + ': ' + str(exc)
    return result


def simulate(config, runtime, build_dir, output=None, before_tick=None, wall_speed=0, wait_check=None,
             after_record=None, scheduled=False, external_pacing_speed=None):
    validate(config)
    if not isinstance(wall_speed, (int, float)) or not math.isfinite(wall_speed) or not 0 <= wall_speed <= 1000:
        raise ValueError('wall speed must be finite in [0,1000]; zero means unpaced')
    if external_pacing_speed is not None:
        if (wall_speed != 0 or type(external_pacing_speed) not in (int, float)
                or not math.isfinite(external_pacing_speed) or not 0 <= external_pacing_speed <= 1000):
            raise ValueError('external pacing must be finite [0,1000] with internal pacing disabled')
    runtime = Path(runtime)
    manifest = dict(schema_version=2, executed_at=datetime.now(timezone.utc).isoformat(),
                    configuration=config, configuration_sha256=digest(canonical(config).encode()),
                    build=build_identity(build_dir), python=platform.python_version(),
                    platform=platform.platform(), interface='DL1', model=config['model'],
                    simulation_only=True, outcome='running', errors=[],
                    trajectory_format=FORMAT, trajectory_file='trajectory.jsonl',
                    completed_ticks=0, trajectory_sha256=None,
                    wall_speed=wall_speed if external_pacing_speed is None else external_pacing_speed,
                    pacing_owner='runner' if external_pacing_speed is None else 'experiment_broker', scheduled=scheduled)
    writer = TrajectoryWriter(output)
    records = writer.trajectory
    writer.write_manifest(manifest)
    admin = runtime / 'admin/plant.sock'
    patient = runtime / 'patient/service.sock'
    resistance = config['resistance_mmHg_min_mL']
    sensor = dict(control_sensor='none', protection_sensor='none')
    pending_plant_state = None
    tick_context = None
    extended = config['schema_version'] >= 2
    coupled = config['schema_version'] >= 3
    online = config['schema_version'] >= 4
    lifecycle = config['schema_version'] >= 5
    patient_snapshot = None
    try:
        wait_ready(runtime)
        if scheduled:
            if not lifecycle: raise ValueError('scheduled experiment requires schema 5')
            for role in ('control', 'protection'):
                expect(rpc(runtime / role / 'service.sock', 'SCHEDULE7'), 'OK', 1)
        if extended:
            from . import circuit
            circuit.configure(admin, config)
        if online:
            from . import treatment
            treatment.configure(admin, config)
        if lifecycle:
            from . import machine
            machine.configure(admin, config)
        if coupled:
            from .compartments import validate_snapshot
            expect(rpc(patient, 'INIT5' if lifecycle else 'INIT4' if online else 'INIT3', canonical(config['patient'])), 'OK', 1)
        else:
            expect(rpc(patient, 'INIT', config['patient_volume_mL']), 'OK', 1)
        wall_start = time.monotonic()
        for n in range(config['ticks']):
            t = n * config['dt_ms']
            tick_context = dict(sequence=n, time_ms=t)
            if wall_speed:
                delay = wall_start + n * config['dt_ms'] / (1000 * wall_speed) - time.monotonic()
                # Cancellation checks do not run before_tick repeatedly: that
                # hook may contain one-shot scenario actions. Virtual time stays
                # frozen while bounded wall waits continue liveness heartbeats.
                deadline = time.monotonic() + max(0, delay)
                while time.monotonic() < deadline:
                    if wait_check: wait_check()
                    pause(runtime, min(.1, max(0, deadline - time.monotonic())))
                if wait_check: wait_check()
            if before_tick:
                before_tick(n)
            event = next((e for e in config['workflow'] if e['tick'] == n), None) if lifecycle else None
            workflow_request = machine.request(runtime, event, scheduled) if event else None
            if coupled and patient_snapshot is not None:
                circuit.transport(admin, config, patient_snapshot['concentration_mmol_L'][2])
            for fault in config['faults']:
                if fault['tick'] == n:
                    if lifecycle and fault['target'].startswith('device:'):
                        expect(rpc(admin, 'FAULT5', fault['target'][7:], fault['value']), 'OK', 1)
                    elif online and fault['target'].startswith('online:'):
                        expect(rpc(admin, 'FAULT4', fault['target'][7:], fault['value']), 'OK', 1)
                    elif extended and fault['target'].startswith('edge:'):
                        expect(rpc(admin, 'EDGE2', int(fault['target'][5:]), fault['value']['resistance'],
                                   int(fault['value']['closed'])), 'OK', 1)
                    elif fault['target'] == 'resistance':
                        resistance = fault['value']
                    else:
                        sensor[fault['target']] = fault['value']
            expect(rpc(admin, 'PREPARE', n, t, config['dt_ms'], resistance,
                       sensor['control_sensor'], sensor['protection_sensor']), 'OK', 1)
            measurements = {role: (machine.observation if lifecycle else treatment.observation if online else observation)(rpc(runtime / role / 'plant.sock', 'SENSE5' if lifecycle else 'SENSE4' if online else 'SENSE', n, t))
                            for role in ('control', 'protection')}
            failures = []
            try:
                extra = [] if lifecycle else [config['blood_mL_min'], config['uf_mL_min']] + ([config['treatment']['replacement_mL_min'], treatment.MODES.index(config['treatment']['mode'])] if online else [])
                expect(rpc(runtime / 'control/service.sock', 'STEP5' if lifecycle else 'STEP4' if online else 'STEP', n, t, *extra), 'OK', 1)
            except (OSError, ValueError) as exc:
                failures.append('control:' + type(exc).__name__)
            try:
                extra = [] if lifecycle else [config['pressure_limit_mmHg']] + ([treatment.MODES.index(config['treatment']['mode'])] if online else [])
                decision = expect(rpc(runtime / 'protection/service.sock', 'STEP5' if lifecycle else 'STEP4' if online else 'STEP', n, t, *extra), 'DECISION', 2)[1]
            except (OSError, ValueError) as exc:
                decision = 'unavailable'
                failures.append('protection:' + type(exc).__name__)
            tick_context.update(protection_decision=decision, observations=measurements)
            if failures:
                manifest['rpc_failures'] = failures
                raise RuntimeError(','.join(failures))
            if workflow_request and workflow_request['delivery'] == 'queued':
                role = 'protection' if event['action'] == 'RESET' else 'control'
                intent = machine.view(rpc(runtime / role / 'service.sock', 'OPERATOR7', 'STATUS5') if scheduled
                                      else rpc(runtime / 'device' / (role + '.sock'), 'STATUS5'))['intent']
                workflow_request['result'] = intent['result']
                if intent['result'] != 'applied': raise RuntimeError('workflow rejected: ' + intent['result'])
            physical = machine.committed(rpc(admin, 'COMMIT5', n, t)) if lifecycle else treatment.committed(rpc(admin, 'COMMIT4', n, t)) if online else (circuit.committed(rpc(admin, 'COMMIT3' if coupled else 'COMMIT2', n, t), coupled) if extended
                        else state(rpc(admin, 'COMMIT', n, t)))
            pending_plant_state = physical
            if physical['sequence'] != n or physical['time_ms'] != t + config['dt_ms']:
                raise ValueError('plant clock mismatch')
            water = physical['removed_tick_mL']
            if extended:
                if physical['circuit']['sequence'] != n or physical['circuit']['time_ms'] != t + config['dt_ms']:
                    raise ValueError('circuit clock mismatch')
                water = physical['circuit']['draw_tick_mL'] - physical['circuit']['return_tick_mL']
            if coupled:
                c = physical['circuit']
                transaction = dict(sequence=n, time_ms=t, dt_ms=config['dt_ms'], draw_mL=c['draw_tick_mL'],
                                   return_mL=c['return_tick_mL'], uf_mL=c['uf_tick_mL'], stored_mL=c['stored_mL'],
                                   clearance_mL_min=c['clearance_mL_min'], sieving=config['circuit']['profile']['sieving'],
                                   dialysate_mmol_L=config['transport']['dialysate_mmol_L'])
                if online:
                    o = physical['online']
                    if o['sequence'] != n or o['time_ms'] != t + config['dt_ms']:
                        raise ValueError('online clock mismatch')
                    transaction.update(pre_mL=o['pre_tick_mL'], post_mL=o['post_tick_mL'],
                                       substitution_mmol_L=o['concentration_mmol_L'], dialysate_mmol_L=o['concentration_mmol_L'])
                if lifecycle:
                    m = physical['machine']
                    transaction.update(flush_in_mL=m['flush_in_tick_mL'], flush_out_mL=m['flush_out_tick_mL'],
                                       flush_mmol_L=o['concentration_mmol_L'])
                    if m['stage'] in ('PRIMING', 'CLEANING'): transaction.update(draw_mL=0, return_mL=0)
                    physical['workflow_request'] = workflow_request
                reply = expect(rpc(patient, 'ADVANCE5' if lifecycle else 'ADVANCE4' if online else 'ADVANCE3', canonical(transaction)), 'PATIENT5' if lifecycle else 'PATIENT4' if online else 'PATIENT3', 2)
                patient_snapshot = validate_snapshot(strict_json(reply[1]), online, lifecycle)
                physical['patient'] = patient_snapshot
                volume = ['VOLUME', str(patient_snapshot['sequence']), str(patient_snapshot['time_ms']),
                          str(math.fsum(patient_snapshot['volume_mL'][:2])), str(patient_snapshot['net_patient_loss_mL'])]
            else:
                volume = expect(rpc(patient, 'FLUID2' if extended else 'ADVANCE', n, t, config['dt_ms'], water),
                                'FLUID_VOLUME2' if extended else 'VOLUME', 6 if extended else 5)
            if integer(volume[1]) != n or integer(volume[2]) != t + config['dt_ms']:
                raise ValueError('patient clock mismatch')
            if extended and not coupled:
                physical['patient_numerical_correction_mL'] = real(volume[5], -1e-8, 1e-8)
            record = dict(physical, patient_volume_mL=real(volume[3], 0, 100000),
                                patient_removed_mL=real(volume[4], -100000, 100000), observations=measurements,
                                protection_decision=decision)
            writer.append(record)
            pending_plant_state = None
            if after_record: after_record(record)
            if physical['reason'] in ('liveness', 'protocol', 'control_missing', 'protection_missing'):
                raise RuntimeError('unexpected plant failure: ' + physical['reason'])
        if extended:
            manifest['final_plant_observation'] = treatment.live(rpc(admin, 'STATUS4')) if online else state(rpc(admin, 'STATUS'))
            if manifest['final_plant_observation']['reason'] in ('liveness', 'protocol', 'control_missing', 'protection_missing'):
                raise RuntimeError('plant stopped after commit: ' + manifest['final_plant_observation']['reason'])
        if scheduled: expect(rpc(runtime / 'control/service.sock', 'CHECK7'), 'OK', 1)
        manifest['outcome'] = 'completed'
    except (OSError, ValueError, RuntimeError) as exc:
        manifest['outcome'] = 'aborted'
        manifest['errors'].append(str(exc))
        manifest['uncommitted_plant_state'] = pending_plant_state
        manifest['aborted_tick'] = tick_context
        manifest['stop'] = stop_plant(admin, online)
    finally:
        writer.close()
    manifest['completed_ticks'] = len(records)
    manifest['trajectory_sha256'] = writer.hasher.hexdigest()
    manifest['trajectory_bytes'] = writer.bytes_written
    manifest['memory'] = dict(peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024)
    for name in ('memory.peak', 'memory.max'):
        try:
            manifest['memory'][name] = int((Path('/sys/fs/cgroup') / name).read_text())
        except (OSError, ValueError):
            pass
    try:
        writer.write_manifest(manifest)
    except OSError:
        stop_plant(admin, online)
        raise
    return records, manifest


def shutdown(runtime):
    for path in ('admin/plant.sock', 'control/service.sock', 'protection/service.sock', 'patient/service.sock'):
        try:
            rpc(Path(runtime) / path, 'STOP')
        except (OSError, ValueError):
            pass


def main():
    def interrupt(signum, _frame):
        raise InterruptedError('runner received signal ' + str(signum))
    signal.signal(signal.SIGTERM, interrupt)
    signal.signal(signal.SIGINT, interrupt)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--build-dir', default='build', type=Path)
    parser.add_argument('--runtime-dir', default='/run/dialysis', type=Path)
    parser.add_argument('--local', action='store_true', help='Launch four separate native service processes')
    parser.add_argument('--wall-speed', type=float, default=0, help='Optional virtual/wall speed; 0 is unpaced batch')
    args = parser.parse_args()
    with args.config.open('rb') as stream:
        config = validate(strict_json(stream.read(1024 * 1024 + 1)))
    if args.output.exists():
        parser.error('output already exists; choose a new directory')
    if args.local:
        with LocalCluster(args.build_dir) as cluster:
            _, manifest = simulate(config, cluster.runtime, args.build_dir, args.output, wall_speed=args.wall_speed)
    else:
        _, manifest = simulate(config, args.runtime_dir, args.build_dir, args.output, wall_speed=args.wall_speed)
        # Compose stops remaining services when this process exits. Keep their
        # processes alive until then so --exit-code-from runner sees our result.
        try:
            rpc(args.runtime_dir / 'admin/plant.sock', 'HALT')
        except (OSError, ValueError):
            pass
    print(json.dumps(dict(outcome=manifest['outcome'], completed_ticks=manifest['completed_ticks'],
                          trajectory_sha256=manifest['trajectory_sha256'], errors=manifest['errors'])))
    return 0 if manifest['outcome'] == 'completed' else 1


if __name__ == '__main__':
    sys.exit(main())
