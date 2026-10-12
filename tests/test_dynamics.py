"""Dynamic model acceptance, benchmark holdout and bounded transport regression."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'python'))
from dialysislab import physical
from dialysislab.calibration import fit,clearance
from dialysislab.compartments import Compartments
from dialysislab.protocol import read_line,ProtocolError


class DynamicsTests(unittest.TestCase):
    def test_gas_pumps_balancing_and_independent_level_protection(self):
        with tempfile.TemporaryDirectory() as d:
            binary=Path(d)/'dynamic'
            subprocess.run(['g++','-std=c++17','-O2','-Wall','-Wextra','-Werror','-I'+str(ROOT/'src'),str(ROOT/'tests/dynamic_model.cpp'),'-o',str(binary)],check=True,capture_output=True)
            r=subprocess.run([str(binary)],capture_output=True,text=True,timeout=60)
            self.assertEqual(r.returncode,0,r.stdout+r.stderr)

    def test_reference_holdout_and_discretization_are_reported(self):
        data=json.loads((ROOT/'references/dialyzer_benchmarks.json').read_text())
        for profile in data['profiles']:
            report=fit(profile)
            self.assertTrue(report['accepted']);self.assertLess(abs(report['holdout_relative_error']),.02)
            self.assertIn('blood rheology',report['uncalibrated'])
        # Exact countercurrent exchanger limit; this does not reuse the FV solve.
        import math
        koa,qb,qd=500,300,500;e=math.exp(koa*(1/qb-1/qd))
        exact=qb*(e-1)/(e-qb/qd)
        coarse=abs(clearance(koa,qb,qd,12)-exact);fine=abs(clearance(koa,qb,qd,48)-exact)
        self.assertLess(fine,coarse/3)

    def test_distributed_transit_delay_conservation_and_atomic_rejection(self):
        c=json.loads((ROOT/'scenarios/device_guided.json').read_text());p=Compartments(physical.patient_configuration(c),True,True)
        d=p.config['extracorporeal'];snapshot=None
        for n in range(30):
            q=dict(sequence=n,time_ms=n*1000,dt_ms=1000,draw_mL=5,return_mL=5,uf_mL=0,stored_mL=0,
                clearance_mL_min=[0]*6,sieving=[1]*6,dialysate_mmol_L=[0]*6,pre_mL=0,post_mL=0,
                substitution_mmol_L=[0]*6,flush_in_mL=0,flush_out_mL=0,flush_mmol_L=[0]*6,rinseback=False,
                distributed=dict(volumes_mL=d['volumes_mL'],filtration_mL=[0]*12,dialysate_mL_min=0,dialysate_storage_mL=0,dialysate_drain_mL_min=0,membrane_open=False))
            snapshot=p.advance(q)
            if n==0:
                cells=snapshot['distributed']['compartments']
                self.assertGreater(cells[0]['hematocrit'],cells[-1]['hematocrit']*100)
            self.assertLess(abs(snapshot['hemodynamics']['rbc_residual_mL']),1e-6)
        saved=copy.deepcopy(p.snapshot());bad=copy.deepcopy(q);bad.update(sequence=30,time_ms=30000)
        bad['distributed']['volumes_mL']=list(d['volumes_mL']);bad['distributed']['volumes_mL'][0]+=1
        with self.assertRaises(ValueError):p.advance(bad)
        self.assertEqual(p.snapshot(),saved)
        raw=('DL1 PATIENT5 '+json.dumps(snapshot,separators=(',',':'))+'\n').encode()
        self.assertGreater(len(raw),4096);self.assertLess(len(raw),32768)
        class Connection:
            def __init__(self,data):self.data=iter(data)
            def settimeout(self,value):pass
            def recv(self,n):return bytes([next(self.data)])
        with self.assertRaises(ProtocolError):read_line(Connection(raw),time.monotonic()+5)
        self.assertEqual(read_line(Connection(raw),time.monotonic()+5,32768)[0],'PATIENT5')
        with self.assertRaises(ProtocolError):read_line(Connection(b'x'*32768),time.monotonic()+5,32768)


if __name__=='__main__':unittest.main()
