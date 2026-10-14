#!/usr/bin/env python3
"""Record CR-MIX-001 execution and reject reuse after any verification input changes."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]


def inputs(root=ROOT):
    paths=list((root/'src').rglob('*'))+list((root/'python/dialysislab').glob('*.py'))+list((root/'scenarios').glob('*.json'))
    paths += [root/p for p in ('tests/preparation_model.cpp','tests/guided_plant.cpp','tests/test_preparation.py',
        'tools/verify_preparation.py','docs/design/PREPARATION.md','docs/testing/PREPARATION.md')]
    return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths) if p.is_file()}


def applicable(report,root=ROOT):
    return (report.get('schema_version')==1 and report.get('source_sha256')==inputs(root)
            and report.get('successful') is True and report.get('tests_run',0)>0
            and all(c.get('result')=='passed' for c in report.get('cases',[]))
            and len(report.get('cases',[]))==report['tests_run'])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path)
    parser.add_argument('--check',type=Path)
    args=parser.parse_args()
    if args.check:
        ok=applicable(json.loads(args.check.read_text()))
        print('Preparation evidence applicable: '+str(ok));return 0 if ok else 1
    if not args.output:parser.error('--output or --check is required')
    if args.output.exists():parser.error('output already exists; preserve previous execution')
    sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'tools')]
    from verify_m1 import RecordedResults
    import io
    start=inputs();stream=io.StringIO()
    captures=args.output.parent/(args.output.stem+'-cases');captures.mkdir(parents=True,exist_ok=False)
    os.environ['DIALYSISLAB_PREPARATION_CAPTURE']=str(captures)
    suite=unittest.defaultTestLoader.loadTestsFromName('test_preparation')
    result=unittest.TextTestRunner(stream=stream,verbosity=2,resultclass=RecordedResults).run(suite)
    document=dict(schema_version=1,executed_at=datetime.now(timezone.utc).isoformat(),
        command=['python3','tools/verify_preparation.py','--output',str(args.output)],
        source_revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        worktree_dirty_at_execution=bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip()),
        verification_input_sha256=hashlib.sha256(json.dumps(start,sort_keys=True,separators=(',',':')).encode()).hexdigest(),
        source_sha256=start,inputs_unchanged=start==inputs(),
        environment=dict(python=platform.python_version(),platform=platform.platform(),
            compiler=subprocess.check_output(['g++','--version'],text=True).splitlines()[0]),
        tests_run=result.testsRun,cases=result.cases,output=stream.getvalue(),
        successful=result.wasSuccessful() and not result.skipped and start==inputs(),
        results={p.name:json.loads(p.read_text()) for p in sorted(captures.glob('*.json'))},
        scope='Actual production Plant and patient over pipes; component eight-hour simulation; no clinical calibration or independent review.')
    args.output.write_text(json.dumps(document,indent=2)+'\n');print(stream.getvalue(),end='')
    return 0 if document['successful'] else 1


if __name__=='__main__':sys.exit(main())
