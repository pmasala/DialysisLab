"""Synthetic M1 acceptance: independent oracles and actual process boundaries."""
import copy
from decimal import Decimal
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'python'))
from dialysislab.patient import Patient
from dialysislab.protocol import ProtocolError, expect, pause, rpc, state
from dialysislab.runner import LocalCluster, canonical, simulate, validate

BUILD = Path(os.environ.get('DIALYSISLAB_BUILD_DIR', ROOT / 'build'))
CONFIG = json.loads((ROOT / 'scenarios/hd_nominal.json').read_text())
OCCLUSION = json.loads((ROOT / 'scenarios/hd_occlusion.json').read_text())


class M1Configuration(unittest.TestCase):
    def test_reject_configuration_before_execution(self):
        for key, value in [('dt_ms', 0), ('ticks', True), ('seed', -1), ('blood_mL_min', float('nan')),
                           ('uf_mL_min', 21), ('model', 'unknown'), ('patient_volume_mL', 0)]:
            with self.subTest(key=key):
                config = copy.deepcopy(CONFIG)
                config[key] = value
                with self.assertRaises(ValueError):
                    validate(config)
        config = copy.deepcopy(CONFIG)
        config['faults'] = [{'tick': 5, 'target': 'resistance', 'value': 4}] * 2
        with self.assertRaises(ValueError):
            validate(config)

    def test_patient_sequence_and_conservation_long_run(self):
        patient = Patient()
        patient.handle(['INIT', '40000'])
        with self.assertRaises(ProtocolError):
            patient.handle(['INIT', '40000'])
        for n in range(100000):
            patient.handle(['ADVANCE', str(n), str(n * 1000), '1000', '0.33333333333333331'])
        expected = Decimal(40000) - Decimal(100000) / 3
        self.assertLess(abs(patient.volume - expected), Decimal('1e-8'))
        for invalid in (['ADVANCE', '99999', '99999000', '1000', '0.1'],
                        ['ADVANCE', '100000', '100000000', '1000', '-1'],
                        ['ADVANCE', '100000', '100000000', '1000', 'nan']):
            with self.assertRaises(ValueError):
                patient.handle(invalid)


class M1Processes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        missing = [role for role in ('plant', 'control', 'protection', 'build_identity.json')
                   if not (BUILD / role).is_file()]
        if missing:
            raise RuntimeError('Build M1 first: cmake -S . -B build && cmake --build build; missing ' + str(missing))

    def run_scenario(self, config, before_tick=None):
        with LocalCluster(BUILD) as cluster:
            records, manifest = simulate(config, cluster.runtime, BUILD,
                                         before_tick=(lambda n: before_tick(cluster, n)) if before_tick else None)
        return records, manifest

    def assert_balance(self, records, config, active_ticks, rate=None):
        # Analytic oracle from input settings and predeclared active interval count.
        # Deliberately does not use measured UF or the plant/patient cumulative totals.
        rate = config['uf_mL_min'] if rate is None else rate
        expected = Decimal(str(rate)) * Decimal(active_ticks) * Decimal(config['dt_ms']) / Decimal(60000)
        initial = Decimal(str(config['patient_volume_mL']))
        last = records[-1]
        for actual in (last['removed_total_mL'], last['patient_removed_mL'],
                       config['patient_volume_mL'] - last['patient_volume_mL']):
            self.assertLess(abs(Decimal(str(actual)) - expected), Decimal('1e-8'))
        self.assertLess(abs(Decimal(str(last['patient_volume_mL'])) + expected - initial), Decimal('1e-8'))

    def test_nominal_conservation_and_build_identity(self):
        records, manifest = self.run_scenario(CONFIG)
        self.assertEqual(manifest['outcome'], 'completed')
        self.assertEqual(len(records), CONFIG['ticks'])
        self.assert_balance(records, CONFIG, 20)
        self.assertTrue(all(r['blood_mL_min'] == 300 and r['pressure_mmHg'] == 150 for r in records))
        self.assertTrue(all(not r['latched'] for r in records))
        self.assertEqual(set(manifest['build']['binary_sha256']), {'plant', 'control', 'protection'})
        self.assertEqual(manifest['configuration'], CONFIG)
        self.assertEqual(manifest['model'], 'm1-hd-1')

    def test_same_seed_exact_replay(self):
        a, ma = self.run_scenario(OCCLUSION)
        b, mb = self.run_scenario(OCCLUSION)
        self.assertEqual(list(a), list(b))  # Small 20-tick fixtures only.
        self.assertEqual(ma['configuration_sha256'], mb['configuration_sha256'])
        self.assertEqual(ma['trajectory_sha256'], mb['trajectory_sha256'])

    def test_zero_and_partial_flow_independent_balance(self):
        for blood, uf, expected_rate in [(300, 0, 0), (0, 10, 0), (0.1, 10, 0.1)]:
            with self.subTest(blood=blood, uf=uf):
                config = dict(CONFIG, blood_mL_min=blood, uf_mL_min=uf)
                records, manifest = self.run_scenario(config)
                self.assertEqual(manifest['outcome'], 'completed')
                self.assert_balance(records, config, 20, expected_rate)

    def test_occlusion_bound_and_persistent_conflicting_commands(self):
        records, manifest = self.run_scenario(OCCLUSION)
        self.assertEqual(manifest['outcome'], 'completed')
        self.assert_balance(records, OCCLUSION, 5)
        fault = records[5]
        self.assertEqual(fault['observations']['protection']['pressure_mmHg'], 600)
        self.assertEqual(fault['observations']['protection']['blood_mL_min'], 150)
        self.assertLessEqual(fault['time_ms'] - 500, 100)
        self.assertEqual(fault['protection_decision'], 'pressure')
        # Control continues demanding 300/10; protection subsequently permits a
        # now-zero measurement. Neither operation may reset plant's first latch.
        self.assertEqual(records[6]['protection_decision'], 'none')
        for record in records[5:]:
            self.assertEqual(record['reason'], 'pressure')
            self.assertTrue(record['latched'] and record['clamp_closed'])
            self.assertEqual((record['blood_mL_min'], record['uf_mL_min']), (0, 0))

    def test_measurement_invalidity_bound(self):
        for fault in ('invalid', 'missing', 'stale', 'future', 'replay'):
            with self.subTest(fault=fault):
                config = copy.deepcopy(CONFIG)
                config['faults'] = [dict(tick=5, target='protection_sensor', value=fault)]
                records, manifest = self.run_scenario(config)
                self.assertEqual(manifest['outcome'], 'completed')
                self.assertEqual(records[5]['reason'], 'measurement')
                self.assertLessEqual(records[5]['time_ms'] - 500, 100)
                self.assert_balance(records, config, 5)

    def test_control_sensor_fault_is_separate(self):
        config = copy.deepcopy(CONFIG)
        config['faults'] = [dict(tick=5, target='control_sensor', value='missing')]
        records, manifest = self.run_scenario(config)
        self.assertEqual(manifest['outcome'], 'completed')
        self.assertEqual(records[5]['observations']['protection']['valid'], 1)
        self.assertEqual(records[5]['observations']['control']['valid'], 0)
        self.assertEqual(records[5]['protection_decision'], 'none')
        self.assertEqual(records[5]['blood_mL_min'], 0)
        self.assertFalse(records[5]['latched'])
        self.assert_balance(records, config, 5)

    def test_protection_acts_when_control_is_killed(self):
        records, manifest = self.run_scenario(OCCLUSION, lambda c, n: c.kill('control') if n == 5 else None)
        self.assertEqual(manifest['outcome'], 'aborted')
        self.assertEqual(manifest['stop']['observed_state']['reason'], 'pressure')
        self.assertTrue(manifest['stop']['outputs_zero_observed'])
        self.assertEqual(manifest['aborted_tick']['protection_decision'], 'pressure')
        self.assert_balance(records, OCCLUSION, 5)

    def test_missing_control_or_protection_blocks_commit(self):
        for role in ('control', 'protection'):
            with self.subTest(role=role):
                records, manifest = self.run_scenario(CONFIG, lambda c, n: c.kill(role) if n == 5 else None)
                self.assertEqual(manifest['outcome'], 'aborted')
                self.assertEqual(len(records), 5)
                self.assertIn(role + ':', manifest['rpc_failures'][0])
                self.assertTrue(manifest['stop']['outputs_zero_observed'])
                self.assertEqual(manifest['stop']['observed_state']['time_ms'], 500)

    def test_plant_or_patient_loss_aborts_uncommitted_record(self):
        for role in ('plant', 'patient'):
            with self.subTest(role=role):
                records, manifest = self.run_scenario(CONFIG, lambda c, n: c.kill(role) if n == 5 else None)
                self.assertEqual(manifest['outcome'], 'aborted')
                self.assertEqual(len(records), 5)
                self.assertTrue(manifest['errors'])

    def test_virtual_pause_maintains_liveness_without_integrating(self):
        def pause_at_five(cluster, n):
            if n == 5:
                before = state(rpc(cluster.runtime / 'admin/plant.sock', 'STATUS'))
                pause(cluster.runtime, 2.3)
                after = state(rpc(cluster.runtime / 'admin/plant.sock', 'STATUS'))
                self.assertEqual(before, after)
        a, manifest = self.run_scenario(CONFIG, pause_at_five)
        b, _ = self.run_scenario(CONFIG)
        self.assertEqual(manifest['outcome'], 'completed')
        self.assertEqual(list(a), list(b))

    def test_runner_loss_wall_watchdog_does_not_advance_clock(self):
        with LocalCluster(BUILD) as cluster:
            self.manual_tick(cluster, 0)
            # A real scheduler subprocess supplies pause heartbeats, then is killed.
            child = subprocess.Popen([sys.executable, '-c',
                'from dialysislab.protocol import pause; import sys; pause(sys.argv[1], 30)',
                str(cluster.runtime)], env=dict(os.environ, PYTHONPATH=str(ROOT / 'python')))
            try:
                time.sleep(0.15)
                self.assertIsNone(child.poll())
                child.kill()
                child.wait(timeout=2)
            finally:
                if child.poll() is None:
                    child.kill()
                    child.wait(timeout=2)
            before = state(rpc(cluster.runtime / 'admin/plant.sock', 'STATUS'))
            start = time.monotonic()
            time.sleep(2.15)
            after = state(rpc(cluster.runtime / 'admin/plant.sock', 'STATUS'))
            self.assertLess(time.monotonic() - start, 3)
            self.assertEqual(after['reason'], 'liveness')
            self.assertEqual(after['blood_mL_min'], 0)
            self.assertEqual(after['time_ms'], before['time_ms'])
            self.assertEqual(after['removed_total_mL'], before['removed_total_mL'])

    @staticmethod
    def manual_tick(cluster, n):
        runtime = cluster.runtime
        expect(rpc(runtime / 'admin/plant.sock', 'PREPARE', n, 100*n, 100, 0.5, 'none', 'none'), 'OK', 1)
        expect(rpc(runtime / 'control/service.sock', 'STEP', n, 100*n, 300, 10), 'OK', 1)
        expect(rpc(runtime / 'protection/service.sock', 'STEP', n, 100*n, 250), 'DECISION', 2)
        return state(rpc(runtime / 'admin/plant.sock', 'COMMIT', n, 100*n))

    def test_role_authority_and_duplicate_tick_rejection(self):
        with LocalCluster(BUILD) as cluster:
            self.manual_tick(cluster, 0)
            with self.assertRaises(ProtocolError):
                rpc(cluster.runtime / 'control/plant.sock', 'PERMIT', 0, 0)
            self.assertEqual(state(rpc(cluster.runtime / 'admin/plant.sock', 'STATUS'))['reason'], 'protocol')
        with LocalCluster(BUILD) as cluster:
            self.manual_tick(cluster, 0)
            with self.assertRaises(ProtocolError):
                rpc(cluster.runtime / 'admin/plant.sock', 'COMMIT', 0, 0)
            self.assertEqual(state(rpc(cluster.runtime / 'admin/plant.sock', 'STATUS'))['time_ms'], 100)

    def test_malformed_frames_fail_closed(self):
        for message in ('DL2 PING\n', 'DL1 PING extra\n', 'DL1 PREPARE 0 0 100 nan none none\n',
                        'DL1 ' + 'X'*4096 + '\n'):
            with self.subTest(message=message[:30]), LocalCluster(BUILD) as cluster:
                with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
                    connection.settimeout(1)
                    connection.connect(str(cluster.runtime / 'admin/plant.sock'))
                    connection.sendall(message.encode())
                    self.assertTrue(connection.recv(100).startswith(b'DL1 ERR'))
                self.assertEqual(state(rpc(cluster.runtime / 'admin/plant.sock', 'STATUS'))['reason'], 'protocol')


if __name__ == '__main__':
    unittest.main()
