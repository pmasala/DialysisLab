#!/usr/bin/env python3
"""Run configured real-process models, scan exact evidence and check water balance."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'python'))
from dialysislab.runner import LocalCluster, simulate
from dialysislab.trajectory import scan, read_records
from verify_compose import collect_case, ComposeRunFailure


def verify(directory):
    manifest = json.loads((directory / 'manifest.json').read_text())
    summary = scan(directory / 'trajectory.jsonl')
    config = manifest['configuration']
    if manifest['outcome'] != 'completed' or summary['records'] != config['ticks']:
        raise ValueError('scenario incomplete')
    if summary['sha256'] != manifest['trajectory_sha256']:
        raise ValueError('trajectory hash mismatch')
    maximum_error = 0
    for record in read_records(directory / 'trajectory.jsonl'):
        storage = record.get('circuit', {}).get('stored_mL', 0)
        error = abs(config['patient_volume_mL'] - record['patient_volume_mL'] - storage - record['removed_total_mL'])
        maximum_error = max(maximum_error, error)
        if error > 1e-6:
            raise ValueError('water conservation: ' + str(error))
    return dict(manifest=manifest, scan=summary, maximum_water_error_mL=maximum_error,
                expected_water_error_mL=1e-6)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scenarios', nargs='+', default=['circuit_small', 'circuit_large', 'circuit_occlusion'])
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--build-dir', default='build', type=Path)
    parser.add_argument('--compose', action='store_true')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    report = dict(executed_at=datetime.now(timezone.utc).isoformat(), command=[sys.executable, *sys.argv],
                  successful=False, cases=[])
    try:
        for name in args.scenarios:
            hashes = []
            for repeat in (1, 2):
                config = json.loads((ROOT / 'scenarios' / (name + '.json')).read_text())
                if args.compose:
                    collected = collect_case(name, repeat, args.output, timeout=900)
                    if collected['compose_exit_code'] or collected['collection_errors'] or collected['cleanup_errors']:
                        raise ComposeRunFailure(collected)
                    directory = Path(collected['directory']) / 'results/run'
                else:
                    directory = args.output / (name + '-' + str(repeat))
                    with LocalCluster(args.build_dir) as cluster:
                        simulate(config, cluster.runtime, args.build_dir, directory)
                    collected = None
                case = verify(directory)
                case.update(scenario=name, repeat=repeat, collection=collected,
                            directory=str(directory))
                report['cases'].append(case)
                hashes.append(case['scan']['sha256'])
            if hashes[0] != hashes[1]:
                raise ValueError('reproduction failed: ' + name)
        report['successful'] = True
    except Exception as exc:
        report['error'] = type(exc).__name__ + ': ' + str(exc)
        raise
    finally:
        (args.output / 'models.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(dict(successful=True, runs=len(report['cases']))))


if __name__ == '__main__':
    main()
