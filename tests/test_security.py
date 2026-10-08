"""M8 real input/lifecycle/availability regressions; synthetic services only."""
import json
import os
from pathlib import Path
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
import unittest
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'python'))
from dialysislab import experiment_rpc as wire
from dialysislab.protocol import rpc, state
from dialysislab.runner import LocalCluster, simulate
from dialysislab.trajectory import scan, strict_json
from test_experiments import Fixture, wait_for
BUILD = Path(os.environ.get('DIALYSISLAB_BUILD_DIR', ROOT / 'build/gui')).resolve()


class SecurityTests(unittest.TestCase):
    def test_strict_json_rejects_ambiguous_and_unbounded_inputs(self):
        invalid = ['{"seed":1,"seed":2}', '{"x":{"a":1,"a":2}}',
                   '['*33+'0'+']'*33, '1e999', 'NaN', 'Infinity', '1'*129, ' '*1048577]
        for raw in invalid:
            with self.subTest(raw=raw[:50]), self.assertRaises(ValueError): strict_json(raw)
        self.assertEqual(strict_json('{"escaped":"[\\\"{}]", "epoch":'+'9'*49+'}')['epoch'], int('9'*49))
        self.assertEqual(strict_json('['*32+'0'+']'*32), json.loads('['*32+'0'+']'*32))

    def test_patient_rejects_duplicate_or_deep_json_and_survives(self):
        with LocalCluster(BUILD) as cluster:
            for raw in ('{"patient":1,"patient":2}', '['*33+'0'+']'*33):
                with self.assertRaises(ValueError): rpc(cluster.runtime/'patient/service.sock', 'INIT5', raw)
            self.assertEqual(rpc(cluster.runtime/'patient/service.sock','PING'), ['OK'])
            self.assertEqual(rpc(cluster.runtime/'patient/service.sock','INIT',40000), ['OK'])

    def test_broker_bad_frames_do_not_change_draft_or_disclose_credentials(self):
        with Fixture() as f:
            before=f.call('DRAFT')
            for payload in ('{"revision":1,"revision":2}', '['*33+'0'+']'*33, 'NaN'):
                with self.subTest(payload=payload[:40]), socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as s:
                    s.connect(str(f.root/'api/broker.sock'))
                    s.sendall(('DX1 '+f.server.token+' VALIDATE '+payload.encode().hex()+'\n').encode())
                    reply=wire.line(s)
                    self.assertTrue(reply.startswith('DX1 ERROR '),reply)
                    self.assertNotIn(f.server.token,reply)
            self.assertEqual(f.call('DRAFT'),before)
            with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as s:
                s.connect(str(f.root/'api/broker.sock'))
                s.sendall(b'X'*(wire.MAX_FRAME+1))
                self.assertTrue(wire.line(s).startswith('DX1 ERROR 0 - unauthorized -1 0 '))
            self.assertEqual(f.call('DRAFT'),before)

    def test_broker_four_slow_clients_are_bounded_and_recover(self):
        with Fixture() as f:
            sockets=[]
            try:
                start=time.monotonic()
                for _ in range(4):
                    s=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);s.settimeout(3)
                    s.connect(str(f.root/'api/broker.sock'));s.sendall(b'D');sockets.append(s)
                time.sleep(.1)
                with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as extra:
                    extra.settimeout(.5);extra.connect(str(f.root/'api/broker.sock'))
                    try: self.assertEqual(extra.recv(1),b'')
                    except ConnectionResetError: pass
                # Trickle bytes cannot renew the original two-second deadline.
                time.sleep(.9)
                for s in sockets: s.sendall(b'X')
                for s in sockets:
                    reply=s.recv(4096)
                    self.assertTrue(reply.startswith(b'DX1 ERROR 0 - unauthorized'),reply)
                self.assertLess(time.monotonic()-start,3)
            finally:
                for s in sockets:s.close()
            self.assertEqual(f.call('STATUS')['state'],'idle')

    def test_partial_device_request_cannot_extend_plant_liveness(self):
        with LocalCluster(BUILD) as cluster:
            config=json.loads((ROOT/'scenarios/hd_nominal.json').read_text())
            config['ticks']=2
            records,manifest=simulate(config,cluster.runtime,BUILD)
            self.assertEqual(manifest['outcome'],'completed')
            self.assertGreater(state(rpc(cluster.runtime/'admin/plant.sock','STATUS'))['blood_mL_min'],0)
            started=time.monotonic()
            with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as slow:
                slow.connect(str(cluster.runtime/'device/control.sock'));slow.sendall(b'DL1 STATUS')
                time.sleep(.3);slow.sendall(b'5')
                slow.settimeout(1)
                self.assertEqual(slow.recv(100),b'DL1 ERR protocol\n')
            self.assertLess(time.monotonic()-started,1)
            # Do not issue heartbeat. Actual independent plant observation must
            # show liveness isolation without integrating additional virtual time.
            time.sleep(2.05)
            actual=state(rpc(cluster.runtime/'admin/plant.sock','STATUS'))
            self.assertTrue(actual['latched'] and actual['clamp_closed'])
            self.assertEqual(actual['reason'],'liveness')
            self.assertEqual((actual['blood_mL_min'],actual['uf_mL_min'],actual['time_ms']),(0,0,200))
            self.assertEqual(actual['removed_total_mL'],records[-1]['removed_total_mL'])

    def test_killed_broker_terminates_actual_children_preserves_unknown_stop(self):
        with tempfile.TemporaryDirectory(prefix='dl-m8-') as temporary:
            root=Path(temporary);runtime=None;pids=[]
            with (root/'broker.log').open('w') as log:
                process=subprocess.Popen([sys.executable,'-m','dialysislab.experiments','--build-dir',str(BUILD),
                    '--output',str(root/'runs'),'--api-dir',str(root/'api')],
                    env=dict(os.environ,PYTHONPATH=str(ROOT/'python')),stdout=log,stderr=log)
                try:
                    def ready():
                        try:return wire.request(root/'api','STATUS')
                        except (OSError,ValueError):return None
                    status=wait_for(ready)
                    run=wire.request(root/'api','START',dict(revision=status['revision'],request_id=uuid.uuid4().hex,wall_speed=1))['run_id']
                    wait_for(ready,lambda s:s and s['sequence']>=3)
                    for path in Path('/proc',str(process.pid),'task').glob('*/children'):
                        pids.extend(int(n) for n in path.read_text().split())
                    self.assertEqual(len(pids),4,pids)
                    command=Path('/proc',str(pids[0]),'cmdline').read_bytes().split(b'\0')
                    runtime=Path(os.fsdecode(command[command.index(b'--runtime-dir')+1]))
                    process.kill();process.wait(timeout=3)
                    def alive(pid):
                        try:return Path('/proc',str(pid),'stat').read_text().split(') ',1)[1][0]!='Z'
                        except FileNotFoundError:return False
                    wait_for(lambda:[pid for pid in pids if alive(pid)],lambda remaining:not remaining,timeout=3)
                    data=root/'runs'/run/'data';prefix=scan(data/'trajectory.jsonl',recover=True)
                    self.assertGreaterEqual(prefix['records'],4)
                    self.assertEqual(json.loads((data/'manifest.json').read_text())['outcome'],'running')
                    # Recovery reports interruption, never inferred observed zero.
                    from dialysislab.experiments import Broker
                    recovered=Broker(BUILD,root/'runs')
                    try:
                        self.assertEqual(recovered.history[run]['state'],'interrupted')
                        self.assertIsNone(recovered.history[run]['stop'])
                    finally:recovered.close()
                finally:
                    if process.poll() is None:process.kill();process.wait(timeout=3)
                    for pid in pids:
                        try:os.kill(pid,signal.SIGKILL)
                        except ProcessLookupError:pass
                    if runtime and runtime.name.startswith('dl-m1-'):shutil.rmtree(runtime,ignore_errors=True)


if __name__=='__main__':unittest.main()
