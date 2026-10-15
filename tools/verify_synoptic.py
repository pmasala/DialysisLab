#!/usr/bin/env python3
"""Source-bound synthetic UI execution; requires a real LVGL build, no skipped passes."""
import argparse
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]


def inputs():
    paths=[p for folder in ('src','python/dialysislab','scenarios') for p in (ROOT/folder).rglob('*') if p.suffix in ('.cpp','.hpp','.h','.py','.json')]
    paths += [ROOT/p for p in ('CMakeLists.txt','cmake/Gui.cmake','gui_dependencies.json','docs/wire-contract.json',
        'tests/synoptic_app.cpp','tests/synoptic_motion.cpp','tests/synoptic_view.cpp','tests/test_synoptic.py','tests/guided_view.cpp','tests/guided_plant.cpp',
        'tests/test_guided.py','tests/wire_contract_witness.cpp','tests/test_document_contracts.py','tools/verify_synoptic.py','tools/verify_m1.py')]
    return {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(set(paths))}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path);parser.add_argument('--check',type=Path);args=parser.parse_args()
    if args.check:
        report=json.loads(args.check.read_text());ok=report.get('successful') is True and report.get('source_sha256')==inputs()
        print('Synoptic evidence applicable: '+str(ok));return 0 if ok else 1
    if not args.output or args.output.exists():parser.error('choose a new --output path')
    sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'tools')]
    from verify_m1 import RecordedResults
    start=inputs();stream=io.StringIO();selection=['test_synoptic','test_guided.GuidedUnitTests','test_document_contracts.WireWitnessTests']
    suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(name) for name in selection)
    result=unittest.TextTestRunner(stream=stream,verbosity=2,resultclass=RecordedResults).run(suite)
    build=Path(os.environ.get('DIALYSISLAB_GUI_BUILD_DIR',ROOT/'build/gui'))
    document=dict(schema_version=1,executed_at=datetime.now(timezone.utc).isoformat(),source_revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        worktree_dirty_at_execution=bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip()),source_sha256=start,
        verification_input_sha256=hashlib.sha256(json.dumps(start,sort_keys=True,separators=(',',':')).encode()).hexdigest(),
        environment=dict(python=platform.python_version(),compiler=subprocess.check_output(['g++','--version'],text=True).splitlines()[0],
            lvgl='9.6.0',build_identity=json.loads((build/'build_identity.json').read_text())),
        command=['python3','tools/verify_synoptic.py','--output',str(args.output)],selection=selection,tests_run=result.testsRun,cases=result.cases,output=stream.getvalue(),
        successful=result.wasSuccessful() and not result.skipped and start==inputs(),
        scope='Synthetic LVGL renderer/pointer tests, C++/Python wire boundaries and actual Plant/patient over pipes. Not real Unix IPC, physical touch hardware, representative-user approval, numerical closure or clinical validation.')
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(document,indent=2)+'\n');print(stream.getvalue(),end='');return 0 if document['successful'] else 1


if __name__=='__main__':sys.exit(main())
