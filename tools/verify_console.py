#!/usr/bin/env python3
"""Record actual external console widget/broker/service integration."""
import argparse
from datetime import datetime,timezone
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'python'));sys.path.insert(0,str(ROOT/'tools'))
from dialysislab.runner import build_identity
from capture_png import convert
from verify_m1 import RecordedResults


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build-dir',type=Path,default=ROOT/'build/gui');p.add_argument('--output',required=True,type=Path);p.add_argument('--graphical',action='store_true');args=p.parse_args()
    args.output.mkdir(parents=True,exist_ok=False)
    os.environ.update(DIALYSISLAB_BUILD_DIR=str(args.build_dir.resolve()),DIALYSISLAB_GUI_BUILD_DIR=str(args.build_dir.resolve()),DIALYSISLAB_CONSOLE_EVIDENCE=str(args.output.resolve()),DIALYSISLAB_CONSOLE_GRAPHICAL='1' if args.graphical else '0')
    spec=importlib.util.spec_from_file_location('console_regressions',ROOT/'tests/console_regressions.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    output=io.StringIO();result=unittest.TextTestRunner(stream=output,verbosity=2,resultclass=RecordedResults).run(unittest.defaultTestLoader.loadTestsFromModule(module))
    for path in args.output.rglob('*.ppm'):convert(path,path.with_suffix('.png'))
    report=dict(schema_version=1,executed_at=datetime.now(timezone.utc).isoformat(),command=sys.argv,build=build_identity(args.build_dir),dependencies=json.loads((ROOT/'gui_dependencies.json').read_text()),graphical=args.graphical,tests_run=result.testsRun,successful=result.wasSuccessful() and not result.skipped,cases=result.cases,output=output.getvalue(),console_binary_sha256=hashlib.sha256((args.build_dir/'sim-console').read_bytes()).hexdigest(),artifacts={str(p.relative_to(args.output)):hashlib.sha256(p.read_bytes()).hexdigest() for p in args.output.rglob('*') if p.is_file()})
    (args.output/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(output.getvalue(),end='');return 0 if report['successful'] else 1


if __name__=='__main__':sys.exit(main())
