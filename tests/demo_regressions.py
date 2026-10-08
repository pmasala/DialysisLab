"""Real demo launcher failure/closure regression, including paced waits."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
BUILD = Path(os.environ.get('DIALYSISLAB_GUI_BUILD_DIR', ROOT / 'build/gui')).resolve()


class DemoLauncherTests(unittest.TestCase):
    def run_demo(self, output, *args):
        argv = [sys.executable, str(ROOT / 'tools/run_device_demo.py'), '--build-dir', str(BUILD),
                '--headless', '--output', str(output), *args]
        started = time.monotonic()
        result = subprocess.run(argv, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=8)
        return result, json.loads((output / 'demo.json').read_text()), time.monotonic() - started

    def test_unexpected_workflow_abort_returns_failure_despite_confirmed_halt(self):
        with tempfile.TemporaryDirectory(prefix='dl-ui-failure-') as directory:
            root = Path(directory)
            config = json.loads((ROOT / 'scenarios/device_ui_demo.json').read_text())
            config['workflow'] = [dict(tick=0, action='START', values=[])]
            path = root / 'rejected.json'; path.write_text(json.dumps(config))
            result, report, _ = self.run_demo(root / 'run', '--config', str(path), '--seconds', '2')
            self.assertNotEqual(result.returncode, 0, result.stdout)
            self.assertEqual(report['run_outcome'], 'aborted')
            self.assertIn('workflow rejected', report['run_errors'][0])
            self.assertTrue(report['stop']['acknowledged'])
            self.assertTrue(report['stop']['outputs_zero_observed'])
            self.assertFalse(report['expected_window_closure'])

    def test_window_closure_interrupts_100_second_pacing_wait(self):
        with tempfile.TemporaryDirectory(prefix='dl-ui-closure-') as directory:
            result, report, elapsed = self.run_demo(Path(directory) / 'run', '--seconds', '1', '--wall-speed', '.001')
            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertLess(elapsed, 4, 'closure must not await next 100-second virtual tick')
            self.assertTrue(report['expected_window_closure'])
            self.assertEqual(report['run_errors'], ['device window closed, exit=0'])
            self.assertTrue(report['stop']['acknowledged'])
            self.assertTrue(report['stop']['outputs_zero_observed'])
            manifest = json.loads((Path(directory) / 'run/run/manifest.json').read_text())
            self.assertEqual(manifest['completed_ticks'], 1)
            self.assertEqual(manifest['aborted_tick']['sequence'], 1)
