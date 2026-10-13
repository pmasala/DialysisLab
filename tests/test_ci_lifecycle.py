"""Ten-minute physical lifecycle, diagnostic isolation and timeout evidence."""
import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from audit_fixture import Coupled,compile_driver
from dialysislab.runner import ProgressReporter,validate
from dialysislab.trajectory import TrajectoryWriter,read_records
from verify_integrated import configurations,acceptance
from verify_compose import live_command,CommandFailure
from retain_dynamic_resources import retain
from ci_artifacts import recover


class ShortLifecycleTests(unittest.TestCase):
    def test_exact_scheduled_ten_minute_cycle_repeats_with_progress_enabled(self):
        name,config=next(configurations('dynamic-short'));validate(config)
        self.assertEqual(config['ticks'],1440)
        self.assertEqual(config['dt_ms'],500)
        hashes=[]
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);binary=compile_driver(directory)
            events={e['tick']:e['action'] for e in config['workflow']}
            for repeat in (1,2):
                writer=TrajectoryWriter(root/str(repeat));f=Coupled(binary,config)
                progress=ProgressReporter(writer.directory,config,100) if repeat==2 else None
                try:
                    with contextlib.redirect_stdout(io.StringIO()):
                        if progress:progress.update(0,force=True)
                        for n in range(config['ticks']):
                            r=f.step(action=events.get(n),auto=False)
                            writer.append(r)
                            if progress:progress.update(n+1,r)
                        if progress:progress.update(config['ticks'],outcome='completed',force=True)
                finally:writer.close();f.close()
                result=acceptance(writer.directory,config,'dynamic-short',name)
                self.assertEqual(result['integrated_treatment_ms'],600000)
                self.assertEqual(result['stage_order'][-1],'CLEANED')
                self.assertIsNone(result['first_alarm_ms'])
                for r in read_records(writer.directory/'trajectory.jsonl'):
                    self.assertTrue(all(abs(x)<1e-6 for x in r['patient']['mass_residual_mmol']))
                hashes.append(writer.hasher.hexdigest())
                if progress:
                    state=json.loads((writer.directory/'progress.json').read_text())
                    self.assertEqual(state['completed_ticks'],1440)
                    self.assertEqual(state['progress_percent'],100)
                    self.assertEqual(state['stage'],'CLEANED')
                # The acceptance gate must reject omission of each required phase,
                # a shortened therapy and an alarm, even with well-formed timestamps.
                compact=[dict(sequence=r['sequence'],time_ms=r['time_ms'],machine=r['machine'])
                         for r in read_records(writer.directory/'trajectory.jsonl')]
                for missing in result['stage_order']:
                    changed=[r for r in compact if r['machine']['stage']!=missing]
                    with patch('verify_integrated.read_records',return_value=iter(changed)):
                        with self.assertRaises(ValueError):acceptance(writer.directory,config,'dynamic-short',name)
                import copy
                changed=copy.deepcopy(compact);changed[-1]['machine']['guided']['treatment_elapsed_ms']=599500
                with patch('verify_integrated.read_records',return_value=iter(changed)):
                    with self.assertRaises(ValueError):acceptance(writer.directory,config,'dynamic-short',name)
                changed=copy.deepcopy(compact);changed[100]['machine']['alarm_mask']=4
                with patch('verify_integrated.read_records',return_value=iter(changed)):
                    with self.assertRaises(ValueError):acceptance(writer.directory,config,'dynamic-short',name)
            self.assertEqual(hashes[0],hashes[1])
            print(json.dumps(dict(scope='Actual plant/patient pipe harness, no RPC/container claim',
                ticks_per_run=config['ticks'],repetitions=2,trajectory_sha256=hashes[0],acceptance=result)))

    def test_progress_is_atomic_diagnostic_and_retained_on_failure(self):
        with tempfile.TemporaryDirectory() as directory,contextlib.redirect_stdout(io.StringIO()):
            root=Path(directory);out=root/'integrated_dynamic_hdf_10min-1/results/run';out.mkdir(parents=True)
            p=ProgressReporter(out,dict(ticks=1200,dt_ms=500),100)
            p.update(0,force=True)
            record=dict(machine=dict(stage='TREATMENT',guided=dict(treatment_elapsed_ms=500,duration_ms=600000)))
            p.update(1,record);before=(out/'progress.json').read_bytes()
            p.update(2,record);self.assertEqual((out/'progress.json').read_bytes(),before)
            p.update(2,outcome='aborted',force=True)
            self.assertEqual(json.loads((out/'progress.json').read_text())['completed_ticks'],2)
            stream=io.StringIO();retain(root,stream);recover(io.StringIO(stream.getvalue()),root/'recovered')
            self.assertEqual((root/'recovered/dynamic-resources/integrated_dynamic_hdf_10min-1/results/run/progress.json').read_bytes(),(out/'progress.json').read_bytes())
            before=(out/'progress.json').read_bytes();write=Path.write_text
            def partial(path,text,*args,**kwargs):
                write(path,text[:8],*args,**kwargs);raise OSError('injected full disk')
            with patch.object(Path,'write_text',partial):
                with self.assertRaises(OSError):p.update(3,force=True)
            self.assertEqual((out/'progress.json').read_bytes(),before)

    def test_live_command_preserves_failure_and_timeout_output(self):
        with contextlib.redirect_stdout(io.StringIO()) as log:
            self.assertEqual(live_command([sys.executable,'-c','print("progress 100")'],timeout=10),'progress 100\n')
            self.assertIn('progress 100',log.getvalue())
            with self.assertRaises(CommandFailure) as failed:
                live_command([sys.executable,'-c','print("failed prefix");raise SystemExit(7)'],timeout=10)
            self.assertEqual(failed.exception.returncode,7)
            self.assertIn('failed prefix',failed.exception.output)
            with self.assertRaises(CommandFailure) as expired:
                live_command([sys.executable,'-c','import time;print("last tick 10",flush=True);time.sleep(10)'],timeout=.5)
            self.assertEqual(expired.exception.returncode,124)
            self.assertIn('last tick 10',expired.exception.output)
            self.assertIn('Verification timeout',expired.exception.output)

class HostedRunnerProgressTests(unittest.TestCase):
    def test_real_runner_progress_and_aborted_prefix(self):
        import os
        from dialysislab import runner
        root=Path(__file__).resolve().parents[1]
        build=Path(os.environ.get('DIALYSISLAB_BUILD_DIR',root/'build/gui'))
        config=json.loads((root/'scenarios/hd_nominal.json').read_text())
        hashes=[]
        with tempfile.TemporaryDirectory() as directory,contextlib.redirect_stdout(io.StringIO()):
            for every in (0,3):
                out=Path(directory)/str(every)
                with runner.LocalCluster(build) as cluster:
                    _,manifest=runner.simulate(config,cluster.runtime,build,out,progress_every=every)
                self.assertEqual(manifest['outcome'],'completed',manifest['errors'])
                hashes.append(manifest['trajectory_sha256'])
                if every:
                    progress=json.loads((out/'progress.json').read_text())
                    self.assertEqual(progress['completed_ticks'],config['ticks'])
                    self.assertEqual(progress['outcome'],'completed')
            self.assertEqual(hashes[0],hashes[1])
            def fail(n):
                if n==5:raise RuntimeError('injected failure after five completed ticks')
            out=Path(directory)/'aborted'
            with runner.LocalCluster(build) as cluster:
                _,manifest=runner.simulate(config,cluster.runtime,build,out,before_tick=fail,progress_every=3)
            progress=json.loads((out/'progress.json').read_text())
            self.assertEqual(manifest['outcome'],'aborted')
            self.assertTrue(manifest['stop']['outputs_zero_observed'])
            self.assertEqual(progress['completed_ticks'],5)
            self.assertEqual(progress['outcome'],'aborted')

if __name__=='__main__':unittest.main()
