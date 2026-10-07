"""M3 analytic/independent ledgers and actual coupled service regressions."""
import copy
import json
import math
import os
from pathlib import Path
import random
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'python'))
from dialysislab.compartments import Compartments, validate_snapshot
from dialysislab.protocol import ProtocolError, rpc
from dialysislab.runner import LocalCluster, simulate, validate

BUILD = Path(os.environ.get('DIALYSISLAB_BUILD_DIR', ROOT / 'build'))
CONFIG = json.loads((ROOT / 'scenarios/patient_baseline.json').read_text())


def transaction(n, dt=100, **values):
    data = dict(sequence=n, time_ms=n * dt, dt_ms=dt, draw_mL=0, return_mL=0,
                uf_mL=0, stored_mL=0, clearance_mL_min=[0] * 6, sieving=[1] * 6,
                dialysate_mmol_L=[0] * 6)
    data.update(values)
    return data


def inert_config():
    config = copy.deepcopy(CONFIG['patient'])
    config.update(refill_mL_min=0, exchange_mL_min=[0] * 6, generation_mmol_min=[0] * 6)
    return config


class CompartmentNumerics(unittest.TestCase):
    def test_100000_steps_rss_and_mass_ledger(self):
        result = subprocess.run([sys.executable, str(ROOT / 'tests/patient_memory_probe.py')],
                                capture_output=True, text=True, timeout=180, check=True)
        report = json.loads(result.stdout)
        self.assertEqual(report['ticks'], 100000)
        self.assertEqual(report['time_ms'], 1000000)
        self.assertLess(report['peak_rss_bytes'], 64 * 1024 * 1024)
        self.assertLess(report['maximum_mass_residual_mmol'], 1e-6)

    def test_two_compartment_analytic_transient_and_convergence(self):
        config = inert_config()
        config.update(volume_mL=[1000, 1000], partition=[1] * 6, exchange_mL_min=[1000, 0, 0, 0, 0, 0])
        config['concentration_mmol_L'][0][0] = 20
        config['concentration_mmol_L'][1][0] = 0
        errors = []
        expected = 10 + 10 * math.exp(-2)
        for dt in (1000, 500, 250):
            patient = Compartments(config)
            for n in range(60000 // dt): patient.advance(transaction(n, dt))
            actual = patient.snapshot()['concentration_mmol_L'][0][0]
            self.assertAlmostEqual(actual, 10 + 10 * (1 + 2 * dt / 60000) ** (-60000 // dt), delta=1e-10)
            errors.append(abs(actual - expected))
        self.assertGreater(errors[0] / errors[1], 1.9)
        self.assertGreater(errors[1] / errors[2], 1.9)

    def test_equilibrium_zero_mass_and_acid_base_indicator(self):
        config = inert_config()
        config['concentration_mmol_L'] = [[0, 140, 5, 105, 24, 2.4]] * 2
        config.update(partition=[1] * 6, exchange_mL_min=[2000] * 6)
        patient = Compartments(config)
        original = patient.snapshot()
        for n in range(100): patient.advance(transaction(n))
        final = validate_snapshot(patient.snapshot())
        for actual, expected in zip(final['mass_mmol'], original['mass_mmol']):
            for a, e in zip(actual, expected): self.assertAlmostEqual(a, e, delta=1e-9)
        self.assertEqual([row[0] for row in final['mass_mmol']], [0, 0, 0])
        self.assertAlmostEqual(final['illustrative_pH'], 6.1 + math.log10(20), delta=1e-12)
        config['concentration_mmol_L'] = [[0] * 6, [0] * 6]
        self.assertIsNone(Compartments(config).snapshot()['illustrative_pH'])

    def test_external_inputs_generation_outputs_and_weight(self):
        config = inert_config()
        config.update(external_in_mL_min=60, external_mmol_L=[2, 140, 4, 105, 24, 2.4],
                      generation_mmol_min=[0.2, 0, 0, 0, 0, 0])
        patient = Compartments(config)
        original = patient.snapshot()
        for n in range(60): patient.advance(transaction(n, 1000))
        final = patient.snapshot()
        self.assertAlmostEqual(final['volume_mL'][0] - original['volume_mL'][0], 60, delta=1e-8)
        self.assertAlmostEqual(final['mass_mmol'][0][0] - original['mass_mmol'][0][0], 0.32, delta=1e-9)
        self.assertEqual(final['external_in_mL'], 60)
        self.assertAlmostEqual(final['weight_kg'], config['initial_weight_kg'] + 0.06, delta=1e-12)
        self.assertEqual(final['gross_uf_mL'], 0)
        config = inert_config(); config['external_out_mL_min'] = 60
        patient = Compartments(config)
        for n in range(60): patient.advance(transaction(n, 1000))
        final = patient.snapshot()
        self.assertAlmostEqual(final['concentration_mmol_L'][0][0], 20, delta=1e-10)
        self.assertAlmostEqual(final['output_mmol'][0], 1.2, delta=1e-10)
        self.assertAlmostEqual(final['net_patient_loss_mL'], 60, delta=1e-8)

    def test_random_transfers_conserve_each_species_without_negative_mass(self):
        config = inert_config()
        config.update(refill_mL_min=1000, exchange_mL_min=[2000] * 6)
        patient = Compartments(config)
        initial = [math.fsum(row[i] for row in patient.snapshot()['mass_mmol']) for i in range(6)]
        rng = random.Random(42)
        for n in range(1000):
            draw = rng.uniform(0, 0.5)
            state = patient.advance(transaction(n, draw_mL=draw, return_mL=draw,
                                   clearance_mL_min=[rng.uniform(0, 500) for _ in range(6)],
                                   dialysate_mmol_L=[rng.uniform(0, 100) for _ in range(6)]))
            for i in range(6):
                remaining = math.fsum(row[i] for row in state['mass_mmol'])
                self.assertAlmostEqual(remaining + state['diffusive_mmol'][i] + state['convective_mmol'][i], initial[i], delta=1e-7)
                self.assertTrue(all(row[i] >= 0 for row in state['mass_mmol']))
                self.assertTrue(all(row[i] >= 0 for row in state['concentration_mmol_L']))

    def test_rejected_transaction_is_atomic_and_inputs_are_bounded(self):
        patient = Compartments(inert_config())
        before = patient.snapshot()
        for changes in [dict(sequence=1), dict(dt_ms=0), dict(draw_mL=1), dict(sieving=[2] * 6),
                        dict(clearance_mL_min=[float('nan')] * 6), dict(stored_mL=100000)]:
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                patient.advance(transaction(0, **changes))
            self.assertEqual(patient.snapshot(), before)
        config = copy.deepcopy(CONFIG)
        config['patient']['volume_mL'][0] += 1
        with self.assertRaises(ValueError): validate(config)


class CoupledProcesses(unittest.TestCase):
    def test_synthetic_scenarios_mass_water_and_profile_effect(self):
        removals = {}
        for name in ('patient_baseline', 'patient_overload', 'patient_imbalance', 'patient_large'):
            config = json.loads((ROOT / ('scenarios/' + name + '.json')).read_text())
            config['ticks'] = 100
            with LocalCluster(BUILD) as cluster:
                records, manifest = simulate(config, cluster.runtime, BUILD)
            self.assertEqual(manifest['outcome'], 'completed', manifest['errors'])
            p = config['patient']
            initial = [sum(p['volume_mL'][j] * p['concentration_mmol_L'][j][i] / 1000 for j in range(2))
                       + p['prime_mL'] * p['concentration_mmol_L'][0][i] / 1000 for i in range(6)]
            for record in records:
                state = record['patient']
                expected_water = config['patient_volume_mL'] + p['prime_mL'] + state['external_in_mL'] - state['external_out_mL']
                self.assertAlmostEqual(sum(state['volume_mL']) + record['removed_total_mL'], expected_water, delta=1e-8)
                for i in range(6):
                    expected = initial[i] + state['input_mmol'][i] - state['output_mmol'][i]
                    actual = math.fsum(row[i] for row in state['mass_mmol']) + state['diffusive_mmol'][i] + state['convective_mmol'][i]
                    self.assertAlmostEqual(actual, expected, delta=1e-7)
                self.assertAlmostEqual(state['weight_kg'], p['initial_weight_kg'] - state['net_patient_loss_mL'] / 1000, delta=1e-10)
                self.assertNotIn('patient', record['observations']['protection'])
            last = records[-1]['patient']
            self.assertGreater(last['diffusive_mmol'][0], 0)
            self.assertLess(last['diffusive_mmol'][4], 0)
            self.assertGreater(last['net_patient_loss_mL'], last['gross_uf_mL'])
            removals[name] = last['diffusive_mmol'][0]
        self.assertGreater(removals['patient_large'], removals['patient_baseline'])

    def test_repeatability_and_real_patient_failure(self):
        config = copy.deepcopy(CONFIG); config['ticks'] = 10
        hashes = []
        for _ in range(2):
            with LocalCluster(BUILD) as cluster:
                _, manifest = simulate(config, cluster.runtime, BUILD)
            self.assertEqual(manifest['outcome'], 'completed', manifest['errors'])
            hashes.append(manifest['trajectory_sha256'])
        self.assertEqual(hashes[0], hashes[1])
        with LocalCluster(BUILD) as cluster:
            records, manifest = simulate(config, cluster.runtime, BUILD,
                                         before_tick=lambda n: cluster.kill('patient') if n == 5 else None)
        self.assertEqual(manifest['outcome'], 'aborted')
        self.assertEqual(len(records), 5)
        self.assertEqual(manifest['uncommitted_plant_state']['sequence'], 5)
        self.assertTrue(manifest['stop']['outputs_zero_observed'])

    def test_sensor_failure_stops_device_without_freezing_body_exchange(self):
        config = copy.deepcopy(CONFIG)
        config.update(ticks=10, faults=[dict(tick=5, target='protection_sensor', value='invalid')])
        with LocalCluster(BUILD) as cluster:
            records, manifest = simulate(config, cluster.runtime, BUILD)
            with self.assertRaises(ProtocolError): rpc(cluster.runtime / 'control/plant.sock', 'CSTATE3')
        self.assertEqual(manifest['outcome'], 'completed', manifest['errors'])
        self.assertEqual(records[5]['reason'], 'measurement')
        self.assertEqual(records[9]['patient']['gross_uf_mL'], records[5]['patient']['gross_uf_mL'])
        self.assertGreater(records[9]['patient']['input_mmol'][0], records[5]['patient']['input_mmol'][0])


if __name__ == '__main__':
    unittest.main()
