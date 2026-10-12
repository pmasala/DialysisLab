#!/usr/bin/env python3
"""Real Docker regressions for M1 memory and failed-run evidence retention."""
from datetime import datetime, timezone
import argparse
import hashlib
import json
from pathlib import Path
import sys
import uuid
from unittest.mock import patch

from verify_compose import ROOT, collect_case, command, CommandFailure
import verify_compose
from dialysislab.trajectory import scan

LOST_REPLY_RUNNER = '''import json, sys
from pathlib import Path
from dialysislab import runner
original = runner.rpc
def rpc(path, *fields):
    response = original(path, *fields)
    if path.parent.name == 'control' and path.name == 'service.sock' and fields[:3] == ('STEP', 5, 500):
        raise TimeoutError('STEP reply deliberately discarded after real plant acceptance')
    return response
runner.rpc = rpc
config = json.loads(Path('/opt/dialysislab/scenarios/hd_nominal.json').read_text())
_, manifest = runner.simulate(config, '/run/dialysis', '/opt/bin', '/results/run')
print(json.dumps(dict(outcome=manifest['outcome'], completed_ticks=manifest['completed_ticks'], stop=manifest.get('stop'))))
sys.exit(7 if manifest['outcome'] == 'aborted' else 0)
'''


def assert_aborted(directory):
    directory = Path(directory)
    manifest = json.loads((directory / 'manifest.json').read_text())
    trajectory = scan(directory / 'trajectory.jsonl')
    assert manifest['outcome'] == 'aborted', manifest
    assert manifest['completed_ticks'] == trajectory['records'] == 5
    assert trajectory['sha256'] == manifest['trajectory_sha256']
    assert manifest['stop']['outputs_zero_observed'] is True
    assert manifest['stop']['observed_state']['time_ms'] == 500
    return dict(manifest=manifest, trajectory=trajectory)


def failures(output):
    reports = []
    for kind in ('runner_aborted', 'before_runner_start', 'extraction_failure'):
        project = 'dl-m1-review-' + uuid.uuid4().hex[:12]
        override = output / (kind + '.json')
        runner = dict(command=['python3', '-c', LOST_REPLY_RUNNER])
        if kind == 'before_runner_start':
            runner.update(image='dialysislab-review-absent:' + uuid.uuid4().hex, pull_policy='never')
        override.write_text(json.dumps(dict(services=dict(runner=runner)), indent=2) + '\n')
        files = [ROOT / 'compose.yaml', override]
        prefix = ['docker', 'compose', '-p', project, '-f', str(files[0]), '-f', str(files[1])]
        original = verify_compose.command

        def failed_copy(args, *a, **kw):
            if 'cp' in args:
                raise CommandFailure(args, 19, 'Injected artifact extraction failure')
            return original(args, *a, **kw)

        with patch.object(verify_compose, 'command', side_effect=failed_copy if kind == 'extraction_failure' else original):
            report = collect_case('hd_nominal', kind, output, project=project, compose_files=files)
        if kind == 'runner_aborted':
            assert report['compose_exit_code'] == 7
            assert not report['collection_errors'], report
            assert not report['resources_retained'], report
            report['checked_artifacts'] = assert_aborted(Path(report['directory']) / 'results/run')
        elif kind == 'extraction_failure':
            assert report['compose_exit_code'] == 7
            assert report['resources_retained'] and not report['extracted']
            assert any(e['stage'] == 'extract' for e in report['collection_errors'])
            # Recovery uses the exact retained container/volume, then verifies the
            # artifacts before test-owned cleanup. The collector never removes it.
            command(['docker', 'volume', 'inspect', project + '_results'])
            recovered = Path(report['directory']) / 'recovered-results'
            command(prefix + ['cp', 'runner:/results/.', str(recovered)])
            report['recovered_artifacts'] = assert_aborted(recovered / 'run')
            report['recovery_verified_before_cleanup'] = True
            command(prefix + ['down', '--volumes', '--remove-orphans'])
        else:
            assert report['compose_exit_code'] != 0
            assert report['resources_retained'] and not report['extracted']
            # Independently inspect whether any volume exists. If created before
            # startup failure it must be empty; do not delete unknown results.
            volumes = command(['docker', 'volume', 'ls', '--filter', 'label=com.docker.compose.project=' + project,
                               '--format', '{{.Name}}']).splitlines()
            result_volume = project + '_results'
            if result_volume in volumes:
                checked = command(['docker', 'run', '--rm', '--network', 'none', '--read-only',
                    '--mount', 'type=volume,src=' + result_volume + ',dst=/results,readonly',
                    'dialysislab-m1:local', 'python3', '-c',
                    "from pathlib import Path; assert not list(Path('/results').iterdir()); print('empty results verified')"])
                report['volume_inspection'] = checked
            else:
                report['volume_inspection'] = 'No results volume was created (queried project labels).'
            command(prefix + ['down', '--volumes', '--remove-orphans'])
            report['empty_or_absent_results_verified_before_cleanup'] = True
        reports.append(report)
        print(kind + ': verified', flush=True)
    return reports


def long_runs(output):
    cases = []
    for index in (1, 2):
        print('Starting real 100000-tick Compose run ' + str(index), flush=True)
        report = collect_case('hd_100000', index, output, timeout=900)
        assert report['compose_exit_code'] == 0, report
        assert not report['collection_errors'] and not report['cleanup_errors'], report
        directory = Path(report['directory']) / 'results/run'
        manifest = json.loads((directory / 'manifest.json').read_text())
        trajectory = scan(directory / 'trajectory.jsonl')
        assert manifest['outcome'] == 'completed'
        assert trajectory['records'] == manifest['completed_ticks'] == 100000
        assert trajectory['last']['sequence'] == 99999
        assert trajectory['last']['time_ms'] == 10000000
        assert trajectory['sha256'] == manifest['trajectory_sha256']
        assert manifest['memory']['peak_rss_bytes'] <= 64 * 1024**2
        service = next(s for s in report['services'] if s['service'] == 'runner')
        assert service['memory_limit_bytes'] == 128 * 1024**2
        assert not service['oom_killed'] and service['exit_code'] == 0
        case = dict(manifest=manifest, scan=trajectory, runner=service,
                    rss_headroom_bytes=128*1024**2-manifest['memory']['peak_rss_bytes'])
        cases.append(case)
        print('Completed run ' + str(index) + ': ' + json.dumps(manifest['memory']), flush=True)
    assert cases[0]['scan']['sha256'] == cases[1]['scan']['sha256']
    return cases


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    args.output = args.output.resolve()
    args.output.mkdir(parents=True, exist_ok=False)
    report = dict(executed_at=datetime.now(timezone.utc).isoformat(), successful=False,
                  command='python3 tools/verify_m1_review.py --output ' + str(args.output),
                  verification_source_sha256={name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
                                              for name in ('tools/verify_m1_review.py', 'tools/verify_compose.py')})
    try:
        report['failure_regressions'] = failures(args.output)
        report['long_runs'] = long_runs(args.output)
        report['successful'] = True
    finally:
        (args.output / 'review-docker.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(dict(successful=True, failure_regressions=3, real_100000_tick_runs=2)))


if __name__ == '__main__':
    main()
