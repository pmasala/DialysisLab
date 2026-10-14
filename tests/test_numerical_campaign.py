"""Numerical oracles, deliberately bad observations, and actual coupled stimuli."""
import copy
import math
from pathlib import Path
import sys
import subprocess
import json
import tempfile
import unittest
sys.path[:0] = [str(Path(__file__).resolve().parents[1]/'tools')]
from numerical_campaign import (analytic_exchange, comparisons, compile_bench, configuration,
                                connected, kernel_mesh, metrics, run)


class NumericalCampaignTests(unittest.TestCase):
    def test_actual_patient_exchange_has_first_order_error_against_exact_solution(self):
        cases = analytic_exchange()['cases']
        for a,b in zip(cases,cases[1:]):
            self.assertGreater(a['maximum_error_mmol_L'], b['maximum_error_mmol_L'])
            self.assertAlmostEqual(math.log(a['maximum_error_mmol_L']/b['maximum_error_mmol_L'],2),1,delta=.02)
        self.assertLess(cases[-1]['maximum_error_mmol_L'],1e-5)
        self.assertLess(max(c['maximum_mass_residual_mmol'] for c in cases),1e-6)

    def test_kernel_mesh_approaches_independent_continuum_and_conserves(self):
        cases = kernel_mesh()['cases']
        self.assertEqual([c['cells'] for c in cases],[6,12,24,48,96])
        for a,b in zip(cases,cases[1:]):
            self.assertLess(b['absolute_error_mmol_L'],a['absolute_error_mmol_L'])
        self.assertLess(cases[-1]['absolute_error_mmol_L'],.05)
        self.assertLess(max(c['mass_residual_mmol_min'] for c in cases),1e-9)

    def test_grid_shape_and_nonfinite_observations_reject(self):
        a = [dict(time_ms=400,values={'level':[1,2]})]
        for b in ([],[dict(time_ms=800,values={'level':[1,2]})],
                  [dict(time_ms=400,values={'level':[1]})],
                  [dict(time_ms=400,values={'level':[float('nan'),2]})]):
            with self.subTest(b=b), self.assertRaises(ValueError): metrics(a,b)
        b = copy.deepcopy(a);b[0]['values']['level'][1] = 2.1
        self.assertAlmostEqual(metrics(a,b)['level']['maximum_absolute'],.1)
        self.assertFalse(metrics(a,b)['level']['within_proposed_budget'])
        with self.assertRaisesRegex(ValueError,'checkpoint'):
            comparisons([{'initial_sha256':'a'}, {'initial_sha256':'b'}])

    def test_timeout_retains_failure_and_refuses_to_overwrite_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)/'interrupted.json'
            command = [sys.executable, str(Path(__file__).resolve().parents[1]/'tools/numerical_campaign.py'),
                       '--output', str(output), '--timeout-seconds', '1']
            result = subprocess.run(command, capture_output=True, text=True, timeout=10)
            self.assertNotEqual(result.returncode,0)
            report = json.loads(output.read_text())
            self.assertFalse(report['execution_complete'])
            self.assertIn('TimeoutError', report['error'])
            before = output.read_bytes()
            result = subprocess.run(command, capture_output=True, text=True, timeout=10)
            self.assertNotEqual(result.returncode,0)
            self.assertEqual(output.read_bytes(),before)

    def test_all_modes_controlled_stimuli_and_checkpoint_repeatability(self):
        with tempfile.TemporaryDirectory() as directory:
            binary = compile_bench(directory)
            for mode in ('hd','hdf_pre','hdf_post'):
                with self.subTest(mode=mode):
                    config = configuration(mode,100)
                    config['treatment']['replacement_mL_min'] = 0 if mode=='hd' else 40
                    f = connected(binary,config)
                    try:
                        for _ in range(40): f.step()
                        f.save(0)
                        first = run(f,100,'combined')
                        f.restore(0)
                        repeat = run(f,100,'combined')
                        self.assertEqual(first['trajectory_sha256'],repeat['trajectory_sha256'])
                        f.restore(0)
                        fine = run(f,50,'combined')
                        self.assertEqual(first['initial_sha256'],fine['initial_sha256'])
                        self.assertEqual(len(fine['samples']),30)
                        # Known response regression: prepared concentration pulse actually reaches dialysate.
                        samples = fine['samples']
                        key = 'dialysate_local_mmol_L/urea'
                        self.assertNotEqual(samples[5]['values'][key],samples[15]['values'][key])
                        self.assertEqual([samples[i]['values']['net_uf_demand_mL_min'][0] for i in (5,6,16,22)], [5,12,2,5])
                        self.assertGreater(samples[15]['values']['prepared_mmol_L/urea'][0], .9)
                        self.assertGreater(samples[15]['values']['prepared_mmol_L/potassium'][0], 2.4)
                        difference = metrics(first['samples'],fine['samples'])
                        self.assertLess(difference['pressure_mmHg']['maximum_absolute'], 1.1)
                        self.assertLess(difference['blood_local_mmol_L/urea']['maximum_absolute'], .05)
                        self.assertLess(max(fine['residual_maxima'].values()),1e-6)
                        self.assertFalse(fine['bypass_ticks'])
                    finally: f.close()

if __name__ == '__main__': unittest.main()
