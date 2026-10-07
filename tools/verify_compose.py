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
import uuid

ROOT = Path(__file__).resolve().parents[1]


def command(args, env=None):
    result = subprocess.run(args, cwd=ROOT, env=env, text=True, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, timeout=120)
    if result.returncode:
        raise RuntimeError('Command failed: ' + ' '.join(args) + '\n' + result.stdout)
    return result.stdout


def inspect_services(prefix):
    ids = command(prefix + ['ps', '-aq']).split()
    inspected = json.loads(command(['docker', 'inspect'] + ids))
    return [dict(service=c['Config']['Labels']['com.docker.compose.service'], image=c['Image'],
                 exit_code=c['State']['ExitCode'], user=c['Config']['User'],
                 network=c['HostConfig']['NetworkMode'], read_only=c['HostConfig']['ReadonlyRootfs'],
                 cap_drop=c['HostConfig']['CapDrop'], security_opt=c['HostConfig']['SecurityOpt'],
                 mounts=[m['Destination'] for m in c['Mounts']]) for c in inspected]


def run_case(scenario, index, output):
    project = 'dl-m1-verify-' + uuid.uuid4().hex[:12]
    prefix = ['docker', 'compose', '-p', project]
    env = dict(os.environ, SCENARIO=scenario, RUN_NAME='run')
    directory = output / (scenario + '-' + str(index))
    directory.mkdir()
    try:
        log = command(prefix + ['up', '--no-build', '--abort-on-container-exit', '--exit-code-from', 'runner'], env)
        (directory / 'compose.log').write_text(log)
        services = inspect_services(prefix)
        command(prefix + ['cp', 'runner:/results/run/.', str(directory)], env)
        manifest = json.loads((directory / 'manifest.json').read_text())
        trajectory = json.loads((directory / 'trajectory.json').read_text())
        if manifest['outcome'] != 'completed' or len(trajectory) != 20:
            raise ValueError('Compose scenario incomplete')
        if {s['service'] for s in services} != {'plant', 'patient', 'control', 'protection', 'runner'}:
            raise ValueError('missing separate service')
        for service in services:
            if service['network'] != 'none' or not service['read_only'] or service['user'] != '10001:10001':
                raise ValueError('container isolation configuration')
            if service['service'] in ('control', 'protection'):
                if service['mounts'] != ['/run/dialysis/' + service['service']]:
                    raise ValueError('decision service has excessive mounts')
        active_ticks = 5 if scenario == 'hd_occlusion' else 20
        expected = Decimal(active_ticks) * Decimal(10) * Decimal(100) / Decimal(60000)
        for actual in (trajectory[-1]['removed_total_mL'], 40000 - trajectory[-1]['patient_volume_mL']):
            if abs(Decimal(str(actual)) - expected) >= Decimal('1e-8'):
                raise ValueError('independent Compose balance')
        if scenario == 'hd_occlusion':
            if trajectory[5]['reason'] != 'pressure' or any(x['blood_mL_min'] for x in trajectory[5:]):
                raise ValueError('Compose protection response')
        return dict(scenario=scenario, index=index, services=services, manifest=manifest,
                    trajectory_path=str(directory.relative_to(output) / 'trajectory.json'),
                    expected_removed_mL=str(expected), actual_removed_mL=trajectory[-1]['removed_total_mL'])
    finally:
        command(prefix + ['down', '--volumes', '--remove-orphans'], env)


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
    main()
