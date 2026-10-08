"""Lossless evidence storage preserves bytes and never drops a failed source."""
import gzip
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from verify_integrated import archive_trajectory
from dialysislab.trajectory import scan,read_records


class IntegrationTests(unittest.TestCase):
    def test_archived_trajectory_restores_original_order_hash_and_existing_readers(self):
        raw=b''.join(json.dumps(dict(sequence=n,time_ms=(n+1)*100,value=n/7),indent=None).encode()+b'\n' for n in range(1000))
        expected=hashlib.sha256(raw).hexdigest();archives=[]
        with tempfile.TemporaryDirectory() as tmp:
            for repeat in (1,2):
                path=Path(tmp)/str(repeat)/'trajectory.jsonl';path.parent.mkdir();path.write_bytes(raw)
                result=archive_trajectory(path,expected);self.assertFalse(path.exists())
                self.assertEqual(result['original_sha256'],expected)
                archive=Path(result['path']);archives.append(archive.read_bytes())
                path.write_bytes(gzip.decompress(archive.read_bytes()))
                self.assertEqual(scan(path)['sha256'],expected)
                self.assertEqual([r['sequence'] for r in read_records(path)],list(range(1000)))
                self.assertEqual(json.loads((path.parent/'trajectory-storage.json').read_text()),result)
            self.assertEqual(archives[0],archives[1])

    def test_wrong_hash_or_existing_archive_preserves_raw_trajectory(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'trajectory.jsonl';raw=b'{"sequence":0}\n';path.write_bytes(raw)
            with self.assertRaisesRegex(ValueError,'changed'):archive_trajectory(path,'0'*64)
            self.assertEqual(path.read_bytes(),raw)
            self.assertFalse(path.with_suffix('.jsonl.gz').exists())
            with self.assertRaisesRegex(ValueError,'already exists'):archive_trajectory(path,hashlib.sha256(raw).hexdigest())
            self.assertEqual(path.read_bytes(),raw)


if __name__=='__main__':unittest.main()
