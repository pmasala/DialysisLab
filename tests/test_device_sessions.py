"""Actual service epoch binding; no mocked plant decisions."""
import os
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'python'))
from dialysislab.protocol import rpc
from dialysislab.runner import LocalCluster
from test_machine import DeviceFixture, BUILD


class DeviceSessionTests(unittest.TestCase):
    def test_device_roles_and_old_sessions_do_not_mutate_plant(self):
        with LocalCluster(BUILD) as cluster:
            f = DeviceFixture(cluster)
            f.step()
            for role in ('control', 'protection'):
                path = cluster.runtime / 'device' / (role + '.sock')
                session = rpc(path, 'HELLO6')[1]
                self.assertEqual(len(session), 32)
                self.assertEqual(rpc(path, 'STATUS6', session)[0:2], ['VIEW6', session])
                before = f.view()['machine']
                for command in [('STOP6',), ('REQUEST6', 'PRIME'), ('CONFIRM6', 1), ('ACK6',), ('SILENCE6', 60000), ('PRESCRIBE6', 0, 300, 5, 0)]:
                    self.assertEqual(rpc(path, command[0], '0' * 32, *command[1:]), ['REJECT', 'session'])
                self.assertEqual(before, f.view()['machine'])
                self.assertEqual(rpc(path, 'HALT'), ['REJECT', 'device_operation'])
                self.assertEqual(rpc(path, 'FAULT5', 'air', 1), ['REJECT', 'device_operation'])
            self.assertEqual(rpc(cluster.runtime / 'device/control.sock', 'HELLO6')[1], rpc(cluster.runtime / 'device/control.sock', 'HELLO6')[1])
            self.assertNotEqual(rpc(cluster.runtime / 'device/control.sock', 'HELLO6')[1], rpc(cluster.runtime / 'device/protection.sock', 'HELLO6')[1])

    def test_restart_reusing_intent_number_cannot_accept_old_confirmation(self):
        for role, action in [('control', 'PRIME'), ('protection', 'RESET')]:
            with self.subTest(role=role), LocalCluster(BUILD) as cluster:
                f = DeviceFixture(cluster)
                f.step()
                path = cluster.runtime / 'device' / (role + '.sock')
                old = rpc(path, 'HELLO6')[1]
                self.assertEqual(rpc(path, 'REQUEST6', old, action), ['CONFIRM5', '1'])
                # Graceful exit releases owned sockets. Crash recovery still requires explicit cleanup.
                cluster.processes[role].terminate(); cluster.processes[role].wait(timeout=3)
                cluster.processes[role] = subprocess.Popen([str(BUILD / role), '--runtime-dir', str(cluster.runtime)],
                    stdout=cluster.logs[0], stderr=cluster.logs[0])
                import time
                deadline = time.monotonic() + 3
                while True:
                    try: new = rpc(path, 'HELLO6')[1]; break
                    except OSError:
                        if time.monotonic() >= deadline: raise
                        time.sleep(.01)
                self.assertNotEqual(old, new)
                self.assertEqual(rpc(path, 'REQUEST6', new, action), ['CONFIRM5', '1'])
                self.assertEqual(rpc(path, 'CONFIRM6', old, 1), ['REJECT', 'session'])
                self.assertEqual(rpc(path, 'STATUS6', new)[-2:], ['confirmation', 'confirmation'])
                self.assertEqual(f.view()['machine']['revision'], 0)
                self.assertEqual(rpc(path, 'CONFIRM6', new, 1), ['QUEUED5', '1'])


class WallPacingTests(unittest.TestCase):
    def test_slow_wall_pacing_keeps_heartbeat_and_identical_virtual_records(self):
        import json
        import time
        from dialysislab.runner import simulate
        c = json.loads((ROOT / 'scenarios/machine_hd.json').read_text())
        c.update(ticks=3, workflow=[], faults=[])
        hashes = []
        for speed in (0, .08):
            with LocalCluster(BUILD) as cluster:
                started = time.monotonic()
                _, manifest = simulate(c, cluster.runtime, BUILD, wall_speed=speed)
                elapsed = time.monotonic() - started
            self.assertEqual(manifest['outcome'], 'completed', manifest['errors'])
            hashes.append(manifest['trajectory_sha256'])
            if speed: self.assertGreaterEqual(elapsed, 2.5)
        self.assertEqual(hashes[0], hashes[1])
