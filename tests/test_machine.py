"""M5 real-process lifecycle, isolation, differentiated protection and recovery."""
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'python'))
sys.path.insert(0, str(ROOT / 'tools'))
from dialysislab import circuit, treatment, machine
from dialysislab.compartments import Compartments
from dialysislab.protocol import rpc, expect, pause, ProtocolError
from dialysislab.runner import LocalCluster, simulate, validate
import dialysislab.runner as runner
import verify_models

BUILD = Path(os.environ.get('DIALYSISLAB_BUILD_DIR', ROOT / 'build'))


def config(name='hdf_post'):
    return json.loads((ROOT / ('scenarios/machine_' + name + '.json')).read_text())


class DeviceFixture:
    def __init__(self, cluster):
        self.root = cluster.runtime
        self.admin = self.root / 'admin/plant.sock'
        self.control = self.root / 'control/plant.sock'
        self.protection = self.root / 'protection/plant.sock'
        self.n = 0
        self.c = config()
        circuit.configure(self.admin, self.c); treatment.configure(self.admin, self.c); machine.configure(self.admin, self.c)

    def prepare(self):
        expect(rpc(self.admin, 'PREPARE', self.n, self.n * 100, 100, .5, 'none', 'none'), 'OK', 1)

    def step(self, action=None, values=None):
        if action: machine.request(self.root, dict(action=action, values=values or []))
        self.prepare()
        expect(rpc(self.root / 'control/service.sock', 'STEP5', self.n, self.n * 100), 'OK', 1)
        expect(rpc(self.root / 'protection/service.sock', 'STEP5', self.n, self.n * 100), 'DECISION', 2)
        result = machine.committed(rpc(self.admin, 'COMMIT5', self.n, self.n * 100))
        self.n += 1
        return result

    def treat(self):
        for _ in range(4): self.step()
        self.step('PRIME')
        for _ in range(85): self.step()
        self.step('CONFIGURE')
        self.step('START')
        for _ in range(4): self.step()

    def view(self, role='control'):
        return machine.view(rpc(self.root / 'device' / (role + '.sock'), 'STATUS5'))


class MachineTests(unittest.TestCase):
    def test_real_transport_accepts_representable_subnormal_concentrations(self):
        c = json.loads((ROOT / 'scenarios/patient_baseline.json').read_text())
        c['ticks'] = 10
        c['transport']['blood_mmol_L'][0] = 2.110269719209234e-308
        c['patient']['concentration_mmol_L'][0][0] = c['transport']['blood_mmol_L'][0]
        c['patient']['concentration_mmol_L'][1][0] = c['transport']['blood_mmol_L'][0]
        c['patient']['generation_mmol_min'][0] = 0
        with LocalCluster(BUILD) as cluster:
            records, manifest = simulate(c, cluster.runtime, BUILD)
        self.assertEqual(manifest['outcome'], 'completed', manifest['errors'])
        self.assertGreater(records[0]['circuit']['boundary_diffusion_mmol_min'][0], 0)
        # Supported subnormals are distinct from unrepresentable numeric input.
        for token in ('1e999', '1e-999', '0x1p-2', 'nan'):
            with self.subTest(token=token), LocalCluster(BUILD) as cluster:
                with self.assertRaises(ProtocolError):
                    rpc(cluster.runtime / 'admin/plant.sock', 'PREPARE', 0, 0, 100, token, 'none', 'none')

    def test_isolated_100000_tick_flush_keeps_body_ceiling_and_conserves_mass(self):
        c = config()['patient']; c.update(volume_mL=[35000, 65000], initial_weight_kg=150)
        patient = Compartments(c, online=True, lifecycle=True)
        pressure = 0.0; dt = 1 / 60
        source = [0., 140., 4., 105., 24., 2.4]
        for n in range(100000):
            # Independent one-node implicit RC/pump equation, not the plant solver.
            pressure = (.001 / dt * pressure + 300) / (.001 / dt + 1 + .5)
            draw, returned = (300 - .5 * pressure) * dt, pressure * dt
            result = patient.advance(dict(sequence=n, time_ms=n * 1000, dt_ms=1000, draw_mL=0,
                return_mL=0, uf_mL=0, stored_mL=.001 * pressure, clearance_mL_min=[0.] * 6,
                sieving=[1.] * 6, dialysate_mmol_L=source, pre_mL=0, post_mL=0,
                substitution_mmol_L=source, flush_in_mL=draw, flush_out_mL=returned, flush_mmol_L=source))
            self.assertEqual(sum(result['volume_mL'][:2]), 100000)
        self.assertGreater(result['flush_in_mL'], 333000)
        self.assertAlmostEqual(sum(result['volume_mL']), 100020 + result['flush_in_mL'] - result['flush_out_mL'], delta=1e-6)
        self.assertLess(max(map(abs, result['mass_residual_mmol'])), 1e-6)

    def test_evidence_cross_checks_alarm_mask_latches_and_every_actuator_class(self):
        with tempfile.TemporaryDirectory() as tmp, LocalCluster(BUILD) as cluster:
            directory = Path(tmp) / 'run'; c = config('hd'); records, manifest = simulate(c, cluster.runtime, BUILD, directory)
            self.assertEqual(manifest['outcome'], 'completed', manifest['errors']); original = list(records)
            # Rehash each forgery: evidence integrity alone is not semantic validity.
            for kind in ('air', 'fluid', 'flush', 'mask_removed', 'latch', 'clamp', 'alarm_names'):
                records = copy.deepcopy(original); r = records[110 if kind != 'flush' else 10]
                if kind in ('air', 'fluid', 'flush'):
                    r['machine']['alarm_mask'] = 4 if kind == 'air' else 256
                    r['machine']['alarms'] = ['air' if kind == 'air' else 'integrity']
                elif kind == 'mask_removed':
                    r['online']['quality_latched'] = True
                elif kind == 'latch': r['latched'] = True
                elif kind == 'clamp': r['clamp_closed'] = True
                else: r['machine']['alarms'] = ['air']
                data = ''.join(json.dumps(r, sort_keys=True, separators=(',', ':')) + '\n' for r in records).encode()
                (directory / 'trajectory.jsonl').write_bytes(data)
                manifest['trajectory_sha256'] = hashlib.sha256(data).hexdigest()
                (directory / 'manifest.json').write_text(json.dumps(manifest))
                with self.subTest(kind=kind), self.assertRaises(ValueError):
                    verify_models.verify(directory, c, manifest['build']['source_sha256'])

    def test_quality_detectors_trip_in_their_first_unsafe_observation_cycle(self):
        for name, value, hazard in [('temperature', 90, 'temperature'), ('ratio', .08, 'composition'),
                                    ('filter1', 100, 'filter_pressure'), ('route', 1, 'route'), ('supply', 0, 'supply')]:
            c = config('quality'); c['faults'][0].update(target='online:' + name, value=value)
            with self.subTest(name=name), LocalCluster(BUILD) as cluster:
                records, manifest = simulate(c, cluster.runtime, BUILD)
                self.assertEqual(manifest['outcome'], 'completed', manifest['errors'])
                def unsafe(o):
                    return {'temperature': o['temperature_C'] > 39, 'composition': o['conductivity_mS_cm'] > 16,
                            'filter_pressure': o['filter_pressure_mmHg'] > 300, 'route': o['route'] != 2,
                            'supply': o['supply_ready'] == 0}[hazard]
                measured = next(r for r in records if unsafe(r['observations']['protection']))
                latched = next(r for r in records if hazard in r['machine']['alarms'])
                self.assertEqual(measured['sequence'], latched['sequence'])
                self.assertEqual(latched['time_ms'] - measured['observations']['protection']['time_ms'], 100)
                self.assertGreater(latched['blood_mL_min'], 0); self.assertEqual(latched['uf_mL_min'], 0)

    def test_flush_quality_stops_external_pump_and_missing_decision_is_terminal(self):
        with LocalCluster(BUILD) as cluster:
            f = DeviceFixture(cluster)
            for _ in range(4): f.step()
            f.step('PRIME'); self.assertGreater(treatment.live(rpc(f.admin, 'STATUS4'))['blood_mL_min'], 0)
            rpc(f.admin, 'FAULT4', 'integrity', 0)
            f.prepare(); rpc(cluster.runtime / 'protection/service.sock', 'STEP5', f.n, f.n * 100)
            self.assertEqual(treatment.live(rpc(f.admin, 'STATUS4'))['blood_mL_min'], 0)
            rpc(f.control, 'DEMAND5', f.n, f.n * 100, 300, 140, 120)
            result = machine.committed(rpc(f.admin, 'COMMIT5', f.n, f.n * 100))
            self.assertEqual(result['machine']['flush_in_tick_mL'], 0)
        for missing in ('control', 'protection'):
            with self.subTest(missing=missing), LocalCluster(BUILD) as cluster:
                f = DeviceFixture(cluster); f.treat(); f.prepare()
                if missing == 'control': rpc(cluster.runtime / 'protection/service.sock', 'STEP5', f.n, f.n * 100)
                else: rpc(f.control, 'DEMAND5', f.n, f.n * 100, 300, 140, 120)
                with self.assertRaises(ProtocolError): rpc(f.admin, 'COMMIT5', f.n, f.n * 100)
                self.assertTrue(f.view()['machine']['terminal'])
                self.assertEqual(treatment.live(rpc(f.admin, 'STATUS4'))['blood_mL_min'], 0)

    def test_confirmation_expires_in_wall_time_without_advancing_physics(self):
        with LocalCluster(BUILD) as cluster:
            f = DeviceFixture(cluster); path = cluster.runtime / 'device/control.sock'
            token = rpc(path, 'REQUEST5', 'PRIME')[1]
            pause(cluster.runtime, 10.1)
            self.assertEqual(rpc(path, 'CONFIRM5', token), ['REJECT', 'confirmation'])
            view = f.view(); self.assertEqual(view['machine']['time_ms'], 0)
            self.assertEqual(view['machine']['stage'], 'PREPARATION')
            self.assertEqual(view['intent']['result'], 'expired')

    def test_hd_pre_post_lifecycle_flush_and_independent_balances(self):
        for name in ('hd', 'hdf_pre', 'hdf_post', 'recovery'):
            c = config(name)
            with self.subTest(name=name), tempfile.TemporaryDirectory() as tmp, LocalCluster(BUILD) as cluster:
                records, manifest = simulate(c, cluster.runtime, BUILD, Path(tmp) / 'run')
                self.assertEqual(manifest['outcome'], 'completed', manifest['errors'])
                verified = verify_models.verify(Path(tmp) / 'run', c, manifest['build']['source_sha256'])
                self.assertLess(verified['maximum_water_error_mL'], 1e-6)
                self.assertLess(verified['maximum_mass_error_mmol'], 1e-6)
                stages = {r['machine']['stage'] for r in records}
                self.assertEqual(stages, set(machine.STAGES))
                self.assertEqual(records[-1]['machine']['stage'], 'CLEANED')
                self.assertGreater(records[-1]['patient']['flush_in_mL'], 40)
                for r in records:
                    if r['machine']['stage'] in ('PREPARATION', 'PRIMING', 'CONFIGURATION'):
                        self.assertAlmostEqual(r['patient_volume_mL'], 40000, delta=1e-7)
                    if r['machine']['stage'] != 'TREATMENT':
                        self.assertEqual(r['uf_mL_min'], 0); self.assertEqual(r['online']['replacement_mL_min'], 0)
                        self.assertTrue(r['clamp_closed'])

    def test_illegal_transition_matrix_preserves_actual_state(self):
        # Challenge every stage-incompatible action at the real plant barrier.
        legal = {'PREPARATION': {'PRIME'}, 'PRIMING': {'CONFIGURE'}, 'CONFIGURATION': {'START'},
                 'TREATMENT': {'PAUSE', 'FINISH'}, 'PAUSED': {'START', 'FINISH'}, 'STOPPED': {'RECOVER'},
                 'RECOVERY': set(), 'FINISHED': {'CLEAN'}, 'CLEANING': {'COMPLETE'}, 'CLEANED': set()}
        actions = {'PRIME', 'CONFIGURE', 'START', 'PAUSE', 'RECOVER', 'FINISH', 'CLEAN', 'COMPLETE'}
        challenged = set()
        with LocalCluster(BUILD) as cluster:
            def intercept(path, *fields):
                if fields[0] == 'STEP5' and Path(path).parent.name == 'control':
                    state = machine.metadata(rpc(cluster.runtime / 'control/plant.sock', 'META5'))
                    stage = state['stage']; challenged.add(stage)
                    for action in actions - legal[stage]:
                        with self.subTest(stage=stage, action=action):
                            reply = rpc(cluster.runtime / 'control/plant.sock', 'CHANGE5', fields[1], fields[2], action)
                            self.assertEqual(reply[0], 'REJECT')
                            self.assertEqual(machine.metadata(rpc(cluster.runtime / 'control/plant.sock', 'META5')), state)
                return rpc(path, *fields)
            with patch.object(runner, 'rpc', side_effect=intercept):
                _, manifest = simulate(config(), cluster.runtime, BUILD)
            self.assertEqual(manifest['outcome'], 'completed', manifest['errors'])
        self.assertEqual(challenged, set(machine.STAGES))

    def test_readiness_and_priming_cannot_be_bypassed_through_recovery(self):
        with LocalCluster(BUILD) as cluster:
            f = DeviceFixture(cluster)
            f.step('PRIME'); self.assertEqual(f.view()['intent']['result'], 'transition')
            f.step('STOP'); f.step('RECOVER')
            for _ in range(3): f.step()
            f.step('RESET'); self.assertEqual(f.view()['machine']['stage'], 'PAUSED')
            f.step('START'); self.assertEqual(f.view()['intent']['result'], 'transition')
            self.assertEqual(treatment.live(rpc(f.admin, 'STATUS4'))['blood_mL_min'], 0)

    def test_each_detector_observation_bound_and_specific_actuator_action(self):
        cases = [('air', 'air', True), ('leak', 'blood_leak', True), ('stall', 'low_flow', True),
                 ('balance', 'balance', False), ('quality', 'integrity', False),
                 ('pressure', 'pressure', True), ('invalid', 'measurement', True)]
        for name, hazard, hard in cases:
            with self.subTest(name=name), LocalCluster(BUILD) as cluster:
                records, manifest = simulate(config(name), cluster.runtime, BUILD)
                self.assertEqual(manifest['outcome'], 'completed', manifest['errors'])
                first = next(r for r in records if hazard in r['machine']['alarms'])
                self.assertLessEqual(first['time_ms'], 12200)
                self.assertGreaterEqual(first['time_ms'], 12100)
                for r in records:
                    if hazard in r['machine']['alarms']:
                        self.assertEqual(r['uf_mL_min'], 0); self.assertEqual(r['online']['replacement_mL_min'], 0)
                        self.assertEqual(r['blood_mL_min'] == 0, hard)

    def test_simultaneous_hazards_apply_before_commit_and_defeat_hostile_control(self):
        with LocalCluster(BUILD) as cluster:
            f = DeviceFixture(cluster); f.treat()
            previous = treatment.live(rpc(f.admin, 'STATUS4'))
            rpc(f.admin, 'FAULT4', 'integrity', 0)
            f.prepare()
            rpc(cluster.runtime / 'protection/service.sock', 'STEP5', f.n, f.n * 100)
            isolated = treatment.live(rpc(f.admin, 'STATUS4'))
            self.assertGreater(isolated['blood_mL_min'], 0)
            self.assertEqual(isolated['uf_mL_min'], 0); self.assertEqual(isolated['online']['replacement_mL_min'], 0)
            self.assertEqual(isolated['removed_total_mL'], previous['removed_total_mL'])
            rpc(f.control, 'DEMAND5', f.n, f.n * 100, 300, 140, 120)
            result = machine.committed(rpc(f.admin, 'COMMIT5', f.n, f.n * 100)); f.n += 1
            self.assertEqual(result['uf_mL_min'], 0); self.assertGreater(result['blood_mL_min'], 0)
            rpc(f.admin, 'FAULT5', 'air', 1); rpc(f.admin, 'FAULT5', 'leak', 1)
            f.prepare(); rpc(cluster.runtime / 'protection/service.sock', 'STEP5', f.n, f.n * 100)
            live = treatment.live(rpc(f.admin, 'STATUS4'))
            self.assertEqual(live['blood_mL_min'], 0); self.assertTrue(live['clamp_closed'])
            self.assertEqual(set(f.view('protection')['machine']['alarms']), {'air', 'blood_leak', 'integrity'})
            rpc(f.control, 'DEMAND5', f.n, f.n * 100, 300, 140, 120)
            result = machine.committed(rpc(f.admin, 'COMMIT5', f.n, f.n * 100))
            self.assertEqual(result['blood_mL_min'], 0); self.assertEqual(result['uf_mL_min'], 0)

    def test_ack_silence_expiration_new_alarm_and_override_never_reset(self):
        with LocalCluster(BUILD) as cluster:
            f = DeviceFixture(cluster); f.treat(); rpc(f.admin, 'FAULT5', 'air', 1); f.step()
            path = cluster.runtime / 'device/protection.sock'
            mask = f.view('protection')['machine']['alarm_mask']
            rpc(path, 'SILENCE5', 200); self.assertFalse(f.view('protection')['machine']['annunciating'])
            f.step(); f.step(); self.assertTrue(f.view('protection')['machine']['annunciating'])
            rpc(path, 'ACK5'); rpc(path, 'SILENCE5', 120000)
            self.assertFalse(f.view('protection')['machine']['annunciating'])
            self.assertEqual(rpc(path, 'OVERRIDE5'), ['REJECT', 'device_operation'])
            self.assertEqual(f.view('protection')['machine']['alarm_mask'], mask)
            rpc(f.admin, 'FAULT5', 'leak', 1); f.step()
            self.assertTrue(f.view('protection')['machine']['annunciating'])
            self.assertEqual(f.view('protection')['machine']['acknowledged_mask'], 0)
            f.step('RESET'); self.assertEqual(f.view('protection')['intent']['result'], 'unsafe_reset')
            self.assertEqual(treatment.live(rpc(f.admin, 'STATUS4'))['blood_mL_min'], 0)

    def test_reset_needs_three_safe_cycles_and_never_resumes_automatically(self):
        with LocalCluster(BUILD) as cluster:
            f = DeviceFixture(cluster); f.treat(); rpc(f.admin, 'FAULT5', 'air', 1); f.step()
            f.step('STOP'); f.step('RECOVER'); f.step('RESET')
            self.assertEqual(f.view('protection')['intent']['result'], 'unsafe_reset')
            rpc(f.admin, 'FAULT5', 'air', 0)
            f.step('RESET'); self.assertEqual(f.view('protection')['intent']['result'], 'unsafe_reset')
            f.step(); result = f.step('RESET')
            self.assertEqual(result['machine']['stage'], 'PAUSED'); self.assertEqual(result['machine']['alarm_mask'], 0)
            self.assertEqual(result['blood_mL_min'], 0)
            result = f.step('START'); self.assertGreater(result['blood_mL_min'], 0)

    def test_unproven_low_flow_filter_and_retained_pressure_do_not_reset(self):
        for target, value in [('device:pump_stalled', 1), ('online:filter1', 100), ('edge:0', 100)]:
            with self.subTest(target=target), LocalCluster(BUILD) as cluster:
                f = DeviceFixture(cluster); f.treat()
                if target.startswith('edge:'): rpc(f.admin, 'EDGE2', 0, value, 0)
                else: rpc(f.admin, 'FAULT5' if target.startswith('device:') else 'FAULT4', target.split(':')[1], value)
                for _ in range(6): f.step()
                self.assertNotEqual(f.view()['machine']['alarm_mask'], 0)
                pressure = treatment.live(rpc(f.admin, 'STATUS4'))['pressure_mmHg']
                f.step('STOP'); f.step('RECOVER')
                for _ in range(4): f.step()
                f.step('RESET'); self.assertEqual(f.view('protection')['intent']['result'], 'unsafe_reset')
                self.assertAlmostEqual(treatment.live(rpc(f.admin, 'STATUS4'))['pressure_mmHg'], pressure)

    def test_latent_stuck_air_detector_is_an_explicit_detection_gap(self):
        c = config('air'); c['faults'].append(dict(tick=119, target='device:air_stuck', value=1))
        with LocalCluster(BUILD) as cluster:
            records, manifest = simulate(c, cluster.runtime, BUILD)
            self.assertEqual(manifest['outcome'], 'completed', manifest['errors'])
            self.assertFalse(any('air' in r['machine']['alarms'] for r in records))
            self.assertGreater(records[-1]['blood_mL_min'], 0)
            self.assertEqual(records[-1]['observations']['protection']['air_signal'], 0)

    def test_device_authority_confirmation_prescription_and_stop(self):
        with LocalCluster(BUILD) as cluster:
            self.assertEqual(rpc(cluster.runtime / 'device/control.sock', 'STATUS5'), ['REJECT', 'uninitialized'])
            f = DeviceFixture(cluster)
            for role in ('control', 'protection'):
                path = cluster.runtime / 'device' / (role + '.sock')
                for command in ('HALT', 'FAULT5', 'ONLINE4', 'PREPARE', 'ADVANCE5', 'DEMAND5', 'PERMIT', 'RESET5', 'STOP'):
                    self.assertEqual(rpc(path, command), ['REJECT', 'device_operation'])
            path = cluster.runtime / 'device/control.sock'
            token = rpc(path, 'REQUEST5', 'PRIME')[1]
            self.assertEqual(rpc(path, 'REQUEST5', 'START'), ['REJECT', 'pending'])
            self.assertEqual(rpc(path, 'CONFIRM5', int(token) + 1), ['REJECT', 'confirmation'])
            self.assertEqual(f.view()['machine']['stage'], 'PREPARATION')
            rpc(path, 'STOP5')  # Cancels pending intent; cannot later start it.
            self.assertEqual(rpc(path, 'CONFIRM5', token), ['REJECT', 'confirmation'])
            self.assertEqual(f.view()['machine']['stage'], 'STOPPED')
        with LocalCluster(BUILD) as cluster:
            f = DeviceFixture(cluster); f.treat()
            f.step('PRESCRIBE', [0, 200, 2, 0]); self.assertEqual(f.view()['intent']['result'], 'prescription_state')
            f.step('PAUSE'); f.step('PRESCRIBE', [0, 200, 2, 0]); f.step('START')
            view = f.view(); self.assertEqual(view['machine']['mode'], 'HD')
            self.assertEqual(view['machine']['blood_prescribed_mL_min'], 200)
            self.assertNotIn('patient', view); self.assertNotIn('contaminant', view['observation'])

    def test_lost_step_each_role_stops_and_invalidates_pending_m5_decisions(self):
        for role in ('control', 'protection'):
            with self.subTest(role=role), LocalCluster(BUILD) as cluster:
                calls = []
                def intercept(path, *fields):
                    calls.append((Path(path).parent.name, fields))
                    response = rpc(path, *fields)
                    if fields[0] == 'STEP5' and fields[1] == 100 and Path(path).parent.name == role:
                        raise TimeoutError('lost accepted STEP5 reply')
                    return response
                with patch.object(runner, 'rpc', side_effect=intercept):
                    records, manifest = simulate(config(), cluster.runtime, BUILD)
                self.assertEqual(len(records), 100); self.assertEqual(manifest['outcome'], 'aborted')
                self.assertTrue(manifest['stop']['outputs_zero_observed'])
                self.assertFalse(any(f[0] == 'COMMIT5' and f[1] == 100 for _, f in calls))
                self.assertEqual([r for r, f in calls if f[0] == 'STEP5' and f[1] == 100], ['control', 'protection'])
                with self.assertRaises(ProtocolError): rpc(cluster.runtime / 'admin/plant.sock', 'COMMIT5', 100, 10000)
                self.assertEqual(treatment.live(rpc(cluster.runtime / 'admin/plant.sock', 'STATUS4'))['blood_mL_min'], 0)

    def test_control_and_protection_loss_restart_cannot_clear_latches(self):
        for role in ('control', 'protection'):
            with self.subTest(role=role), LocalCluster(BUILD) as cluster:
                def before(n):
                    if n == 100: cluster.kill(role)
                records, manifest = simulate(config(), cluster.runtime, BUILD, before_tick=before)
                self.assertEqual(len(records), 100); self.assertEqual(manifest['outcome'], 'aborted')
                self.assertTrue(manifest['stop']['outputs_zero_observed'])
                restart = subprocess.run([str(BUILD / role), '--runtime-dir', str(cluster.runtime)], capture_output=True, text=True, timeout=3)
                self.assertNotEqual(restart.returncode, 0); self.assertIn('existing sockets', restart.stderr)
                self.assertEqual(treatment.live(rpc(cluster.runtime / 'admin/plant.sock', 'STATUS4'))['blood_mL_min'], 0)

    def test_m5_wall_watchdog_terminal_state_and_observation_remain_separate(self):
        with LocalCluster(BUILD) as cluster:
            f = DeviceFixture(cluster); f.treat(); before = f.view()['machine']['time_ms']
            time.sleep(2.2)
            view = f.view(); self.assertTrue(view['machine']['terminal'])
            self.assertEqual(view['machine']['time_ms'], before)
            self.assertEqual(view['machine']['stage'], 'STOPPED')
            self.assertIn('communication', view['machine']['alarms'])
            self.assertEqual(treatment.live(rpc(f.admin, 'STATUS4'))['blood_mL_min'], 0)
            self.assertEqual(rpc(cluster.runtime / 'device/control.sock', 'STOP5'), ['REJECT', 'terminal'])

    def test_evidence_rejects_forged_flush_water_and_solute(self):
        with tempfile.TemporaryDirectory() as tmp, LocalCluster(BUILD) as cluster:
            directory = Path(tmp) / 'run'; c = config(); records, manifest = simulate(c, cluster.runtime, BUILD, directory)
            self.assertEqual(manifest['outcome'], 'completed', manifest['errors'])
            original = list(records)
            for kind in ('water', 'mass', 'tick'):
                records = copy.deepcopy(original)
                if kind == 'water': records[10]['patient']['flush_in_mL'] += 1
                elif kind == 'mass': records[10]['patient']['flush_output_mmol'][0] += 1
                else: records[10]['machine']['flush_out_tick_mL'] = 0
                data = ''.join(json.dumps(r, sort_keys=True, separators=(',', ':')) + '\n' for r in records).encode()
                (directory / 'trajectory.jsonl').write_bytes(data)
                manifest['trajectory_sha256'] = hashlib.sha256(data).hexdigest()
                (directory / 'manifest.json').write_text(json.dumps(manifest))
                with self.subTest(kind=kind), self.assertRaises(ValueError):
                    verify_models.verify(directory, c, manifest['build']['source_sha256'])

    def test_configuration_bounds_and_exact_replay(self):
        c = config('air'); hashes = []
        for _ in range(2):
            with LocalCluster(BUILD) as cluster:
                _, manifest = simulate(c, cluster.runtime, BUILD)
                self.assertEqual(manifest['outcome'], 'completed', manifest['errors']); hashes.append(manifest['trajectory_sha256'])
        self.assertEqual(hashes[0], hashes[1])
        for mutate in (lambda x: x['workflow'].append(x['workflow'][0]),
                       lambda x: x['workflow'][0].update(action='OVERRIDE'),
                       lambda x: x['workflow'][0].update(action='SILENCE', values=[120001]),
                       lambda x: x['faults'][0].update(value=float('nan'))):
            invalid = copy.deepcopy(c); mutate(invalid)
            with self.assertRaises(ValueError): validate(invalid)
