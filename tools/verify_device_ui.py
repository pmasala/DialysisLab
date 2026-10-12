#!/usr/bin/env python3
"""Run actual LVGL widget/service integration, retain reports and RGB captures."""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'python'))
sys.path.insert(0, str(ROOT / 'tools'))
from dialysislab.runner import build_identity
from capture_png import convert
from verify_m1 import RecordedResults


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build-dir', type=Path, default=ROOT / 'build/gui')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--graphical', action='store_true')
    args = parser.parse_args(); args.output.mkdir(parents=True, exist_ok=False)
    os.environ.update(DIALYSISLAB_GUI_BUILD_DIR=str(args.build_dir.resolve()),
                      DIALYSISLAB_UI_EVIDENCE=str(args.output.resolve()), DIALYSISLAB_UI_GRAPHICAL='1' if args.graphical else '0')
    spec = importlib.util.spec_from_file_location('ui_regressions', ROOT / 'tests/ui_regressions.py')
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    suite = unittest.defaultTestLoader.loadTestsFromModule(module)
    spec_demo = importlib.util.spec_from_file_location('demo_regressions', ROOT / 'tests/demo_regressions.py')
    demo = importlib.util.module_from_spec(spec_demo); spec_demo.loader.exec_module(demo)
    suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(demo))
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=2, resultclass=RecordedResults).run(suite)
    for source in args.output.rglob('*.ppm'): convert(source, source.with_suffix('.png'))
    report = dict(schema_version=1, executed_at=datetime.now(timezone.utc).isoformat(),
                  command=sys.argv, build=build_identity(args.build_dir), dependencies=json.loads((ROOT / 'gui_dependencies.json').read_text()),
                  graphical=args.graphical, display=os.environ.get('DISPLAY'), driver=os.environ.get('SDL_VIDEODRIVER'),
                  tests_run=result.testsRun, successful=result.wasSuccessful() and not result.skipped, cases=result.cases, output=stream.getvalue(),
                  fixture_configuration=json.loads((ROOT / 'scenarios/machine_hdf_post.json').read_text()),
                  demo_configuration=json.loads((ROOT / 'scenarios/device_ui_demo.json').read_text()),
                  test_source_sha256={name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in ('tests/ui_regressions.py','tests/demo_regressions.py')},
                  ui_binary_sha256=hashlib.sha256((args.build_dir / 'device-ui').read_bytes()).hexdigest(),
                  artifacts={str(p.relative_to(args.output)): hashlib.sha256(p.read_bytes()).hexdigest() for p in args.output.rglob('*') if p.is_file()},
                  scope='Actual LVGL widgets/RPCs/rendered frames; synthetic equipment, no clinical usability approval')
    (args.output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(stream.getvalue(), end='')
    return 0 if report['successful'] else 1


if __name__ == '__main__': sys.exit(main())
