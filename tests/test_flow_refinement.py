"""Independent conservative-transfer oracles and actual fine-step valve transients."""
import copy
import math
from pathlib import Path
import random
import sys
import tempfile
import unittest
sys.path[:0]=[str(Path(__file__).resolve().parents[1]/'tools'),str(Path(__file__).resolve().parents[1]/'python')]
from dialysislab.distributed import advect_face, solve
from dialysislab.compartments import Compartments
from dialysislab import physical
from flow_refinement import configuration, connected, sample_run, valve_campaign
from audit_fixture import compile_driver


class FaceAdvectionTests(unittest.TestCase):
    def test_both_directions_match_closed_two_cell_mass_solution(self):
        for volume in (3.0,-7.0,0.0):
            with self.subTest(volume=volume):
                sizes=[10+volume,20-volume]
                matrix=[[sizes[0],0.0],[0.0,sizes[1]]]
                advect_face(matrix,0,1,volume)
                c=solve(matrix,[20.,160.])
                expected=[(20+volume*8)/sizes[0],8] if volume>=0 else [2,(160-volume*2)/sizes[1]]
                for actual,wanted in zip(c,expected):self.assertAlmostEqual(actual,wanted,places=12)
                self.assertAlmostEqual(math.fsum(v*x for v,x in zip(sizes,c)),180,places=11)

    def test_random_internal_reversals_conserve_mass_and_preserve_bounds(self):
        rng=random.Random(42013)
        for uniform in (False,True):
            for _ in range(50):
                n=12;old=[rng.uniform(2,20) for _ in range(n)]
                concentration=[4.0 if uniform else rng.uniform(0,20) for _ in range(n)]
                faces=[0.0]+[rng.uniform(-.5,.5) for _ in range(n-1)]+[0.0]
                new=[old[j]+faces[j+1]-faces[j] for j in range(n)]
                matrix=[[new[i] if i==j else 0.0 for j in range(n)] for i in range(n)]
                for j in range(1,n):advect_face(matrix,j-1,j,faces[j])
                result=solve(matrix,[v*c for v,c in zip(old,concentration)])
                self.assertAlmostEqual(math.fsum(v*c for v,c in zip(new,result)),math.fsum(v*c for v,c in zip(old,concentration)),places=10)
                self.assertGreaterEqual(min(result),min(concentration)-1e-12)
                self.assertLessEqual(max(result),max(concentration)+1e-12)
                if uniform:
                    for c in result:self.assertAlmostEqual(c,4,places=12)

    def test_external_flow_reversal_remains_rejected_atomically(self):
        c=configuration('hd',25);patient=Compartments(physical.patient_configuration(c),True,True)
        d=patient.config['extracorporeal'];before=patient.snapshot()
        request=dict(sequence=0,time_ms=0,dt_ms=25,draw_mL=0,return_mL=0,uf_mL=0,stored_mL=0,
            clearance_mL_min=[0]*6,sieving=[1]*6,dialysate_mmol_L=[0]*6,pre_mL=0,post_mL=0,
            substitution_mmol_L=[0]*6,flush_in_mL=0,flush_out_mL=0,flush_mmol_L=[0]*6,rinseback=False,
            distributed=dict(volumes_mL=d['volumes_mL'],filtration_mL=[0]*12,dialysate_mL_min=0,
                dialysate_storage_mL=0,dialysate_drain_mL_min=0,membrane_open=False))
        for field in ('dialysate_mL_min','dialysate_drain_mL_min'):
            bad=copy.deepcopy(request);bad['distributed'][field]=-1
            with self.subTest(field=field),self.assertRaises(ValueError):patient.advance(bad)
            self.assertEqual(patient.snapshot(),before)


class FlowRefinementTests(unittest.TestCase):
    def test_valve_volume_and_event_times_match_analytic_pulse_train(self):
        with tempfile.TemporaryDirectory() as directory:
            report=valve_campaign(directory)
        self.assertTrue(report['successful']);self.assertEqual(len(report['cases']),24)

    def test_fine_step_coupled_hd_and_hdf_accept_internal_reversals(self):
        with tempfile.TemporaryDirectory() as directory:
            binary=compile_driver(directory)
            for mode in ('hd','hdf_pre','hdf_post'):
                with self.subTest(mode=mode):
                    f=connected(binary,configuration(mode,25))
                    try:report=sample_run(f,25)
                    finally:f.close()
                    if mode=='hd':
                        self.assertGreater(report['reverse_internal_face_count'],0)
                    self.assertLess(report['maximum_water_residual_mL'],1e-6)
                    self.assertLess(report['maximum_solute_residual_mmol'],1e-6)
                    self.assertEqual(len(report['samples']),30)

if __name__=='__main__':unittest.main()
