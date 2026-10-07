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
from .protocol import expect, heartbeat, integer, observation, pause, real, rpc, state, wait_ready
from .trajectory import FORMAT, TrajectoryWriter, canonical

ROOT = Path(__file__).resolve().parents[2]
FAULTS = {'none', 'invalid', 'missing', 'stale', 'future', 'replay'}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def validate(config):
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
        for role in ('admin', 'control', 'protection', 'patient'):
            (self.runtime / role).mkdir()
        env = dict(os.environ, PYTHONPATH=str(ROOT / 'python'), PYTHONDONTWRITEBYTECODE='1')
        try:
            for role in ('plant', 'control', 'protection', 'patient'):
                command = ([sys.executable, '-m', 'dialysislab.patient'] if role == 'patient'
                           else [str(self.build_dir / role)])
                log = (self.runtime / (role + '.log')).open('w')
                self.logs.append(log)
                self.processes[role] = subprocess.Popen(command + ['--runtime-dir', str(self.runtime)],
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
    # Identify the Python code actually executing, including native post-build edits.
    identity['python_sha256'] = {str(p.relative_to(ROOT)): digest(p.read_bytes())
                                 for p in sorted((ROOT / 'python/dialysislab').glob('*.py'))}
    return identity


def stop_plant(admin):
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
        observed = state(rpc(admin, 'STATUS'))
        result['observed_state'] = observed
        result['outputs_zero_observed'] = (observed['latched'] and observed['clamp_closed']
                                          and observed['blood_mL_min'] == 0 and observed['uf_mL_min'] == 0)
    except (OSError, ValueError) as exc:
        result['observation_error'] = type(exc).__name__ + ': ' + str(exc)
    return result


def simulate(config, runtime, build_dir, output=None, before_tick=None):
    validate(config)
    runtime = Path(runtime)
    manifest = dict(schema_version=2, executed_at=datetime.now(timezone.utc).isoformat(),
                    configuration=config, configuration_sha256=digest(canonical(config).encode()),
                    build=build_identity(build_dir), python=platform.python_version(),
                    platform=platform.platform(), interface='DL1', model=config['model'],
                    simulation_only=True, outcome='running', errors=[],
                    trajectory_format=FORMAT, trajectory_file='trajectory.jsonl',
                    completed_ticks=0, trajectory_sha256=None)
    writer = TrajectoryWriter(output)
    records = writer.trajectory
    writer.write_manifest(manifest)
    admin = runtime / 'admin/plant.sock'
    patient = runtime / 'patient/service.sock'
    resistance = config['resistance_mmHg_min_mL']
    sensor = dict(control_sensor='none', protection_sensor='none')
    pending_plant_state = None
    tick_context = None
    extended = config['schema_version'] == 2
    try:
        wait_ready(runtime)
        if extended:
            from . import circuit
            circuit.configure(admin, config)
        expect(rpc(patient, 'INIT', config['patient_volume_mL']), 'OK', 1)
        for n in range(config['ticks']):
            t = n * config['dt_ms']
            tick_context = dict(sequence=n, time_ms=t)
            if before_tick:
                before_tick(n)
            for fault in config['faults']:
                if fault['tick'] == n:
                    if extended and fault['target'].startswith('edge:'):
                        expect(rpc(admin, 'EDGE2', int(fault['target'][5:]), fault['value']['resistance'],
                                   int(fault['value']['closed'])), 'OK', 1)
                    elif fault['target'] == 'resistance':
                        resistance = fault['value']
                    else:
                        sensor[fault['target']] = fault['value']
            expect(rpc(admin, 'PREPARE', n, t, config['dt_ms'], resistance,
                       sensor['control_sensor'], sensor['protection_sensor']), 'OK', 1)
            measurements = {role: observation(rpc(runtime / role / 'plant.sock', 'SENSE', n, t))
                            for role in ('control', 'protection')}
            failures = []
            try:
                expect(rpc(runtime / 'control/service.sock', 'STEP', n, t,
                           config['blood_mL_min'], config['uf_mL_min']), 'OK', 1)
            except (OSError, ValueError) as exc:
                failures.append('control:' + type(exc).__name__)
            try:
                decision = expect(rpc(runtime / 'protection/service.sock', 'STEP', n, t,
                                      config['pressure_limit_mmHg']), 'DECISION', 2)[1]
            except (OSError, ValueError) as exc:
                decision = 'unavailable'
                failures.append('protection:' + type(exc).__name__)
            tick_context.update(protection_decision=decision, observations=measurements)
            if failures:
                manifest['rpc_failures'] = failures
                raise RuntimeError(','.join(failures))
            physical = (circuit.committed(rpc(admin, 'COMMIT2', n, t)) if extended
                        else state(rpc(admin, 'COMMIT', n, t)))
            pending_plant_state = physical
            if physical['sequence'] != n or physical['time_ms'] != t + config['dt_ms']:
                raise ValueError('plant clock mismatch')
            water = physical['removed_tick_mL']
            if extended:
                if physical['circuit']['sequence'] != n or physical['circuit']['time_ms'] != t + config['dt_ms']:
                    raise ValueError('circuit clock mismatch')
                water = physical['circuit']['draw_tick_mL'] - physical['circuit']['return_tick_mL']
            volume = expect(rpc(patient, 'FLUID2' if extended else 'ADVANCE', n, t, config['dt_ms'], water),
                            'FLUID_VOLUME2' if extended else 'VOLUME', 6 if extended else 5)
            if integer(volume[1]) != n or integer(volume[2]) != t + config['dt_ms']:
                raise ValueError('patient clock mismatch')
            if extended:
                physical['patient_numerical_correction_mL'] = real(volume[5], -1e-8, 1e-8)
            writer.append(dict(physical, patient_volume_mL=real(volume[3], 0, 100000),
                                patient_removed_mL=real(volume[4], -100000, 100000), observations=measurements,
                                protection_decision=decision))
            pending_plant_state = None
            if physical['reason'] in ('liveness', 'protocol', 'control_missing', 'protection_missing'):
                raise RuntimeError('unexpected plant failure: ' + physical['reason'])
        if extended:
            manifest['final_plant_observation'] = state(rpc(admin, 'STATUS'))
            if manifest['final_plant_observation']['reason'] in ('liveness', 'protocol', 'control_missing', 'protection_missing'):
                raise RuntimeError('plant stopped after commit: ' + manifest['final_plant_observation']['reason'])
        manifest['outcome'] = 'completed'
    except (OSError, ValueError, RuntimeError) as exc:
        manifest['outcome'] = 'aborted'
        manifest['errors'].append(str(exc))
        manifest['uncommitted_plant_state'] = pending_plant_state
        manifest['aborted_tick'] = tick_context
        manifest['stop'] = stop_plant(admin)
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
        stop_plant(admin)
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
    args = parser.parse_args()
    config = validate(json.loads(args.config.read_text()))
    if args.output.exists():
        parser.error('output already exists; choose a new directory')
    if args.local:
        with LocalCluster(args.build_dir) as cluster:
            _, manifest = simulate(config, cluster.runtime, args.build_dir, args.output)
    else:
        _, manifest = simulate(config, args.runtime_dir, args.build_dir, args.output)
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
