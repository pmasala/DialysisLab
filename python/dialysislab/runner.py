"""Deterministic barrier scheduler and build/configuration-specific run records."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
from .protocol import expect, heartbeat, integer, observation, pause, real, rpc, state, wait_ready

ROOT = Path(__file__).resolve().parents[2]
FAULTS = {'none', 'invalid', 'missing', 'stale', 'future', 'replay'}


def canonical(data):
    return json.dumps(data, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def validate(config):
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


def simulate(config, runtime, build_dir, output=None, before_tick=None):
    validate(config)
    runtime = Path(runtime)
    manifest = dict(schema_version=1, executed_at=datetime.now(timezone.utc).isoformat(),
                    configuration=config, configuration_sha256=digest(canonical(config).encode()),
                    build=build_identity(build_dir), python=platform.python_version(),
                    platform=platform.platform(), interface='DL1', model='m1-hd-1',
                    simulation_only=True, outcome='running', errors=[])
    records = []
    admin = runtime / 'admin/plant.sock'
    patient = runtime / 'patient/service.sock'
    resistance = config['resistance_mmHg_min_mL']
    sensor = dict(control_sensor='none', protection_sensor='none')
    pending_plant_state = None
    try:
        wait_ready(runtime)
        expect(rpc(patient, 'INIT', config['patient_volume_mL']), 'OK', 1)
        for n in range(config['ticks']):
            t = n * config['dt_ms']
            if before_tick:
                before_tick(n)
            for fault in config['faults']:
                if fault['tick'] == n:
                    if fault['target'] == 'resistance':
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
            physical = state(rpc(admin, 'COMMIT', n, t))
            pending_plant_state = physical
            if physical['sequence'] != n or physical['time_ms'] != t + config['dt_ms']:
                raise ValueError('plant clock mismatch')
            volume = expect(rpc(patient, 'ADVANCE', n, t, config['dt_ms'], physical['removed_tick_mL']),
                            'VOLUME', 5)
            if integer(volume[1]) != n or integer(volume[2]) != t + config['dt_ms']:
                raise ValueError('patient clock mismatch')
            records.append(dict(physical, patient_volume_mL=real(volume[3], 0, 100000),
                                patient_removed_mL=real(volume[4], 0, 100000), observations=measurements,
                                protection_decision=decision))
            pending_plant_state = None
            if failures:
                raise RuntimeError(','.join(failures))
            if physical['reason'] in ('liveness', 'protocol', 'control_missing', 'protection_missing'):
                raise RuntimeError('unexpected plant failure: ' + physical['reason'])
        manifest['outcome'] = 'completed'
    except (OSError, ValueError, RuntimeError) as exc:
        manifest['outcome'] = 'aborted'
        manifest['errors'].append(str(exc))
        manifest['uncommitted_plant_state'] = pending_plant_state
        # Direct observer stop is best effort; plant's own watchdog covers runner loss.
        try:
            rpc(admin, 'HALT')
        except (OSError, ValueError):
            pass
    manifest['completed_ticks'] = len(records)
    trajectory = canonical(records)
    manifest['trajectory_sha256'] = digest(trajectory.encode())
    if output is not None:
        output = Path(output)
        output.mkdir(parents=True, exist_ok=False)
        (output / 'trajectory.json').write_text(trajectory)
        (output / 'manifest.json').write_text(json.dumps(manifest, indent=2, allow_nan=False) + '\n')
    return records, manifest


def shutdown(runtime):
    for path in ('admin/plant.sock', 'control/service.sock', 'protection/service.sock', 'patient/service.sock'):
        try:
            rpc(Path(runtime) / path, 'STOP')
        except (OSError, ValueError):
            pass


def main():
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
