#!/usr/bin/env python3
"""Check separate CMake builds and native/container synthetic trajectories."""
import argparse
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'python'))
from dialysislab.runner import LocalCluster, build_identity, canonical, simulate


def compare(a, b):
    if isinstance(a, dict):
        if not isinstance(b, dict) or set(a) != set(b):
            raise ValueError('record keys differ')
        for key in a:
            compare(a[key], b[key])
    elif isinstance(a, list):
        if not isinstance(b, list) or len(a) != len(b):
            raise ValueError('record lengths differ')
        for left, right in zip(a, b):
            compare(left, right)
    elif isinstance(a, float):
        if not math.isclose(a, b, abs_tol=1e-9, rel_tol=1e-9):
            raise ValueError('numeric replay differs')
    elif a != b:
        raise ValueError('discrete replay differs')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--first-build', type=Path, required=True)
    parser.add_argument('--second-build', type=Path, required=True)
    parser.add_argument('--compose-output', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    identities = [build_identity(p) for p in (args.first_build, args.second_build)]
    if identities[0]['binary_sha256'] != identities[1]['binary_sha256']:
        raise ValueError('clean CMake builds have different binary hashes')
    cases = []
    for name in ('hd_nominal', 'hd_occlusion'):
        config = json.loads((ROOT / 'scenarios' / (name + '.json')).read_text())
        with LocalCluster(args.first_build) as cluster:
            records, manifest = simulate(config, cluster.runtime, args.first_build)
        if manifest['outcome'] != 'completed':
            raise ValueError('native replay aborted')
        container_records = json.loads((args.compose_output / (name + '-1') / 'trajectory.json').read_text())
        compare(records, container_records)
        cases.append(dict(scenario=name, native_manifest=manifest,
                          container_manifest=json.loads((args.compose_output / (name + '-1') / 'manifest.json').read_text()),
                          absolute_tolerance=1e-9, relative_tolerance=1e-9,
                          exact_match=canonical(records) == canonical(container_records)))
    result = dict(schema_version=1, executed_at=datetime.now(timezone.utc).isoformat(),
                  command='python3 tools/verify_reproducibility.py --first-build ' + str(args.first_build)
                  + ' --second-build ' + str(args.second_build) + ' --compose-output ' + str(args.compose_output)
                  + ' --output ' + str(args.output), successful=True,
                  clean_builds_identical=True, builds=identities, cases=cases)
    with args.output.open('x') as output:
        json.dump(result, output, indent=2)
        output.write('\n')
    print(json.dumps(dict(successful=True, clean_builds_identical=True,
                         cross_build_exact=all(c['exact_match'] for c in cases))))


if __name__ == '__main__':
    main()
