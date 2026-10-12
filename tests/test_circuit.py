"""M2 independent analytic oracles and real process-boundary regressions."""
import copy
from decimal import Decimal
import json
import math
import os
from pathlib import Path
import sys
import time
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'python'))
from dialysislab import circuit, runner
from dialysislab.protocol import ProtocolError, rpc, state
from dialysislab.patient import Patient
sys.path.insert(0, str(ROOT / 'tools'))
import verify_models

BUILD = Path(os.environ.get('DIALYSISLAB_BUILD_DIR', ROOT / 'build'))
CONFIG = json.loads((ROOT / 'scenarios/circuit_small.json').read_text())


class CircuitTests(unittest.TestCase):
    def run_scenario(self, config):
        with runner.LocalCluster(BUILD) as cluster:
            records, manifest = runner.simulate(config, cluster.runtime, BUILD)
        self.assertEqual(manifest['outcome'], 'completed', manifest['errors'])
        return records, manifest

    @staticmethod
    def single_node(dt=100, ticks=100):
        config = copy.deepcopy(CONFIG)
        config.update(uf_mL_min=0, dt_ms=dt, ticks=ticks)
        config['circuit'].update(compliance_mL_mmHg=[0.02], edges=[[1, 0, 0.5, 'dialyzer', False]],
                                 pump_node=1, sensor_node=1, sensor_edge=0, dialyzer_edge=0)
        config['circuit']['profile']['resistance_mmHg_min_mL'] = 0.5
        return config

    def test_rc_solution_and_step_halving(self):
        duration = 0.5 / 60
        asymptote = 300 / (2 + 300 / 600)
        tau = 0.02 / (2 + 300 / 600)
        analytic = asymptote * (1 - math.exp(-duration / tau))
        errors = []
        for dt in (100, 50, 25):
            config = self.single_node(dt, 500 // dt)
            records, _ = self.run_scenario(config)
            pressure = records[-1]['circuit']['pressure_mmHg'][0]
            backward_euler = asymptote * (1 - (1 + dt / 60000 / tau) ** (-config['ticks']))
            self.assertAlmostEqual(pressure, backward_euler, delta=1e-8)
            errors.append(abs(pressure - analytic))
        self.assertGreater(errors[0] / errors[1], 1.8)
        self.assertGreater(errors[1] / errors[2], 1.8)
        records, _ = self.run_scenario(self.single_node())
        self.assertAlmostEqual(records[-1]['pressure_mmHg'], asymptote, delta=1e-6 * asymptote)

    def test_branch_resistance_clamps_and_steady_flow(self):
        config = self.single_node(ticks=300)
        config['circuit']['edges'] += [[1, 0, 1, 'resistor', False], [1, 0, 0.01, 'clamp', True]]
        records, _ = self.run_scenario(config)
        # Two open parallel resistances: equivalent R=1/3. Closed shunt contributes zero.
        expected_p = 300 / (3 + 300 / 600)
        last = records[-1]['circuit']
        self.assertAlmostEqual(last['pressure_mmHg'][0], expected_p, delta=1e-6)
        self.assertEqual(last['edge_mL_min'][2], 0)
        self.assertAlmostEqual(last['pump_mL_min'], expected_p * 3, delta=1e-6)

    def test_water_balance_independent_decimal_ledger(self):
        records, _ = self.run_scenario(CONFIG)
        cumulative = Decimal(0)
        for record in records:
            c = record['circuit']
            self.assertLess(abs(c['draw_tick_mL'] - c['return_tick_mL'] - c['uf_tick_mL']
                                - c['storage_change_mL']), 1e-8)
            # Independent node-volume computation from pressure and configured C.
            stored = sum(Decimal(str(p)) * Decimal(str(cap)) for p, cap in
                         zip(c['pressure_mmHg'], CONFIG['circuit']['compliance_mL_mmHg']))
            cumulative += Decimal(str(c['uf_mL_min'])) * Decimal(CONFIG['dt_ms']) / Decimal(60000)
            self.assertLess(abs(Decimal(str(record['patient_volume_mL'])) + stored + cumulative
                                - Decimal(CONFIG['patient_volume_mL'])), Decimal('1e-8'))
            self.assertGreaterEqual(record['patient_volume_mL'], 0)

    def test_transport_oracle_profiles_equilibrium_and_no_flow(self):
        results = []
        for name in ('circuit_small', 'circuit_large'):
            config = json.loads((ROOT / ('scenarios/' + name + '.json')).read_text())
            records, _ = self.run_scenario(config)
            c = records[-1]['circuit']
            qb = abs(c['edge_mL_min'][config['circuit']['dialyzer_edge']])
            p, tr = config['circuit']['profile'], config['transport']
            for i in range(6):
                k = (p['koa_mL_min'][i] * qb * tr['dialysate_mL_min'] /
                     (qb * tr['dialysate_mL_min'] + p['koa_mL_min'][i] * tr['dialysate_mL_min'] + p['koa_mL_min'][i] * qb))
                expected = k * (tr['blood_mmol_L'][i] - tr['dialysate_mmol_L'][i]) / 1000
                self.assertAlmostEqual(c['diffusion_mmol_min'][i], expected, delta=1e-12)
                conv = c['uf_mL_min'] * p['sieving'][i] * tr['blood_mmol_L'][i] / 1000
                self.assertAlmostEqual(c['convection_mmol_min'][i], conv, delta=1e-12)
            self.assertLess(c['diffusion_mmol_min'][4], 0)  # Reverse bicarbonate gradient.
            results.append(c['diffusion_mmol_min'][0])
        self.assertGreater(results[1], results[0])
        for zero in ('flow', 'gradient', 'membrane'):
            config = copy.deepcopy(CONFIG)
            config.update(ticks=5, uf_mL_min=0)
            if zero == 'flow': config['blood_mL_min'] = 0
            if zero == 'gradient': config['transport']['blood_mmol_L'] = config['transport']['dialysate_mmol_L'][:]
            if zero == 'membrane': config['circuit']['profile']['koa_mL_min'] = [0] * 6
            records, _ = self.run_scenario(config)
            for record in records:
                self.assertEqual(record['circuit']['diffusion_mmol_min'], [0] * 6)
                self.assertEqual(record['circuit']['convection_mmol_min'], [0] * 6)

    def test_occlusion_observation_bound_and_isolated_storage(self):
        config = json.loads((ROOT / 'scenarios/circuit_occlusion.json').read_text())
        records, _ = self.run_scenario(config)
        first = next(r for r in records if r['latched'])
        # Declared demonstration bound: <=1000 virtual ms after closing return clamp.
        self.assertLessEqual(first['time_ms'] - 2000, 1000)
        self.assertGreaterEqual(first['observations']['protection']['pressure_mmHg'], 250)
        self.assertLess(records[first['sequence'] - 1]['observations']['protection']['pressure_mmHg'], 250)
        for record in records[first['sequence']:]:
            c = record['circuit']
            self.assertEqual(c['stored_mL'], first['circuit']['stored_mL'])
            self.assertEqual((c['pump_mL_min'], c['return_mL_min'], c['uf_mL_min']), (0, 0, 0))
            self.assertEqual(record['reason'], 'pressure')

    def test_sensor_fault_and_repeatability(self):
        config = copy.deepcopy(CONFIG)
        config.update(ticks=12, faults=[dict(tick=5, target='protection_sensor', value='stale')])
        a, ma = self.run_scenario(config)
        b, mb = self.run_scenario(config)
        self.assertEqual(ma['trajectory_sha256'], mb['trajectory_sha256'])
        self.assertEqual(a[5]['reason'], 'measurement')
        self.assertEqual(a[5]['observations']['control']['sequence'], 5)
        self.assertEqual(b[5]['observations']['protection']['sequence'], 4)

    def test_config_rejection_and_admin_authority(self):
        invalid = []
        for field, value in [('pump_node', 0), ('sensor_edge', 99), ('compliance_mL_mmHg', [0]),
                             ('pump_head_mmHg', float('inf'))]:
            config = copy.deepcopy(CONFIG); config['circuit'][field] = value; invalid.append(config)
        config = copy.deepcopy(CONFIG); config['circuit']['profile']['sieving'][0] = 1.1; invalid.append(config)
        config = copy.deepcopy(CONFIG); config['faults'] = [dict(tick=1, target='resistance', value=4)]; invalid.append(config)
        for config in invalid:
            with self.assertRaises(ValueError): runner.validate(config)
        with runner.LocalCluster(BUILD) as cluster:
            with self.assertRaises(ProtocolError): rpc(cluster.runtime / 'control/plant.sock', 'CSTATE2')
            self.assertEqual(state(rpc(cluster.runtime / 'admin/plant.sock', 'STATUS'))['reason'], 'protocol')

    def test_lost_step_reply_preserves_circuit_storage_and_cancels_tick(self):
        for role in ('control', 'protection'):
            with self.subTest(role=role), runner.LocalCluster(BUILD) as cluster:
                calls = []
                def routed(path, *fields):
                    calls.append(fields)
                    result = rpc(path, *fields)
                    if path == cluster.runtime / role / 'service.sock' and fields[:3] == ('STEP', 5, 500):
                        raise ConnectionError('lost reply after actual plant acknowledgment')
                    return result
                with patch.object(runner, 'rpc', side_effect=routed):
                    records, manifest = runner.simulate(CONFIG, cluster.runtime, BUILD)
                self.assertEqual(len(records), 5)
                self.assertEqual(manifest['outcome'], 'aborted')
                self.assertTrue(manifest['stop']['outputs_zero_observed'])
                self.assertFalse(any(f[0] in ('COMMIT', 'COMMIT2', 'FLUID2') and f[1] == 5 for f in calls))
                physical = circuit.state(rpc(cluster.runtime / 'admin/plant.sock', 'CSTATE2'))
                self.assertEqual(physical['stored_mL'], records[-1]['circuit']['stored_mL'])
                self.assertEqual(physical['pump_mL_min'], 0)
                for command in [('COMMIT2', 5, 500), ('EDGE2', 0, 1, 0)]:
                    with self.assertRaises(ProtocolError): rpc(cluster.runtime / 'admin/plant.sock', *command)
                self.assertEqual(circuit.state(rpc(cluster.runtime / 'admin/plant.sock', 'CSTATE2')), physical)

    def test_watchdog_after_commit_preserves_atomic_water_snapshot(self):
        config = copy.deepcopy(CONFIG)
        config['ticks'] = 1
        with runner.LocalCluster(BUILD) as cluster:
            calls = []
            def routed(path, *fields):
                calls.append(fields[0])
                reply = rpc(path, *fields)
                if fields[0] == 'COMMIT2':
                    time.sleep(2.15)  # Real plant watchdog expires after the committed reply.
                return reply
            with patch.object(runner, 'rpc', side_effect=routed):
                records, manifest = runner.simulate(config, cluster.runtime, BUILD)
            self.assertEqual(manifest['outcome'], 'aborted')
            self.assertEqual(manifest['final_plant_observation']['reason'], 'liveness')
            self.assertEqual(len(records), 1)  # The already integrated tick remains accounted for.
            record = records[0]
            self.assertGreater(record['circuit']['draw_tick_mL'], 0)
            self.assertLess(abs(config['patient_volume_mL'] - record['patient_volume_mL']
                                - record['circuit']['stored_mL'] - record['removed_total_mL']), 1e-8)
            live = circuit.state(rpc(cluster.runtime / 'admin/plant.sock', 'CSTATE2'))
            self.assertEqual(live['draw_tick_mL'], 0)
            self.assertEqual(live['stored_mL'], record['circuit']['stored_mL'])
            self.assertNotIn('CSTATE2', calls)  # No split read for accounting.
            self.assertTrue(manifest['stop']['outputs_zero_observed'])

    def test_volume_ceiling_drainage_and_explicit_roundoff_budget(self):
        config = self.single_node(ticks=300)
        config.update(patient_volume_mL=100000,
                      faults=[dict(tick=1, target='control_sensor', value='missing')])
        records, _ = self.run_scenario(config)
        for record in records:
            self.assertLessEqual(record['patient_volume_mL'], 100000)
            self.assertLessEqual(abs(record['patient_numerical_correction_mL']), 1e-8)
            self.assertLess(abs(record['patient_volume_mL'] + record['circuit']['stored_mL'] - 100000), 1e-8)
        self.assertAlmostEqual(records[-1]['patient_volume_mL'], 100000, delta=1e-8)
        patient = Patient()
        patient.handle(['INIT', '100000'])
        with self.assertRaises(ProtocolError):
            patient.handle(['FLUID2', '0', '0', '100', '-0.000001'])
        self.assertEqual(patient.volume, 100000)
        reply = patient.handle(['FLUID2', '0', '0', '100', '-0.0000000001'])
        self.assertTrue(reply.startswith('DL1 FLUID_VOLUME2'))
        self.assertEqual(patient.volume, 100000)
        self.assertEqual(patient.numerical_correction, Decimal('-1e-10'))
        for n in range(1, 100):
            patient.handle(['FLUID2', str(n), str(n * 100), '100', '-0.0000000001'])
        with self.assertRaises(ProtocolError):
            patient.handle(['FLUID2', '100', '10000', '100', '-0.0000000001'])
        self.assertEqual(patient.next_sequence, 100)

    def test_evidence_rejects_wrong_configuration_digest_and_stale_build(self):
        config = copy.deepcopy(CONFIG)
        config['ticks'] = 2
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp) / 'run'
            with runner.LocalCluster(BUILD) as cluster:
                _, manifest = runner.simulate(config, cluster.runtime, BUILD, directory)
            sources = manifest['build']['source_sha256']
            verify_models.verify(directory, config, sources)
            requested = copy.deepcopy(config)
            requested['faults'] = [dict(tick=1, target='edge:2', value=dict(resistance=0.1, closed=True))]
            with self.assertRaisesRegex(ValueError, 'configuration'):
                verify_models.verify(directory, requested, sources)
            stale = dict(sources, **{'src/circuit.hpp': '0' * 64})
            with self.assertRaisesRegex(ValueError, 'build sources'):
                verify_models.verify(directory, config, stale)
            manifest['configuration_sha256'] = '0' * 64
            (directory / 'manifest.json').write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, 'configuration'):
                verify_models.verify(directory, config, sources)


if __name__ == '__main__':
    unittest.main()
