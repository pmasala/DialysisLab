#!/usr/bin/env python3
"""Drive real LVGL widgets in an isolated Compose UI container and collect evidence."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'python'), str(ROOT / 'tools'), str(ROOT / 'tests')]
from verify_compose import command, CommandFailure, inspect_services
from dialysislab.trajectory import scan, read_records
from capture_png import convert
import ui_regressions


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--graphical', action='store_true')
    args = parser.parse_args(); args.output.mkdir(parents=True, exist_ok=False)
    project = 'dl-m6-ui-' + uuid.uuid4().hex[:12]
    prefix = ['docker', 'compose', '-p', project, '-f', str(ROOT / 'compose.yaml')]
    if args.graphical: prefix += ['-f', str(ROOT / 'compose.device-x11.yaml')]
    prefix += ['--profile', 'device-ui']
    env = dict(os.environ, SCENARIO='device_ui_demo', WALL_SPEED='2', RUN_NAME='run')
    ui_name, runner_name = project + '-ui', project + '-runner'
    report = dict(schema_version=1, executed_at=datetime.now(timezone.utc).isoformat(), command=sys.argv,
                  project=project, successful=False, primary_exit=0, primary_error=None, collection_errors=[], cleanup_errors=[],
                  resources_retained=True, graphical=args.graphical, dependencies=json.loads((ROOT / 'gui_dependencies.json').read_text()))
    ui = None; extracted = set()
    ui_regressions.EVIDENCE = args.output
    def until(predicate, timeout=5):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            state = ui.snapshot()
            if predicate(state): return state
            time.sleep(.06)
        raise RuntimeError('widget/Compose condition timeout: ' + json.dumps(state))
    def click(action):
        ui.send('CLICK ' + action)
        if action not in ('STOP', 'ACK'):
            until(lambda s: s['pending']); ui.send('CLICK CONFIRM')
    try:
        report['startup'] = command(prefix + ['up', '-d', '--no-build', 'plant', 'control', 'protection', 'patient'], env)
        report['runner_start'] = command(prefix + ['run', '-d', '--no-deps', '--name', runner_name, 'runner'], env)
        ui_argv = prefix + ['run', '-T', '--no-deps', '--name', ui_name, 'device-ui', '/opt/bin/device-ui',
                             '--runtime-dir', '/run/dialysis', '--test-input', '--capture-dir', '/captures']
        if not args.graphical: ui_argv.append('--headless')
        ui = ui_regressions.UserInterface('/unused', 'widget-events', ui_argv)
        until(lambda s: s['control'] == s['protection'] == 'LIVE' and s.get('sequence', 0) >= 4)
        click('PRIME'); until(lambda s: s.get('stage') == 'PRIMING')
        # Observe sufficient actual priming time, without reading hidden patient state.
        time.sleep(3.4)
        click('CONFIGURE'); until(lambda s: s.get('stage') == 'CONFIGURATION')
        ui.send('CLICK MODE'); ui.send('CLICK MODE'); ui.send('SET blood 280'); ui.send('SET uf 4'); ui.send('SET sub 60')
        click('PRESCRIBE'); until(lambda s: s.get('mode') == 2 and s.get('prescribed_blood_mL_min') == 280)
        click('START'); until(lambda s: s.get('stage') == 'TREATMENT' and s.get('blood_mL_min', 0) > 0)
        report['treatment'] = ui.snapshot('compose_treatment')
        report['ui_process_memory'] = command(['docker', 'exec', ui_name, 'cat', '/proc/1/status'])
        report['ui_cgroup_peak'] = command(['docker', 'exec', ui_name, 'cat', '/sys/fs/cgroup/memory.peak'])
        # Execute denied connection attempts inside the actual running UI container.
        probe = """import socket
from pathlib import Path
from dialysislab.protocol import rpc
for path in ('admin/plant.sock','patient/service.sock','control/plant.sock','protection/plant.sock'):
    with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as s:
        try: s.connect('/run/dialysis/'+path)
        except (FileNotFoundError,PermissionError): print('DENIED '+path)
        else: raise SystemExit('unexpected admin access')
for role in ('control','protection'):
    assert rpc(Path('/run/dialysis/device')/(role+'.sock'),'HALT')==['REJECT','device_operation']
    print('REJECTED device HALT '+role)
"""
        report['boundary_probe'] = command(['docker', 'exec', ui_name, 'python3', '-c', probe])
        click('STOP'); until(lambda s: s.get('stage') == 'STOPPED' and s.get('blood_mL_min') == 0)
        report['stopped'] = ui.snapshot('compose_stopped')
        code = int(command(['docker', 'wait', runner_name], timeout=60).strip())
        if code: raise CommandFailure(['docker', 'wait', runner_name], code, 'runner exited nonzero')
        ui.close(); ui = None
    except Exception as exc:
        report['primary_exit'] = getattr(exc, 'returncode', 1)
        report['primary_error'] = str(exc)
    finally:
        if report['primary_exit']:
            # Let the runner write its aborted manifest before copying/removing volumes.
            try:
                if command(['docker', 'ps', '-aq', '--filter', 'name=^/' + runner_name + '$']).strip():
                    command(['docker', 'stop', '--time', '5', runner_name])
            except Exception as exc: report['collection_errors'].append(dict(stage='runner_stop', error=str(exc)))
        if ui is not None:
            try: ui.close()
            except Exception as exc: report['collection_errors'].append(dict(stage='ui_close', error=str(exc)))
        for stage, argv, target in [
            ('logs', prefix + ['logs', '--no-color', '--timestamps'], args.output / 'services.log'),
            ('runner_logs', ['docker', 'logs', runner_name], args.output / 'runner.log'),
            ('ui_logs', ['docker', 'logs', ui_name], args.output / 'ui-container.log')]:
            try: target.write_text(command(argv, env))
            except Exception as exc: report['collection_errors'].append(dict(stage=stage, error=str(exc)))
        try: report['services'] = inspect_services(prefix)
        except Exception as exc: report['collection_errors'].append(dict(stage='inspect', error=str(exc)))
        for name, source in [('results', runner_name + ':/results/.'), ('captures', ui_name + ':/captures/.')]:
            try: command(['docker', 'cp', source, str(args.output / name)]); extracted.add(name)
            except Exception as exc: report['collection_errors'].append(dict(stage=name, error=str(exc)))
        if extracted == {'results', 'captures'} and not report['collection_errors']:
            try:
                command(prefix + ['down', '--volumes', '--remove-orphans'], env); report['resources_retained'] = False
            except Exception as exc: report['cleanup_errors'].append(str(exc))
        else:
            try: command(prefix + ['stop'], env)
            except Exception as exc: report['cleanup_errors'].append(str(exc))
            report['recovery_commands'] = ['docker cp ' + runner_name + ':/results/. /tmp/' + project + '-results',
                                           'docker cp ' + ui_name + ':/captures/. /tmp/' + project + '-captures',
                                           ' '.join(prefix + ['down', '--volumes', '--remove-orphans'])]
    try:
        if report['primary_exit']: raise RuntimeError(report['primary_error'])
        if report['collection_errors'] or report['cleanup_errors']: raise RuntimeError('evidence collection/cleanup failed')
        run = args.output / 'results/run'
        manifest = json.loads((run / 'manifest.json').read_text()); trajectory = scan(run / 'trajectory.jsonl')
        if manifest['outcome'] != 'completed' or trajectory['records'] != 400 or trajectory['sha256'] != manifest['trajectory_sha256']:
            raise ValueError('incomplete/invalid actual runner artifacts')
        states = [r['machine']['stage'] for r in read_records(run / 'trajectory.jsonl')]
        if 'TREATMENT' not in states or states[-1] != 'STOPPED': raise ValueError('actual trajectory did not apply widget actions')
        service = next(s for s in report['services'] if s['service'] == 'device-ui')
        expected_mounts = {'/run/dialysis/device/control', '/run/dialysis/device/protection', '/captures'} | ({'/tmp/.X11-unix/X0'} if args.graphical else set())
        if set(service['mounts']) != expected_mounts or service['network'] != 'none' or not service['read_only'] or service['oom_killed'] or service['memory_limit_bytes'] != 128 * 1024 ** 2:
            raise ValueError('UI isolation/memory configuration')
        report.update(manifest=manifest, trajectory=trajectory)
        for source in (args.output / 'captures').glob('*.ppm'): convert(source, source.with_suffix('.png'))
        report['successful'] = True
    except Exception as exc:
        report['validation_error'] = str(exc)
    report['artifacts'] = {str(p.relative_to(args.output)): hashlib.sha256(p.read_bytes()).hexdigest() for p in args.output.rglob('*') if p.is_file()}
    (args.output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k in ('successful','primary_exit','primary_error','validation_error','collection_errors','resources_retained')}, indent=2))
    return report['primary_exit'] or (0 if report['successful'] else 1)


if __name__ == '__main__': sys.exit(main())
