"""Physical equations and actual plant/patient boundaries; no clinical calibration."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'python'))
from dialysislab import circuit,treatment,machine,physical
from dialysislab.compartments import Compartments
from dialysislab.runner import validate
from dialysislab.protocol import expect


def configuration():
    return json.loads((ROOT/'scenarios/device_guided.json').read_text())


class PhysicalTests(unittest.TestCase):
    def test_equations_and_limits(self):
        with tempfile.TemporaryDirectory() as d:
            binary=Path(d)/'physics'
            subprocess.run(['g++','-std=c++17','-O2','-Wall','-Wextra','-Werror','-I'+str(ROOT/'src'),str(ROOT/'tests/physical_model.cpp'),'-o',str(binary)],check=True,capture_output=True)
            result=subprocess.run([str(binary)],capture_output=True,text=True,timeout=45)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)

    def test_initial_hematocrit_and_geometry_are_configuration_only(self):
        c=configuration();validate(c)
        for path,value in [('initial_hematocrit',.8),('vascular_mL',-1)]:
            bad=copy.deepcopy(c);bad['patient']['hemodynamics'][path]=value
            with self.assertRaises(ValueError):validate(bad)
        bad=copy.deepcopy(c);bad['physical']['blood']['arterial_diameter_mm']=0
        with self.assertRaises(ValueError):validate(bad)
        bad=copy.deepcopy(c);bad['patient']['prime_mL']+=1
        with self.assertRaises(ValueError):validate(bad)

    def test_uf_hemoconcentration_refill_and_rbc_conservation(self):
        c=configuration()['patient'];c['hemodynamics']['refill_mL_min']=0
        normal=Compartments(c,online=True,lifecycle=True);filtered=copy.deepcopy(normal)
        c_refill=copy.deepcopy(c);c_refill['hemodynamics']['refill_mL_min']=500
        refilled=Compartments(c_refill,online=True,lifecycle=True)
        for n in range(600):
            for patient,uf in ((normal,0),(filtered,.2),(refilled,.2)):
                q=dict(sequence=n,time_ms=n*1000,dt_ms=1000,draw_mL=5,return_mL=5-uf,uf_mL=uf,stored_mL=0,
                    clearance_mL_min=[0]*6,sieving=[1]*6,dialysate_mmol_L=[0]*6,pre_mL=0,post_mL=0,
                    substitution_mmol_L=[0]*6,flush_in_mL=0,flush_out_mL=0,flush_mmol_L=[0]*6,rinseback=False)
                patient.advance(q)
        a=normal.snapshot()['hemodynamics'];b=filtered.snapshot()['hemodynamics'];r=refilled.snapshot()['hemodynamics']
        self.assertGreater(b['hematocrit'],a['hematocrit']);self.assertLess(r['hematocrit'],b['hematocrit'])
        self.assertGreater(b['protein_g_dL'],a['protein_g_dL'])
        for h in (a,b,r):
            self.assertLess(abs(h['rbc_residual_mL']),1e-6);self.assertLess(abs(h['protein_residual_g']),1e-6)

    def test_in_process_physical_treatments(self):
        with tempfile.TemporaryDirectory() as d:
            binary=Path(d)/'plant'
            subprocess.run(['g++','-std=c++17','-O2','-Wall','-Wextra','-Werror',str(ROOT/'tests/guided_plant.cpp'),'-o',str(binary)],check=True,capture_output=True)
            for mode in ('HD','HDF_PRE','HDF_POST'):
                with self.subTest(mode=mode):
                    c=configuration();c['treatment'].update(mode=mode,replacement_mL_min=0 if mode=='HD' else 60)
                    c['guided'].update(test_ms=1000,treatment_ms=60000,disinfection_ms=1000,return_mL=200)
                    process=subprocess.Popen([str(binary)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
                    def call(role,*fields):
                        process.stdin.write(str(role)+' DL1 '+' '.join(str(x) for x in fields)+'\n');process.stdin.flush()
                        line=process.stdout.readline().strip().split()
                        self.assertTrue(line and line[0]=='DL1',line);self.assertNotIn('DRIVER_ERROR',line)
                        return line[1:]
                    try:
                        with patch.object(circuit,'rpc',side_effect=call),patch.object(treatment,'rpc',side_effect=call),patch.object(machine,'rpc',side_effect=call),patch.object(physical,'rpc',side_effect=call):
                            circuit.configure(0,c);treatment.configure(0,c);machine.configure(0,c)
                            patient=Compartments(c['patient'],online=True,lifecycle=True)
                            state='SELF_TEST';stages=set();observed=[];snapshot=None
                            for n in range(500):
                                if snapshot:physical.update_blood(0,snapshot)
                                expect(call(0,'PREPARE',n,n*500,500,.5,'none','none'),'OK',1)
                                action={'PREPARATION':'PRIME','CONFIGURATION':'CONNECT','CONNECTED':'START','FINISHED':'RETURN','DISCONNECTING':'DISCONNECT','DISCONNECTED':'CLEAN'}.get(state)
                                if action:expect(call(1,'CHANGE5',n,n*500,action),'OK',1)
                                expect(call(3,n,n*500),'OK',1)
                                r=machine.committed(call(0,'COMMIT5',n,n*500));m=r['machine'];g=m['guided'];h=r['circuit'];o=r['online'];state=m['stage'];stages.add(state)
                                self.assertEqual(m['alarm_mask'],0,(n,m,r['physical']))
                                rinse=bool(g['return_in_tick_mL'] or g['return_out_tick_mL'])
                                q=dict(sequence=n,time_ms=n*500,dt_ms=500,draw_mL=h['draw_tick_mL']-m['flush_in_tick_mL'],return_mL=h['return_tick_mL']-m['flush_out_tick_mL'],uf_mL=h['uf_tick_mL'],stored_mL=h['stored_mL'],clearance_mL_min=h['clearance_mL_min'],sieving=c['circuit']['profile']['sieving'],dialysate_mmol_L=o['concentration_mmol_L'],pre_mL=o['pre_tick_mL'],post_mL=o['post_tick_mL'],substitution_mmol_L=o['concentration_mmol_L'],flush_in_mL=m['flush_in_tick_mL'],flush_out_mL=m['flush_out_tick_mL'],flush_mmol_L=[0,154,0,154,0,0] if rinse else o['concentration_mmol_L'],rinseback=rinse)
                                snapshot=patient.advance(q)
                                r['patient']=snapshot;physical.verify_record(r,c)
                                if g['integrated_stage']=='TREATMENT':observed.append((r,snapshot))
                                if state=='CLEANED':break
                            self.assertEqual(state,'CLEANED',stages);self.assertEqual(len(observed),120)
                            for r,p in observed:
                                self.assertAlmostEqual(r['physical']['plasma_filtration_fraction'],r['uf_mL_min']/(r['blood_mL_min']*(1-r['physical']['inlet_hematocrit'])+(r['online']['replacement_mL_min'] if mode=='HDF_PRE' else 0)),places=7)
                                self.assertLess(abs(p['hemodynamics']['rbc_residual_mL']),1e-6)
                                self.assertTrue(all(abs(x)<1e-6 for x in p['mass_residual_mmol']))
                    finally:
                        process.stdin.close();process.wait(timeout=5);process.stdout.close();errors=process.stderr.read();process.stderr.close()
                    self.assertEqual(process.returncode,0,errors)

class PhysicalProcessTests(unittest.TestCase):
    def test_real_services_and_retained_evidence(self):
        from dialysislab.runner import LocalCluster,simulate,build_identity
        from dialysislab.trajectory import read_records
        import os
        sys.path.insert(0,str(ROOT/'tools'))
        from verify_models import verify
        build=Path(os.environ.get('DIALYSISLAB_BUILD_DIR',ROOT/'build/gui'))
        for mode in ('HD','HDF_PRE','HDF_POST'):
            c=configuration();c['ticks']=360;c['treatment'].update(mode=mode,replacement_mL_min=0 if mode=='HD' else 60)
            c['guided'].update(test_ms=1000,treatment_ms=60000,disinfection_ms=1000,return_mL=200)
            c['workflow']=[dict(tick=n,action=a,values=[]) for n,a in [(4,'PRIME'),(80,'CONNECT'),(81,'START'),(202,'RETURN'),(285,'DISCONNECT'),(286,'CLEAN')]]
            with self.subTest(mode=mode),LocalCluster(build) as cluster,tempfile.TemporaryDirectory() as d:
                _,manifest=simulate(c,cluster.runtime,build,Path(d)/'run')
                self.assertEqual(manifest['outcome'],'completed',manifest.get('errors'))
                for record in read_records(Path(d)/'run/trajectory.jsonl'):physical.verify_record(record,c)
                verify(Path(d)/'run',c,build_identity(build)['source_sha256'])


if __name__=='__main__':unittest.main()
