"""Streaming, byte-hash and interrupted-run regressions; RSS measured in a process."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'python'))
from dialysislab.runner import LocalCluster, validate
from dialysislab.trajectory import TrajectoryWriter, read_records, scan
BUILD = Path(os.environ.get('DIALYSISLAB_BUILD_DIR', ROOT / 'build'))


class TrajectoryTests(unittest.TestCase):
    def test_100000_records_rss_order_repeatability_and_hash(self):
        validate(json.loads((ROOT / 'scenarios/hd_100000.json').read_text()))
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run([sys.executable, str(ROOT / 'tests/trajectory_memory_probe.py'), directory],
                                    text=True, capture_output=True, timeout=60, check=True)
            report = json.loads(result.stdout)
            self.assertLessEqual(report['peak_rss_bytes'], 64*1024**2)
            self.assertEqual(report['runs'][0]['sha256'], report['runs'][1]['sha256'])
            self.assertEqual(report['runs'][0]['records'], 100000)
            for n, record in enumerate(read_records(Path(directory) / '0/trajectory.jsonl')):
                self.assertEqual(record['sequence'], n)
                self.assertEqual(record['time_ms'], (n+1)*100)

    def test_short_writes_hash_exactly_the_written_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            writer = TrajectoryWriter(Path(directory) / 'output')
            original = writer.stream
            class ShortWriter:
                def write(self, data):
                    return original.write(data[:7])
                def close(self):
                    original.close()
            writer.stream = ShortWriter()
            for n in range(10):
                writer.append(dict(sequence=n, message='short write regression'))
            writer.close()
            raw = writer.trajectory.path.read_bytes()  # Ten small records only.
            self.assertEqual(writer.bytes_written, len(raw))
            self.assertEqual(writer.hasher.hexdigest(), hashlib.sha256(raw).hexdigest())
            self.assertEqual(scan(writer.trajectory.path)['records'], 10)

    def test_recovery_discards_only_an_incomplete_final_line(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'trajectory.jsonl'
            complete = b'{"sequence":0}\n{"sequence":1}\n'
            path.write_bytes(complete + b'{"sequence":2')
            report = scan(path, recover=True)
            self.assertEqual(report['records'], 2)
            self.assertEqual(report['sha256'], hashlib.sha256(complete).hexdigest())
            self.assertGreater(report['discarded_tail_bytes'], 0)
            with self.assertRaises(ValueError):
                scan(path)
            path.write_bytes(complete + b'{"sequence":4}\n')
            with self.assertRaises(ValueError):
                scan(path, recover=True)

    def test_killed_real_runner_retains_complete_written_prefix(self):
        with LocalCluster(BUILD) as cluster, tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'interrupted'
            process = subprocess.Popen([sys.executable, '-m', 'dialysislab.runner',
                '--runtime-dir', str(cluster.runtime), '--build-dir', str(BUILD),
                '--config', str(ROOT / 'scenarios/hd_100000.json'), '--output', str(output)],
                env=dict(os.environ, PYTHONPATH=str(ROOT / 'python')),
                stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            try:
                deadline = time.monotonic() + 10
                path = output / 'trajectory.jsonl'
                while not path.exists() or path.stat().st_size < 65536:
                    if process.poll() is not None or time.monotonic() > deadline:
                        self.fail('runner did not stream records before exit/deadline')
                    time.sleep(0.01)
                process.kill()
                _, stderr = process.communicate(timeout=3)
                self.assertEqual(process.returncode, -9, stderr)
                report = scan(path, recover=True)
                self.assertGreater(report['records'], 0)
                self.assertLess(report['records'], 100000)
                manifest = json.loads((output / 'manifest.json').read_text())
                self.assertEqual(manifest['outcome'], 'running')
                self.assertIsNone(manifest['trajectory_sha256'])
                self.assertEqual(report['last']['sequence'] + 1, report['records'])
            finally:
                if process.poll() is None:
                    process.kill()
                process.communicate(timeout=3)
