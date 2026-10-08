"""Real LVGL widget events against real services; explicitly selected GUI suite."""
import json
import os
from pathlib import Path
import queue
import socket
import subprocess
import sys
import tempfile
import threading
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'python'))
sys.path.insert(0, str(ROOT / 'tests'))
from dialysislab.runner import LocalCluster
from dialysislab.protocol import rpc, heartbeat, wait_ready
from dialysislab import treatment
from test_machine import DeviceFixture

BUILD = Path(os.environ.get('DIALYSISLAB_GUI_BUILD_DIR', ROOT / 'build/gui')).resolve()
EVIDENCE = Path(os.environ.get('DIALYSISLAB_UI_EVIDENCE', ROOT / 'build/m6-ui-diagnostic'))
GRAPHICAL = os.environ.get('DIALYSISLAB_UI_GRAPHICAL') == '1'


class UserInterface:
    def __init__(self, runtime, name, argv=None):
        self.directory = EVIDENCE / name
        self.directory.mkdir(parents=True, exist_ok=False)
        self.error = (self.directory / 'stderr.txt').open('w')
        self.transcript = (self.directory / 'events.jsonl').open('w')
        self.lines = queue.Queue()
        self.argv = [str(BUILD / 'device-ui'), '--runtime-dir', str(runtime), '--test-input',
                     '--capture-dir', str(self.directory)] + ([] if GRAPHICAL else ['--headless'])
        if argv is not None: self.argv = argv
        self.process = subprocess.Popen(self.argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                        stderr=self.error, text=True, bufsize=1)
        def collect():
            for line in self.process.stdout:
                self.transcript.write(line); self.transcript.flush(); self.lines.put(line)
        self.thread = threading.Thread(target=collect, daemon=True); self.thread.start()
        self.serial = 0

    def send(self, text):
        self.process.stdin.write(text + '\n'); self.process.stdin.flush()

    def snapshot(self, capture=None):
        self.serial += 1
        name = capture or ('request_' + str(self.serial))
        self.send(('CAPTURE ' if capture else 'SNAPSHOT ') + name)
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline:
            if self.process.poll() is not None: raise AssertionError('UI exited: ' + (self.directory / 'stderr.txt').read_text())
            line = self.lines.get(timeout=max(.01, deadline - time.monotonic()))
            if line.startswith('DLUI1 '):
                result = json.loads(line[6:])
                if result['tag'] == name: return result
        raise AssertionError('UI report timeout')

    def until(self, predicate, fixture, stepping=True, timeout=3):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if stepping: fixture.step()
            else: heartbeat(fixture.root)
            value = self.snapshot()
            if predicate(value): return value
            time.sleep(.04)
        raise AssertionError('UI condition timeout: ' + json.dumps(value))

    def click(self, action, fixture, confirm=True):
        self.send('CLICK ' + action)
        if action not in ('STOP', 'ACK'):
            self.until(lambda s: s['pending'], fixture, stepping=False)
            if confirm: self.send('CLICK CONFIRM')

    def close(self):
        if self.process.poll() is None:
            self.send('QUIT now')
            try: self.process.wait(timeout=5)
            except subprocess.TimeoutExpired: self.process.kill(); self.process.wait(); raise
        self.thread.join(timeout=2)
        self.process.stdin.close(); self.process.stdout.close(); self.error.close(); self.transcript.close()
        if self.process.returncode != 0: raise AssertionError('UI exit ' + str(self.process.returncode))


class DroppedReplyProxy:
    """Forwards real frames then drops selected replies after actual service acceptance."""
    def __init__(self, source, target):
        self.source, self.target = source, target
        self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.socket.bind(str(source)); self.socket.listen(8); self.socket.settimeout(.05)
        self.stop = False; self.drop = set(); self.calls = []; self.errors = []
        def serve():
            while not self.stop:
                try: connection, _ = self.socket.accept()
                except socket.timeout: continue
                except OSError: break
                with connection:
                    try:
                        connection.settimeout(1)
                        frame = b''
                        while not frame.endswith(b'\n'):
                            part = connection.recv(1)
                            if not part: raise OSError('closed request')
                            frame += part
                            if len(frame) > 4096: raise ValueError('oversize')
                        tokens = frame.decode().split(); self.calls.append(tokens[1:])
                        response = rpc(target, *tokens[1:])
                        if tokens[1] in self.drop: self.drop.remove(tokens[1]); continue
                        connection.sendall(('DL1 ' + ' '.join(response) + '\n').encode())
                    except (OSError, ValueError) as exc: self.errors.append(str(exc))
        self.thread = threading.Thread(target=serve, daemon=True); self.thread.start()

    def close(self):
        self.stop = True; self.thread.join(timeout=2); self.socket.close()


class DeviceUiTests(unittest.TestCase):
    def launch(self, cluster, name):
        ui = UserInterface(cluster.runtime, name)
        self.addCleanup(ui.close)
        return ui

    def ready(self, ui, f):
        for _ in range(4): f.step()
        return ui.until(lambda s: s['control'] == s['protection'] == 'LIVE', f)

    def test_real_widgets_prescription_confirm_and_treatment_all_modes(self):
        for mode in range(3):
            with self.subTest(mode=mode), LocalCluster(BUILD) as cluster:
                f = DeviceFixture(cluster)
                ui = self.launch(cluster, 'mode_' + str(mode))
                self.ready(ui, f)
                ui.click('PRIME', f)
                ui.until(lambda s: s.get('stage') == 'PRIMING', f)
                for _ in range(90): f.step()
                ui.click('CONFIGURE', f)
                ui.until(lambda s: s.get('stage') == 'CONFIGURATION', f)
                # Initial fixture is HDF post; select requested actual widget mode.
                for _ in range((mode - 2) % 3): ui.send('CLICK MODE')
                ui.send('SET blood 501')
                ui.send('CLICK PRESCRIBE')
                invalid = ui.until(lambda s: s['feedback'].startswith('Invalid'), f, stepping=False)
                self.assertFalse(invalid['pending']); self.assertEqual(f.view()['machine']['blood_prescribed_mL_min'], 300)
                ui.send('SET blood 280'); ui.send('SET uf 4'); ui.send('SET sub ' + ('0' if mode == 0 else '60'))
                ui.click('PRESCRIBE', f, confirm=False)
                self.assertEqual(f.view()['machine']['blood_prescribed_mL_min'], 300)
                ui.send('CLICK CANCEL')
                self.assertEqual(f.view()['machine']['blood_prescribed_mL_min'], 300)
                ui.click('PRESCRIBE', f)
                ui.until(lambda s: s.get('prescribed_blood_mL_min') == 280 and s.get('mode') == mode, f)
                self.assertEqual(f.view()['machine']['mode'], ('HD', 'HDF_PRE', 'HDF_POST')[mode])
                ui.click('START', f)
                ui.until(lambda s: s.get('stage') == 'TREATMENT' and s.get('blood_mL_min', 0) > 0, f)
                ui.until(lambda s: s.get('sequence') == f.n - 1, f, stepping=False)
                actual = ui.snapshot('treatment')
                view = f.view()
                self.assertEqual(actual['mode'], mode)
                self.assertGreater(actual['trend_count'], 0)
                self.assertIn('mL/min', actual['labels']['observed'])
                self.assertAlmostEqual(actual['blood_mL_min'], view['observation']['blood_mL_min'], places=2)
                ui.click('STOP', f)
                stopped = ui.until(lambda s: s.get('stage') == 'STOPPED', f, stepping=False)
                self.assertGreater(stopped['blood_mL_min'], 0)  # frozen sample is not replaced with a commanded zero
                state = treatment.live(rpc(f.admin, 'STATUS4'))
                self.assertEqual(state['blood_mL_min'], 0)
                ui.until(lambda s: s.get('blood_mL_min') == 0, f)
                ui.snapshot('stopped')
                ui.close(); self._cleanups.pop()

    def test_alarm_ack_silence_stop_and_guarded_recovery(self):
        with LocalCluster(BUILD) as cluster:
            f = DeviceFixture(cluster); f.treat()
            ui = self.launch(cluster, 'alarms'); self.ready(ui, f)
            rpc(f.admin, 'FAULT5', 'air', 1)
            alarm = ui.until(lambda s: bool(s['mask'] & 4), f)
            self.assertIn('HIGH', alarm['labels']['alarm'])
            ui.click('ACK', f)
            ui.until(lambda s: bool(s.get('acknowledged_mask', 0) & 4), f)
            ui.click('SILENCE', f)
            silenced = ui.until(lambda s: s.get('silence_until_ms', 0) > 0, f)
            self.assertTrue(silenced['mask'] & 4)
            ui.click('RESET', f)
            ui.until(lambda s: 'unsafe_reset' in s['labels']['intent'], f)
            self.assertTrue(f.view()['machine']['alarm_mask'] & 4)
            ui.snapshot('air_alarm')
            ui.click('STOP', f); ui.until(lambda s: s.get('stage') == 'STOPPED', f)
            rpc(f.admin, 'FAULT5', 'air', 0)
            ui.click('RECOVER', f); ui.until(lambda s: s.get('stage') == 'RECOVERY', f)
            for _ in range(4): f.step()
            ui.click('RESET', f)
            recovered = ui.until(lambda s: s.get('stage') == 'PAUSED' and s['mask'] == 0, f)
            self.assertEqual(recovered['blood_mL_min'], 0)
            ui.snapshot('recovered')

    def test_stale_disconnected_reconnect_cancels_confirmation(self):
        with LocalCluster(BUILD) as cluster:
            f = DeviceFixture(cluster); f.treat()
            ui = self.launch(cluster, 'connection'); self.ready(ui, f)
            stale = ui.until(lambda s: s['control'] == s['protection'] == 'STALE', f, stepping=False, timeout=2.2)
            self.assertGreater(stale['blood_mL_min'], 0)
            self.assertIn('[STALE]', stale['labels']['observed'])
            ui.snapshot('stale')
            self.ready(ui, f)
            ui.click('PAUSE', f, confirm=False)
            old_session = rpc(f.root / 'device/control.sock', 'HELLO6')[1]
            cluster.processes['control'].terminate(); cluster.processes['control'].wait(timeout=3)
            started = time.monotonic()
            # Heartbeat the still-live roles, without requiring the lost control service.
            while time.monotonic() - started < 2:
                rpc(f.admin, 'PING'); rpc(f.root / 'protection/service.sock', 'PING')
                disconnected = ui.snapshot()
                if disconnected['control'] == 'DISCONNECTED': break
                time.sleep(.03)
            self.assertEqual(disconnected['control'], 'DISCONNECTED')
            self.assertFalse(disconnected['pending'])
            ui.snapshot('disconnected')
            cluster.processes['control'] = subprocess.Popen([str(BUILD / 'control'), '--runtime-dir', str(f.root)],
                stdout=cluster.logs[0], stderr=cluster.logs[0])
            wait_ready(f.root)
            connected = ui.until(lambda s: s['control'] in ('LIVE', 'STALE'), f, stepping=False)
            self.assertFalse(connected['pending'])
            self.assertNotEqual(old_session, rpc(f.root / 'device/control.sock', 'HELLO6')[1])
            self.assertEqual(f.view()['machine']['stage'], 'TREATMENT')  # no old PAUSE retry
            ui.snapshot('reconnected')


    def test_lost_confirm_and_stop_replies_preserve_intent_and_actual_plant_state(self):
        with LocalCluster(BUILD) as cluster, tempfile.TemporaryDirectory(prefix='dl-ui-proxy-') as temporary:
            f = DeviceFixture(cluster)
            root = Path(temporary); (root / 'device').mkdir()
            (root / 'device/protection.sock').symlink_to(f.root / 'device/protection.sock')
            proxy = DroppedReplyProxy(root / 'device/control.sock', f.root / 'device/control.sock')
            self.addCleanup(proxy.close)
            ui = UserInterface(root, 'lost_replies'); self.addCleanup(ui.close)
            self.ready(ui, f)
            proxy.drop.add('CONFIRM6')
            ui.click('PRIME', f)
            ambiguous = ui.until(lambda s: s['result'] == 'unconfirmed_no_retry' and s.get('stage') == 'PRIMING', f)
            self.assertEqual(sum(c[0] == 'CONFIRM6' for c in proxy.calls), 1)
            self.assertEqual(f.view()['intent']['result'], 'applied')
            for _ in range(4): f.step()
            ui.until(lambda s: s.get('sequence') == f.n - 1 and s.get('blood_mL_min', 0) > 0, f, stepping=False)
            proxy.drop.add('STOP6')
            ui.click('STOP', f)
            stopped = ui.until(lambda s: s['command'] == 'STOP' and s['result'] == 'unconfirmed_no_retry' and s.get('stage') == 'STOPPED', f, stepping=False)
            self.assertGreater(stopped['blood_mL_min'], 0)  # observation predates actual STOP
            actual = treatment.live(rpc(f.admin, 'STATUS4'))
            self.assertEqual(actual['blood_mL_min'], 0)
            self.assertEqual(sum(c[0] == 'STOP6' for c in proxy.calls), 1)
            ui.snapshot('stop_reply_lost')
            self.assertFalse(proxy.errors)
            ui.close(); self._cleanups.pop()
            proxy.close(); self._cleanups.pop()

    def test_invalid_sensor_is_not_a_live_zero_and_new_samples_restore_validity(self):
        with LocalCluster(BUILD) as cluster:
            f = DeviceFixture(cluster); f.treat()
            ui = self.launch(cluster, 'invalid'); self.ready(ui, f)
            rpc(f.admin, 'PREPARE', f.n, f.n * 100, 100, .5, 'invalid', 'invalid')
            rpc(f.root / 'control/service.sock', 'STEP5', f.n, f.n * 100)
            rpc(f.root / 'protection/service.sock', 'STEP5', f.n, f.n * 100)
            rpc(f.admin, 'COMMIT5', f.n, f.n * 100); f.n += 1
            invalid = ui.until(lambda s: s['control'] == s['protection'] == 'INVALID', f, stepping=False)
            self.assertIn('unavailable', invalid['labels']['observed'])
            self.assertNotIn('Blood 0.0', invalid['labels']['observed'])
            self.assertTrue(invalid['mask'] & 16)
            ui.snapshot('invalid_sensor')
            self.ready(ui, f)
            self.assertTrue(f.view()['machine']['alarm_mask'] & 16)  # valid sample does not reset latch
