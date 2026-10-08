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

    def test_external_stop_is_immediate_and_aborts_scheduled_tick(self):
        with Fixture() as f:
            f.configure();identifier=f.start(10)
            wait_for(lambda:f.call('STATUS'),lambda s:s['sequence']>=4)
            f.call('PAUSE',dict(run_id=identifier));before=wait_for(lambda:f.call('STATUS'),lambda s:s['state']=='paused')
            runtime=f.broker.current_runtime
            self.assertEqual(rpc(runtime/'device/control.sock','STOP5'),['OK'])
            from dialysislab.treatment import live
            observed=live(rpc(runtime/'admin/plant.sock','STATUS4'))
            self.assertEqual(observed['blood_mL_min'],0)
            self.assertEqual(rpc(runtime/'control/service.sock','CHECK7'),['REJECT','external_stop'])
            f.call('RESUME',dict(run_id=identifier));after=f.finished()
            self.assertEqual(after['state'],'aborted')
            self.assertEqual(after['sequence'],before['sequence'])
            self.assertTrue(after['experiment']['stop']['outputs_zero_observed'])
            manifest=bounded_json(f.root/'runs'/identifier/'data/manifest.json')
            self.assertIn('control:ProtocolError',manifest['rpc_failures'])
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


if __name__=='__main__':unittest.main()
