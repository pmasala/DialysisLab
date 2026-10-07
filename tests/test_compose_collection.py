"""Collection/cleanup order and original error-code preservation without a daemon."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import verify_compose as verify


class ComposeCollectionTests(unittest.TestCase):
    def exercise(self, code, extraction_failure=False, runner_started=True, cleanup_failure=False):
        calls = []
        with tempfile.TemporaryDirectory() as directory:
            def command(args, env=None, timeout=120):
                calls.append(args)
                if 'up' in args:
                    if code:
                        raise verify.CommandFailure(args, code, 'original Compose failure log')
                    return 'completed'
                if 'logs' in args:
                    return 'all available service logs'
                if 'cp' in args:
                    if extraction_failure or not runner_started:
                        raise verify.CommandFailure(args, 19, 'artifact extraction failed')
                    output = Path(args[-1]) / 'run'
                    output.mkdir(parents=True)
                    (output / 'manifest.json').write_text('{"outcome":"aborted","completed_ticks":1}')
                    (output / 'trajectory.jsonl').write_text('{"sequence":0}\n')
                    return ''
                if cleanup_failure and 'down' in args:
                    raise verify.CommandFailure(args, 23, 'cleanup failed')
                return ''
            with patch.object(verify, 'command', side_effect=command), \
                 patch.object(verify, 'inspect_services', return_value=[]):
                report = verify.collect_case('synthetic', 1, Path(directory), project='dl-test-collection')
            stored = json.loads((Path(report['directory']) / 'collection.json').read_text())
            self.assertEqual(report, stored)
            self.assertEqual(report['compose_exit_code'], code)
            failure = verify.ComposeRunFailure(report)
            self.assertEqual(failure.returncode, code or 1)
            self.assertTrue((Path(report['directory']) / 'compose.log').is_file())
            self.assertTrue((Path(report['directory']) / 'services.log').is_file())
            cp_index = next(i for i,c in enumerate(calls) if 'cp' in c)
            cleanup_index = next(i for i,c in enumerate(calls) if 'down' in c or 'stop' in c)
            self.assertLess(cp_index, cleanup_index)
            if extraction_failure or not runner_started:
                self.assertFalse(any('--volumes' in c for c in calls))
                self.assertTrue(report['resources_retained'])
                self.assertEqual(report['collection_errors'][0]['stage'], 'extract')
                self.assertTrue((Path(report['directory']) / 'RECOVERY.txt').is_file())
            else:
                self.assertTrue(report['extracted'])
                self.assertTrue((Path(report['directory']) / 'results/run/trajectory.jsonl').is_file())
            return report

    def test_aborted_runner_artifacts_collected_before_volume_removal(self):
        self.exercise(7)

    def test_failure_before_runner_start_preserves_original_code(self):
        self.exercise(17, runner_started=False)

    def test_failed_extraction_keeps_volume_and_recovery_commands(self):
        self.exercise(7, extraction_failure=True)

    def test_collection_failure_after_success_has_separate_error(self):
        self.exercise(0, extraction_failure=True)

    def test_cleanup_failure_does_not_replace_original_exit_code(self):
        report = self.exercise(7, cleanup_failure=True)
        self.assertTrue(report['cleanup_errors'])
