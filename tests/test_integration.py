"""Lossless evidence storage preserves bytes and never drops a failed source."""
import gzip
import errno
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from verify_integrated import archive_trajectory,configurations,write_configuration,write_report,acceptance
import verify_package
from dialysislab.trajectory import scan,read_records


class IntegrationTests(unittest.TestCase):
    def test_partial_enospc_report_write_preserves_previous_completed_case(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'integration.json'
            prior={'successful':False,'cases':[{'repeat':1,'verified':True}]}
            write_report(path,prior);original=path.read_bytes();writer=Path.write_text
            def partial(destination,content,*args,**kwargs):
                writer(destination,content[:7],*args,**kwargs)
                raise OSError(errno.ENOSPC,'injected full filesystem')
            with patch.object(Path,'write_text',partial):
                with self.assertRaises(OSError):write_report(path,{'successful':False,'error':'run failed','cases':prior['cases']})
            self.assertEqual(path.read_bytes(),original)
            self.assertEqual(path.with_suffix('.json.tmp').read_text(),'{\n  "su')

    def test_sustained_fixture_reaches_deliverable_gross_uf_without_alarm(self):
        from dialysislab.runner import LocalCluster,simulate,stop_plant,build_identity
        from verify_models import verify
        build=Path(os.environ.get('DIALYSISLAB_BUILD_DIR',ROOT/'build/gui'))
        for name,config in [('long',next(configurations('long'))[1]),('large',list(configurations('matrix'))[-1][1])]:
            config['ticks']=1500;config['dt_ms']=1000;config['workflow']=[e for e in config['workflow'] if e['tick']<=94]
            with self.subTest(profile=name),tempfile.TemporaryDirectory() as tmp,LocalCluster(build) as cluster:
                directory=Path(tmp)/'run';_,manifest=simulate(config,cluster.runtime,build,directory)
                stopped=stop_plant(cluster.runtime/'admin/plant.sock',True)
                self.assertEqual(manifest['outcome'],'completed',manifest['errors']);self.assertTrue(stopped['outputs_zero_observed'])
                result=verify(directory,config,build_identity(build)['source_sha256'])
                for record in read_records(directory/'trajectory.jsonl'):
                    self.assertEqual(record['machine']['alarm_mask'],0)
                    if record['sequence']>=200:
                        self.assertGreater(record['uf_mL_min'],60)
                        self.assertAlmostEqual(record['uf_mL_min']-record['online']['replacement_mL_min'],5,delta=1e-6)
                self.assertGreater(result['scan']['last']['removed_total_mL'],1000)

    def test_generated_compose_fixture_is_readable_under_restrictive_umask(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'scenario.json';config=next(configurations('matrix'))[1]
            previous=os.umask(0o077)
            try:write_configuration(path,config,container_readable=True)
            finally:os.umask(previous)
            self.assertEqual(path.stat().st_mode&0o777,0o644)
            self.assertEqual(json.loads(path.read_text()),config)

    def test_package_without_git_retains_actual_failed_packaging_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'source';(root/'tools').mkdir(parents=True)
            (root/'publication_manifest.json').write_text('{"files":[]}\n')
            (root/'tools/package_release.py').write_text('print("fixture packaging failed")\nraise SystemExit(7)\n')
            output=Path(tmp)/'verification'
            with patch.object(verify_package,'ROOT',root),patch.object(sys,'argv',['verify_package.py','--output',str(output)]):
                with self.assertRaisesRegex(RuntimeError,'package-1 failed'):verify_package.main()
            report=json.loads((output/'package-verification.json').read_text())
            self.assertEqual(report['source_revision'],'unavailable');self.assertIsNone(report['source_worktree_dirty'])
            self.assertFalse(report['successful']);self.assertEqual(report['steps'][0]['exit_code'],7)
            self.assertIn('fixture packaging failed',(output/'package-1.log').read_text())

    def test_integrated_evidence_rejects_consistent_but_wrong_virtual_time(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp);(path/'trajectory.jsonl').write_text('{"sequence":0,"time_ms":200}\n')
            with self.assertRaisesRegex(ValueError,'timestamp'):acceptance(path,{'dt_ms':100},'matrix','tampered')

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
