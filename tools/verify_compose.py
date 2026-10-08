#!/usr/bin/env python3
"""Run isolated Compose acceptance projects; retain evidence before scoped cleanup."""
import argparse
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import shlex
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'python'))
from dialysislab.trajectory import read_records, scan


class CommandFailure(RuntimeError):
    def __init__(self, args, returncode, output):
        self.returncode = returncode
        self.output = output
        super().__init__('Command failed: ' + shlex.join(args) + '\n' + output)


def command(args, env=None, timeout=120):
    try:
        result = subprocess.run(args, cwd=ROOT, env=env, text=True, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        output = exc.stdout or ''
        if isinstance(output, bytes):
            output = output.decode(errors='replace')
        raise CommandFailure(args, 124, output + '\nVerification timeout') from exc
    except OSError as exc:
        raise CommandFailure(args, 127, str(exc)) from exc
    if result.returncode:
        raise CommandFailure(args, result.returncode, result.stdout)
    return result.stdout


class ComposeRunFailure(RuntimeError):
    def __init__(self, report):
        self.report = report
        self.returncode = report['compose_exit_code'] or 1
        super().__init__('Compose verification failed; evidence: ' + report['directory']
                         + '; resources retained: ' + str(report['resources_retained']))


def collect_case(scenario, index, output, *, project=None, compose_files=None, timeout=120):
    """Always retain diagnostics; never delete result volumes after failed extraction."""
    project = project or 'dl-m1-verify-' + uuid.uuid4().hex[:12]
    prefix = ['docker', 'compose', '-p', project]
    for path in compose_files or []:
        prefix.extend(['-f', str(path)])
    env = dict(os.environ, SCENARIO=scenario, RUN_NAME='run')
    directory = Path(output).resolve() / (scenario + '-' + str(index))
    directory.mkdir(parents=True, exist_ok=False)
    report = dict(project=project, directory=str(directory), compose_exit_code=None,
                  collection_errors=[], cleanup_errors=[], extracted=False,
                  resources_retained=True, services=[], recovery_commands=[])
    up = prefix + ['up', '--no-build', '--abort-on-container-exit', '--exit-code-from', 'runner']
    report['up_command'] = up
    try:
        try:
            log = command(up, env, timeout=timeout)
            report['compose_exit_code'] = 0
        except CommandFailure as exc:
            report['compose_exit_code'] = exc.returncode
            log = exc.output
        (directory / 'compose.log').write_text(log)
        try:
            (directory / 'services.log').write_text(command(prefix + ['logs', '--no-color', '--timestamps'], env))
        except (CommandFailure, OSError) as exc:
            report['collection_errors'].append(dict(stage='logs', error=str(exc)))
        try:
            report['services'] = inspect_services(prefix)
        except (CommandFailure, ValueError) as exc:
            report['collection_errors'].append(dict(stage='inspect', error=str(exc)))
        try:
            # Copy the whole result volume view, including partial/temporary files.
            command(prefix + ['cp', 'runner:/results/.', str(directory / 'results')], env)
            report['extracted'] = True
        except CommandFailure as exc:
            report['collection_errors'].append(dict(stage='extract', error=str(exc)))
    finally:
        safe_to_remove = report['extracted'] and not report['collection_errors']
        cleanup = prefix + (['down', '--volumes', '--remove-orphans'] if safe_to_remove else ['stop'])
        report['cleanup_command'] = cleanup
        try:
            command(cleanup, env)
            report['resources_retained'] = not safe_to_remove
        except CommandFailure as exc:
            report['cleanup_errors'].append(str(exc))
        if report['resources_retained']:
            recovery = directory / 'recovered-results'
            report['recovery_commands'] = [
                shlex.join(prefix + ['logs', '--no-color', '--timestamps']),
                shlex.join(prefix + ['cp', 'runner:/results/.', str(recovery)]),
                '# If the runner container was never created, inspect the retained volume:',
                shlex.join(['docker', 'volume', 'inspect', project + '_results']),
                '# Only after recovery/inspection succeeds, remove this test project:',
                shlex.join(prefix + ['down', '--volumes', '--remove-orphans'])]
            (directory / 'RECOVERY.txt').write_text('\n'.join(report['recovery_commands']) + '\n')
        (directory / 'collection.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


def inspect_services(prefix):
    ids = command(prefix + ['ps', '-aq']).split()
    inspected = json.loads(command(['docker', 'inspect'] + ids))
    return [dict(service=c['Config']['Labels']['com.docker.compose.service'], image=c['Image'],
                 exit_code=c['State']['ExitCode'], user=c['Config']['User'],
                 oom_killed=c['State']['OOMKilled'], memory_limit_bytes=c['HostConfig']['Memory'],
                 network=c['HostConfig']['NetworkMode'], read_only=c['HostConfig']['ReadonlyRootfs'],
                 cap_drop=c['HostConfig']['CapDrop'], security_opt=c['HostConfig']['SecurityOpt'],
                 mounts=[m['Destination'] for m in c['Mounts']]) for c in inspected]


def run_case(scenario, index, output):
    report = collect_case(scenario, index, output)
    if report['compose_exit_code'] or report['collection_errors'] or report['cleanup_errors']:
        raise ComposeRunFailure(report)
    directory = Path(report['directory']) / 'results/run'
    services = report['services']
    manifest = json.loads((directory / 'manifest.json').read_text())
    trajectory = scan(directory / 'trajectory.jsonl')
    if manifest['outcome'] != 'completed' or trajectory['records'] != 20:
        raise ValueError('Compose scenario incomplete')
    if manifest['trajectory_sha256'] != trajectory['sha256']:
        raise ValueError('Compose trajectory hash mismatch')
    if {s['service'] for s in services} != {'plant', 'patient', 'control', 'protection', 'runner'}:
        raise ValueError('missing separate service')
    for service in services:
        if service['network'] != 'none' or not service['read_only'] or service['user'] != '10001:10001':
            raise ValueError('container isolation configuration')
        if service['service'] in ('control', 'protection'):
            if set(service['mounts']) != {'/run/dialysis/' + service['service'], '/run/dialysis/device'}:
                raise ValueError('decision service has excessive mounts')
    active_ticks = 5 if scenario == 'hd_occlusion' else 20
    expected = Decimal(active_ticks) * Decimal(10) * Decimal(100) / Decimal(60000)
    last = trajectory['last']
    for actual in (last['removed_total_mL'], 40000 - last['patient_volume_mL']):
        if abs(Decimal(str(actual)) - expected) >= Decimal('1e-8'):
            raise ValueError('independent Compose balance')
    if scenario == 'hd_occlusion':
        for record in read_records(directory / 'trajectory.jsonl'):
            if record['sequence'] == 5 and record['reason'] != 'pressure':
                raise ValueError('Compose protection response')
            if record['sequence'] >= 5 and record['blood_mL_min'] != 0:
                raise ValueError('Compose protection response')
    return dict(scenario=scenario, index=index, services=services, manifest=manifest,
                trajectory_path=str(directory.relative_to(Path(output).resolve()) / 'trajectory.jsonl'),
                expected_removed_mL=str(expected), actual_removed_mL=last['removed_total_mL'])


def boundary_case():
    project = 'dl-m1-boundary-' + uuid.uuid4().hex[:12]
    prefix = ['docker', 'compose', '-p', project]
    probes = []
    try:
        command(prefix + ['up', '-d', '--no-build', 'plant', 'control', 'protection', 'patient'])
        # Mount absence is enforced by the container filesystem, not a menu or
        # runner forwarding rule. This probes actual connection attempts.
        code = """import socket
for path in ('/run/dialysis/admin/plant.sock', '/run/dialysis/patient/service.sock'):
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
        try:
            s.connect(path)
        except (FileNotFoundError, PermissionError):
            print('DENIED ' + path)
        else:
            raise SystemExit('Unexpected administration access')
"""
        for role in ('control', 'protection'):
            probes.append(dict(role=role, output=command(prefix + ['exec', '-T', role, 'python3', '-c', code])))
        device_code = """from pathlib import Path
import time
from dialysislab.protocol import rpc
for role in ('control', 'protection'):
    deadline=time.monotonic()+10
    while True:
        try:
            reply=rpc(Path('/run/dialysis/device')/(role+'.sock'),'HALT')
            assert reply==['REJECT','device_operation'],reply
            print('DEVICE_ENDPOINT_REJECTS_ADMIN '+role)
            break
        except (OSError,ValueError):
            if time.monotonic()>deadline: raise
            time.sleep(.05)
""" + code.replace("'/run/dialysis/patient/service.sock'", "'/run/dialysis/patient/service.sock', '/run/dialysis/control/plant.sock', '/run/dialysis/protection/plant.sock'")
        probes.append(dict(role='device-only', output=command([
            'docker', 'run', '--rm', '--network', 'none', '--read-only', '--cap-drop', 'ALL',
            '--security-opt', 'no-new-privileges:true', '--user', '10001:10001', '--pids-limit', '32', '--memory', '128m',
            '--mount', 'type=volume,src=' + project + '_device,dst=/run/dialysis/device',
            'dialysislab-m1:local', 'python3', '-c', device_code])))
        return probes
    finally:
        command(prefix + ['down', '--volumes', '--remove-orphans'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    cases = [run_case(name, index, args.output) for name in ('hd_nominal', 'hd_occlusion') for index in (1, 2)]
    for a, b in (cases[:2], cases[2:]):
        if a['manifest']['trajectory_sha256'] != b['manifest']['trajectory_sha256']:
            raise ValueError('Compose replay mismatch')
    report = dict(schema_version=1, executed_at=datetime.now(timezone.utc).isoformat(),
                  command='python3 tools/verify_compose.py --output ' + str(args.output),
                  successful=True, cases=cases, boundary_probes=boundary_case(),
                  docker=command(['docker', '--version']).strip(),
                  compose=command(['docker', 'compose', 'version']).strip(),
                  deployment_sha256={name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
                                     for name in ('Dockerfile', '.dockerignore', 'compose.yaml')},
                  scope='Local WSL2 Docker engine, synthetic configurations only; independent review pending')
    (args.output / 'compose-results.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'successful': True, 'runs': len(cases), 'exact_replay': True,
                      'boundary_probes': len(report['boundary_probes'])}))


if __name__ == '__main__':
    try:
        main()
    except ComposeRunFailure as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(exc.returncode if exc.returncode > 0 else 128 - exc.returncode)
