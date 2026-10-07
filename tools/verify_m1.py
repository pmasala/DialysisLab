#!/usr/bin/env python3
"""Execute acceptance tests and retain actual, configuration-bound test results."""
import argparse
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'python'))
from dialysislab.runner import build_identity


class RecordedResults(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cases = []

    def addSuccess(self, test):
        super().addSuccess(test)
        self.cases.append({'test': test.id(), 'result': 'passed'})

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.cases.append({'test': test.id(), 'result': 'failed'})

    def addError(self, test, err):
        super().addError(test, err)
        self.cases.append({'test': test.id(), 'result': 'error'})

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        self.cases.append({'test': test.id(), 'result': 'skipped', 'reason': reason})

    def addSubTest(self, test, subtest, err):
        super().addSubTest(test, subtest, err)
        if err:
            self.cases.append({'test': subtest.id(), 'result': 'failed'})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build-dir', default=ROOT / 'build', type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    os.environ['DIALYSISLAB_BUILD_DIR'] = str(args.build_dir.resolve())
    suite = unittest.defaultTestLoader.discover(str(ROOT / 'tests'))
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=2, resultclass=RecordedResults).run(suite)
    document = dict(schema_version=1, executed_at=datetime.now(timezone.utc).isoformat(),
                    command='python3 tools/verify_m1.py --build-dir ' + str(args.build_dir) + ' --output ' + str(args.output),
                    build=build_identity(args.build_dir), tests_run=result.testsRun,
                    successful=result.wasSuccessful() and not result.skipped, cases=result.cases,
                    output=stream.getvalue(), scope='Synthetic M1 and assurance tooling only; independent review pending',
                    test_source_sha256={str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                                        for p in sorted((ROOT / 'tests').glob('test_*.py'))},
                    configurations={p.name: json.loads(p.read_text()) for p in sorted((ROOT / 'scenarios').glob('*.json'))})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x') as output:
        json.dump(document, output, indent=2)
        output.write('\n')
    print(stream.getvalue(), end='')
    return 0 if document['successful'] else 1


if __name__ == '__main__':
    sys.exit(main())
