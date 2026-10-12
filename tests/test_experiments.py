"""Actual DX1 broker and separate services; no fixed simulation responses."""
import hashlib
import json
import os
from pathlib import Path
import socket
import sys
import tempfile
import threading
import time
import unittest
import uuid
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'python'))
from dialysislab import experiment_rpc as wire
from dialysislab.experiments import Broker, Server, bounded_json
from dialysislab.protocol import rpc
from dialysislab.trajectory import scan
BUILD = Path(os.environ.get('DIALYSISLAB_BUILD_DIR', ROOT / 'build/gui'))


def wait_for(function, expected=lambda x: bool(x), timeout=15):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        value = function()
        if expected(value): return value
        time.sleep(.02)
    raise AssertionError('deadline exceeded: ' + str(value)[:1000])


class Fixture:
    def __enter__(self):
        self.temp = tempfile.TemporaryDirectory(prefix='dl-exp-')
        self.root = Path(self.temp.name)
        self.broker = Broker(BUILD, self.root / 'runs')
        self.server = Server(self.root / 'api', self.broker)
        self.thread = threading.Thread(target=self.server.serve_forever, kwargs=dict(poll_interval=.02))
        self.thread.start()
        return self
    def __exit__(self, *_):
        self.broker.close(); self.server.shutdown(); self.thread.join(); self.server.server_close(); self.temp.cleanup()
    def call(self, op, args=None): return wire.request(self.root / 'api', op, args)
    def configure(self, preset='machine_hd', **updates):
        config = json.loads((ROOT / 'scenarios' / (preset+'.json')).read_text()); config.update(updates)
        self.call('VALIDATE',dict(revision=self.call('STATUS')['revision'],configuration=config)); return config
    def start(self, speed=0):
        return self.call('START',dict(revision=self.call('STATUS')['revision'],request_id=uuid.uuid4().hex,wall_speed=speed))['run_id']
    def finished(self):
        return wait_for(lambda:self.call('STATUS'),lambda s:s['state'] not in ('starting','running','paused','pause_requested','stopping'))
    def job(self, op, args):
        job = self.call(op,args)['job_id']
        status = wait_for(lambda:self.call('STATUS')['job'],lambda s:s['id']==job and s['state']!='running')
        if status['state']!='completed': raise AssertionError(status)
        return status['result']


class ExperimentTests(unittest.TestCase):
    def test_pause_liveness_immutable_configuration_exact_replay_compare_export(self):
        with Fixture() as f:
            config=f.configure(ticks=70,workflow=[e for e in json.loads((ROOT/'scenarios/machine_hd.json').read_text())['workflow'] if e['tick']<70])
            original=f.start(10)
            wait_for(lambda:f.call('STATUS'),lambda s:s['sequence']>=5)
            f.call('PAUSE',dict(run_id=original))
            paused=wait_for(lambda:f.call('STATUS'),lambda s:s['state']=='paused')
            f.configure('machine_hdf_post')  # next draft cannot affect immutable active config
            time.sleep(2.2)
            still=f.call('STATUS');self.assertEqual(paused['sequence'],still['sequence'])
            runtime=f.broker.current_runtime
            self.assertNotEqual(rpc(runtime/'admin/plant.sock','STATUS4')[10],'liveness')
            for role in ('control','protection'):
                path=runtime/'device'/(role+'.sock');session=rpc(path,'HELLO6')[1]
                self.assertEqual(rpc(path,'REQUEST6',session,'PRIME' if role=='control' else 'RESET'),['REJECT','scheduled'])
                self.assertEqual(rpc(path,'OPERATOR7','REQUEST5','PRIME'),['REJECT','scheduled'])
                self.assertEqual(rpc(path,'STATUS6',session)[0],'VIEW6')
            f.call('RESUME',dict(run_id=original));first=f.finished()
            self.assertEqual(first['state'],'completed',first)
            self.assertTrue(first['experiment']['stop']['outputs_zero_observed'])
            stored=bounded_json(f.root/'runs'/original/'data/manifest.json')
            self.assertEqual(stored['configuration'],config)
            replay=f.call('REPLAY',dict(run_id=original,request_id=uuid.uuid4().hex,wall_speed=0))['run_id']
            second=f.finished();self.assertEqual(second['state'],'completed',second)
            result=f.job('COMPARE',dict(left=original,right=replay));self.assertTrue(result['exact_replay'],result)
            export=f.job('EXPORT',dict(run_id=replay));path=f.root/'runs'/export['file']
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),export['sha256'])
            with zipfile.ZipFile(path) as archive:
                self.assertIn('data/trajectory.jsonl',archive.namelist())
                self.assertNotIn('token',archive.namelist())
                self.assertEqual(archive.read('data/trajectory.jsonl'),(f.root/'runs'/replay/'data/trajectory.jsonl').read_bytes())

    def test_external_stop_while_paused_aborts_without_resume_or_another_tick(self):
        with Fixture() as f:
            f.configure();identifier=f.start(10)
            wait_for(lambda:f.call('STATUS'),lambda s:s['sequence']>=4)
            f.call('PAUSE',dict(run_id=identifier));before=wait_for(lambda:f.call('STATUS'),lambda s:s['state']=='paused')
            runtime=f.broker.current_runtime
            session=rpc(runtime/'device/control.sock','HELLO6')[1]
            started=time.monotonic()
            self.assertEqual(rpc(runtime/'device/control.sock','STOP6',session),['OK'])
            from dialysislab.treatment import live
            observed=live(rpc(runtime/'admin/plant.sock','STATUS4'))
            self.assertEqual(observed['blood_mL_min'],0)
            after=wait_for(lambda:f.call('STATUS'),lambda s:s['state']=='aborted',timeout=2)
            self.assertLess(time.monotonic()-started,2)
            self.assertEqual(after['state'],'aborted')
            self.assertEqual(after['sequence'],before['sequence'])
            self.assertTrue(after['experiment']['stop']['outputs_zero_observed'])
            manifest=bounded_json(f.root/'runs'/identifier/'data/manifest.json')
            self.assertTrue(any('device STOP during virtual pause' in error for error in manifest['errors']),manifest['errors'])
            self.assertTrue(manifest['stop']['pending_tick_cancelled'])

    def test_broker_stop_retains_partial_manifest_and_fresh_run_succeeds(self):
        with Fixture() as f:
            f.configure();identifier=f.start(.001)
            wait_for(lambda:f.call('STATUS'),lambda s:s['sequence']==0)
            started=time.monotonic();f.call('STOP',dict(run_id=identifier));done=f.finished()
            self.assertLess(time.monotonic()-started,2)
            self.assertEqual(done['state'],'aborted');self.assertEqual(done['sequence'],0)
            self.assertTrue(done['experiment']['stop']['outputs_zero_observed'])
            result=f.job('EXPORT',dict(run_id=identifier));self.assertTrue((f.root/'runs'/result['file']).is_file())
            f.configure(ticks=4,workflow=[],faults=[]);other=f.start();done=f.finished()
            self.assertNotEqual(other,identifier);self.assertEqual(done['state'],'completed')

    def test_authentication_limits_paths_and_compare_reject_tampering(self):
        with Fixture() as f:
            with self.assertRaisesRegex(ValueError,'unauthorized'):wire.request(f.root/'api','STATUS',token='0'*64)
            for op,args in [('LOAD',dict(name='../../README',revision=1)),('EXPORT',dict(run_id='../secret')),('START',dict(revision=999,request_id=uuid.uuid4().hex,wall_speed=0)),('HALT',{})]:
                with self.subTest(op=op),self.assertRaises(ValueError): f.call(op,args)
            self.assertEqual((f.root/'api/token').stat().st_mode & 0o777,0o600)
            with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as connection:
                connection.settimeout(3);connection.connect(str(f.root/'api/broker.sock'));connection.sendall(b'DX1 wrong STATUS 7b7d\n')
                self.assertIn(b'ERROR',connection.recv(4096))
            f.configure(ticks=4,workflow=[],faults=[]);identifier=f.start();self.assertEqual(f.finished()['state'],'completed')
            path=f.root/'runs'/identifier/'data/trajectory.jsonl';path.write_bytes(path.read_bytes().replace(b'"sequence":0',b'"sequence":7',1))
            job=f.call('COMPARE',dict(left=identifier,right=identifier))['job_id']
            result=wait_for(lambda:f.call('STATUS')['job'],lambda s:s['id']==job and s['state']=='failed')
            self.assertIn('evidence mismatch',result['error'])

    def test_duplicate_start_ids_are_idempotent_and_stale_run_controls_fail(self):
        with Fixture() as f:
            f.configure(ticks=4,workflow=[],faults=[])
            args=dict(revision=f.call('STATUS')['revision'],request_id=uuid.uuid4().hex,wall_speed=0)
            first=f.call('START',args);again=f.call('START',args);self.assertEqual(first['run_id'],again['run_id'])
            self.assertTrue(again['duplicate']);self.assertEqual(f.finished()['state'],'completed')
            self.assertEqual(len(f.call('RUNS')),1)
            with self.assertRaisesRegex(ValueError,'reused'):f.call('START',dict(args,wall_speed=1))
            with self.assertRaisesRegex(ValueError,'inactive'):f.call('PAUSE',dict(run_id=first['run_id']))
            with self.assertRaisesRegex(ValueError,'already owned'): Broker(BUILD,f.root/'runs')
            f.broker.close()
            old=Broker(BUILD,f.root/'runs')
            duplicate=old.dispatch('START',args);self.assertTrue(duplicate['duplicate']);self.assertIsNone(old.worker)
            old.close()

    def test_failed_service_keeps_fault_manifest_and_restart_never_resumes(self):
        with Fixture() as f:
            f.configure();identifier=f.start(10)
            wait_for(lambda:f.call('STATUS'),lambda s:s['sequence']>=1)
            runtime=f.broker.current_runtime
            rpc(runtime/'patient/service.sock','STOP')
            status=f.finished();self.assertEqual(status['state'],'aborted')
            manifest=bounded_json(f.root/'runs'/identifier/'data/manifest.json')
            self.assertEqual(manifest['outcome'],'aborted');self.assertIsNotNone(manifest['uncommitted_plant_state'])
            path=f.root/'runs'/identifier/'experiment.json';metadata=bounded_json(path);metadata['state']='running';path.write_text(json.dumps(metadata))
            f.broker.close()
            restarted=Broker(BUILD,f.root/'runs');self.assertEqual(restarted.history[identifier]['state'],'interrupted')
            self.assertIsNone(restarted.worker);self.assertEqual(restarted.state,'idle')
            self.assertIn('unconfirmed',restarted.history[identifier]['error'])
            restarted.close()


class ExperimentRecoveryTests(unittest.TestCase):
    def test_interrupted_prefix_and_prestart_failure_export_only_available_evidence(self):
        with Fixture() as f:
            f.configure(ticks=4,workflow=[],faults=[]);identifier=f.start();f.finished()
            directory=f.root/'runs'/identifier
            meta=bounded_json(directory/'experiment.json');meta['state']='interrupted';meta['stop']=None
            (directory/'experiment.json').write_text(json.dumps(meta));f.broker.history[identifier]=meta
            manifest=bounded_json(directory/'data/manifest.json');manifest.update(outcome='running',completed_ticks=0,trajectory_sha256=None)
            (directory/'data/manifest.json').write_text(json.dumps(manifest))
            with (directory/'data/trajectory.jsonl').open('ab') as stream:stream.write(b'{"sequence":4')
            exported=f.job('EXPORT',dict(run_id=identifier))
            self.assertEqual(exported['integrity'],'interrupted_available_evidence')
            with zipfile.ZipFile(f.root/'runs'/exported['file']) as archive:
                recovery=json.loads(archive.read('recovery.json'));self.assertEqual(recovery['prefix']['records'],4)
                self.assertIsNone(recovery['outputs_zero_observed']);self.assertGreater(recovery['prefix']['discarded_tail_bytes'],0)
            import shutil
            shutil.rmtree(directory/'data')
            exported=f.job('EXPORT',dict(run_id=identifier))
            with zipfile.ZipFile(f.root/'runs'/exported['file']) as archive:
                self.assertNotIn('data/manifest.json',archive.namelist())
                self.assertEqual(json.loads(archive.read('recovery.json'))['status'],'no_run_manifest')

    def test_patient_circuit_profile_and_fault_calendar_are_actual_accepted_run_inputs(self):
        with Fixture() as f:
            config=json.loads((ROOT/'scenarios/machine_hdf_post.json').read_text())
            patient=json.loads((ROOT/'scenarios/patient_imbalance.json').read_text())['patient']
            large=json.loads((ROOT/'scenarios/patient_large.json').read_text())['circuit']['profile']
            config['patient']=patient;config['patient_volume_mL']=sum(patient['volume_mL'])
            config['transport']['blood_mmol_L']=patient['concentration_mmol_L'][0]
            config['circuit']['profile']=large
            config['faults']=[dict(tick=550,target='device:air',value=1)]
            # End before the existing recovery workflow because a persistent air
            # detector must reject its reset, not silently authorize treatment.
            config['ticks']=650;config['workflow']=[dict(tick=4,action='PRIME',values=[]),dict(tick=500,action='CONFIGURE',values=[]),dict(tick=504,action='START',values=[])]
            f.call('VALIDATE',dict(configuration=config,revision=f.call('STATUS')['revision']))
            identifier=f.start();done=f.finished();self.assertEqual(done['state'],'completed',done)
            manifest=bounded_json(f.root/'runs'/identifier/'data/manifest.json');self.assertEqual(manifest['configuration'],config)
            from dialysislab.trajectory import read_records
            records=read_records(f.root/'runs'/identifier/'data/trajectory.jsonl')
            last=None
            for record in records:
                if record['sequence']>=550:
                    self.assertIn('air',record['machine']['alarms']);self.assertEqual(record['blood_mL_min'],0)
                last=record
            self.assertEqual(last['sequence'],649)

    def test_full_frame_deadline_and_configuration_bound_preserve_broker(self):
        with Fixture() as f:
            with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as connection:
                connection.settimeout(3);connection.connect(str(f.root/'api/broker.sock'))
                connection.sendall(b'DX1 ')
                started=time.monotonic();response=connection.recv(4096)
                self.assertIn(b'ERROR',response);self.assertLess(time.monotonic()-started,2.8)
            with self.assertRaisesRegex(ValueError,'size limit'):wire.payload({'large':'x'*wire.MAX_JSON})
            self.assertEqual(f.call('STATUS')['state'],'idle')


class ExperimentReviewTests(unittest.TestCase):
    def test_stop_reaches_actual_plant_when_journal_write_fails(self):
        from unittest.mock import patch
        with Fixture() as f:
            f.configure();identifier=f.start(10)
            wait_for(lambda:f.call('STATUS'),lambda s:s['sequence']>=5)
            f.call('PAUSE',dict(run_id=identifier));before=wait_for(lambda:f.call('STATUS'),lambda s:s['state']=='paused')
            with patch.object(f.broker,'event',side_effect=OSError(28,'injected journal filesystem full')):
                reply=f.call('STOP',dict(run_id=identifier));self.assertEqual(reply['state'],'stopping')
                after=f.finished()
            self.assertEqual(after['sequence'],before['sequence'])
            self.assertTrue(after['experiment']['stop']['outputs_zero_observed'])
            self.assertTrue(after['experiment']['stop']['pending_tick_cancelled'])
            metadata=bounded_json(f.root/'runs'/identifier/'experiment.json')
            self.assertEqual(metadata['state'],'aborted');self.assertGreaterEqual(metadata['journal_error']['count'],1)
            self.assertIn('filesystem full',metadata['journal_error']['last'])
            self.assertEqual(f.broker.verify(identifier)[2]['outcome'],'aborted')

    def test_shutdown_rejects_new_start_and_replay_before_joining(self):
        from unittest.mock import patch
        with Fixture() as f:
            f.configure(ticks=4,workflow=[],faults=[]);completed=f.start();f.finished()
            args=dict(revision=f.call('STATUS')['revision'],request_id=uuid.uuid4().hex,wall_speed=0)
            actual_join=f.broker.worker.join;entered=threading.Event();release=threading.Event()
            def blocked_join(*args,**kwargs):
                entered.set();release.wait(3);return actual_join(*args,**kwargs)
            with patch.object(f.broker.worker,'join',side_effect=blocked_join):
                closing=threading.Thread(target=f.broker.close);closing.start();self.assertTrue(entered.wait(2))
                try:
                    for op,value in [('START',args),('REPLAY',dict(run_id=completed,request_id=uuid.uuid4().hex,wall_speed=0))]:
                        with self.subTest(op=op),self.assertRaisesRegex(ValueError,'stopping'):f.call(op,value)
                finally:release.set();closing.join(3)
            self.assertEqual(len(f.call('RUNS')),1)

    def test_incomplete_metadata_does_not_hide_valid_runs_or_lose_files(self):
        from unittest.mock import patch
        with Fixture() as f:
            f.configure(ticks=4,workflow=[],faults=[]);identifier=f.start();f.finished();f.broker.close()
            missing=f.root/'runs'/('r'+'0'*16);missing.mkdir();(missing/'configuration.json').write_text('{"preserved":true}\n')
            malformed=f.root/'runs'/('r'+'f'*16);malformed.mkdir();(malformed/'experiment.json').write_text('{torn')
            recovered=Broker(BUILD,f.root/'runs')
            try:
                self.assertIn(identifier,recovered.history);self.assertEqual(len(recovered.incomplete),2)
                self.assertEqual((malformed/'experiment.json').read_text(),'{torn')
                before=set((f.root/'runs').glob('r*'))
                with patch('dialysislab.experiments.build_identity',side_effect=ValueError('missing build identity')):
                    with self.assertRaisesRegex(ValueError,'missing build'):
                        recovered.dispatch('START',dict(revision=recovered.revision,request_id=uuid.uuid4().hex,wall_speed=0))
                self.assertEqual(before,set((f.root/'runs').glob('r*')))
            finally:recovered.close()

    def test_slow_artifact_writer_retains_ownership_after_join_timeout(self):
        from unittest.mock import patch
        with Fixture() as f:
            entered=threading.Event();release=threading.Event()
            def writer():
                entered.set();release.wait(3);(f.root/'runs/writer-finished').write_text('done')
            f.broker.job_thread=threading.Thread(target=writer);f.broker.job_thread.start();self.assertTrue(entered.wait(1))
            actual_join=f.broker.job_thread.join
            try:
                with patch.object(f.broker.job_thread,'join',side_effect=lambda **_:actual_join(timeout=.01)):
                    with self.assertRaisesRegex(RuntimeError,'ownership retained'):f.broker.close()
                with self.assertRaisesRegex(ValueError,'already owned'):Broker(BUILD,f.root/'runs')
            finally:release.set();actual_join(3);f.broker.close()
            recovered=Broker(BUILD,f.root/'runs');recovered.close()
            self.assertEqual((f.root/'runs/writer-finished').read_text(),'done')

    def test_revisions_cannot_repeat_across_broker_incarnations(self):
        with Fixture() as f:
            old=f.configure('machine_hdf_pre');revision=f.call('STATUS')['revision'];f.broker.close()
            other=Broker(BUILD,f.root/'runs')
            try:
                other.dispatch('LOAD',dict(name='machine_hdf_post',revision=other.revision))
                self.assertNotEqual(other.revision,revision)
                for op,args in [('VALIDATE',dict(configuration=old,revision=revision)),('START',dict(revision=revision,request_id=uuid.uuid4().hex,wall_speed=0))]:
                    with self.subTest(op=op),self.assertRaisesRegex(ValueError,'stale draft'):other.dispatch(op,args)
                self.assertEqual(other.draft['treatment']['mode'],'HDF_POST');self.assertIsNone(other.worker)
            finally:other.close()

    def test_maximum_schedule_persists_replays_compares_and_exports(self):
        with Fixture() as f:
            config=json.loads((ROOT/'scenarios/machine_hd.json').read_text());config.update(ticks=1000)
            config['workflow']=[dict(tick=i,action='SILENCE',values=[120000]) for i in range(1000)]
            config['faults']=[dict(tick=i,target='edge:0',value=dict(resistance=.12345678901234567,closed=False)) for i in range(1000)]
            # Alarm annotation is permitted in PREPARATION; it pumps no blood.
            f.call('VALIDATE',dict(configuration=config,revision=f.call('STATUS')['revision']))
            identifier=f.start();self.assertEqual(f.finished()['state'],'completed')
            directory=f.root/'runs'/identifier
            self.assertGreater((directory/'data/manifest.json').stat().st_size,wire.MAX_JSON)
            self.assertEqual(bounded_json(directory/'configuration.json'),config)
            second=f.call('REPLAY',dict(run_id=identifier,request_id=uuid.uuid4().hex,wall_speed=0))['run_id']
            self.assertEqual(f.finished()['state'],'completed')
            self.assertTrue(f.job('COMPARE',dict(left=identifier,right=second))['exact_replay'])
            self.assertEqual(f.job('EXPORT',dict(run_id=identifier))['integrity'],'verified_manifest_and_trajectory')

    def test_journal_limit_does_not_block_terminal_metadata_or_export(self):
        from dialysislab.experiments import MAX_EVENTS
        with Fixture() as f:
            f.configure(ticks=8,workflow=[],faults=[]);identifier=f.start(1)
            wait_for(lambda:f.call('STATUS'),lambda s:s['sequence']>=1)
            with f.broker.lock:f.broker.events=MAX_EVENTS
            done=f.finished();self.assertEqual(done['state'],'completed')
            meta=bounded_json(f.root/'runs'/identifier/'experiment.json')
            self.assertEqual(meta['state'],'completed');self.assertIn('journal limit',meta['journal_error']['last'])
            self.assertTrue(meta['stop']['outputs_zero_observed'])
            self.assertEqual(f.job('EXPORT',dict(run_id=identifier))['integrity'],'verified_manifest_and_trajectory')

    def test_comparison_and_export_reject_every_contradictory_identity(self):
        import copy
        with Fixture() as f:
            f.configure(ticks=4,workflow=[],faults=[]);identifier=f.start();f.finished()
            path=f.root/'runs'/identifier/'experiment.json';original=bounded_json(path)
            corruptions={
                'build':dict(original['build'],binary_sha256={'plant':'f'*64}),
                'trajectory_sha256':'0'*64,'completed_ticks':3,'scheduled':False,
                'stop':dict(original['stop'],outputs_zero_observed=False),'wall_speed':20,
                'pacing_owner':'incorrect','state':'aborted','run_id':'r'+'0'*16}
            for key,value in corruptions.items():
                with self.subTest(field=key):
                    bad=copy.deepcopy(original);bad[key]=value;path.write_text(json.dumps(bad))
                    with self.assertRaisesRegex(ValueError,'mismatch'):f.broker.compare(identifier,identifier)
                    with self.assertRaisesRegex(ValueError,'mismatch'):f.broker.export(identifier)
            path.write_text(json.dumps(original));self.assertTrue(f.broker.compare(identifier,identifier)['exact_replay'])

    def test_initial_and_final_manifest_record_external_pacing_without_double_wait(self):
        with Fixture() as f:
            f.configure(ticks=4,workflow=[],faults=[]);identifier=f.start(.1)
            wait_for(lambda:f.call('STATUS'),lambda s:s['sequence']==0)
            path=f.root/'runs'/identifier/'data/manifest.json'
            initial=bounded_json(path);self.assertEqual(initial['wall_speed'],.1);self.assertEqual(initial['pacing_owner'],'experiment_broker')
            start=time.monotonic();self.assertEqual(f.finished()['state'],'completed');self.assertLess(time.monotonic()-start,4.5)
            final=bounded_json(path);self.assertEqual(final['wall_speed'],.1)
            self.assertEqual(f.broker.verify(identifier)[1]['wall_speed'],final['wall_speed'])

    def test_restarted_inventory_selects_latest_creation_times_not_random_ids(self):
        from datetime import datetime,timedelta,timezone
        import copy
        with Fixture() as f:
            f.configure(ticks=4,workflow=[],faults=[]);identifier=f.start();f.finished();meta=bounded_json(f.root/'runs'/identifier/'experiment.json');f.broker.close()
            expected=[]
            for i in range(105):
                # Synthetic inventory fixtures based on one real completed run;
                # this test does not claim 105 physical executions.
                run_id='r'+format(200-i,'016x');directory=f.root/'runs'/run_id;directory.mkdir()
                record=copy.deepcopy(meta);record.update(run_id=run_id,request_id=uuid.uuid4().hex,created_at=(datetime(2027,1,1,tzinfo=timezone.utc)+timedelta(seconds=i)).isoformat())
                (directory/'experiment.json').write_text(json.dumps(record));expected.append(run_id)
            recovered=Broker(BUILD,f.root/'runs')
            try:self.assertEqual([x['run_id'] for x in recovered.dispatch('RUNS',{})],expected[-100:])
            finally:recovered.close()

    def test_unauthenticated_header_does_not_disclose_experiment_state(self):
        with Fixture() as f:
            f.configure();identifier=f.start(.001);wait_for(lambda:f.call('STATUS'),lambda s:s['sequence']==0)
            with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as connection:
                connection.settimeout(3);connection.connect(str(f.root/'api/broker.sock'))
                connection.sendall(('DX1 '+'0'*64+' STATUS 7b7d\n').encode())
                reply=wire.line(connection).split(' ',7)
            self.assertEqual(reply[:7],['DX1','ERROR','0','-','unauthorized','-1','0'])
            self.assertNotIn(identifier,' '.join(reply))
            f.call('STOP',dict(run_id=identifier));f.finished()


if __name__=='__main__':unittest.main()
