"""Guided treatment model, fluid balance, actual rendering and process acceptance."""
import copy
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'python'));sys.path.insert(0,str(ROOT/'tools'))
from dialysislab.runner import validate, LocalCluster, simulate, build_identity
from dialysislab.compartments import Compartments
from dialysislab.protocol import ProtocolError
from verify_models import verify
BUILD=Path(os.environ.get('DIALYSISLAB_GUI_BUILD_DIR',os.environ.get('DIALYSISLAB_BUILD_DIR',ROOT/'build/gui'))).resolve()


def configuration():
    return json.loads((ROOT/'scenarios/device_guided.json').read_text())


class GuidedUnitTests(unittest.TestCase):
    def test_configuration_rejects_invalid_duration_and_sensor_position(self):
        c=configuration();validate(c)
        for field,value in [('test_ms',0),('treatment_ms',86400001),('disinfection_ms',True),('return_mL',1001)]:
            bad=copy.deepcopy(c);bad['guided'][field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):validate(bad)
        bad=copy.deepcopy(c);bad['circuit']['sensor_node']=0
        with self.assertRaises(ValueError):validate(bad)

    def test_return_salinity_body_gain_and_all_solute_balances(self):
        c=configuration()['patient'];p=Compartments(c,online=True,lifecycle=True)
        before=p.snapshot();initial_body=sum(before['volume_mL'][:2])
        for n in range(100):
            q=dict(sequence=n,time_ms=n*100,dt_ms=100,draw_mL=0,return_mL=.5,uf_mL=0,stored_mL=0,
                   clearance_mL_min=[0]*6,sieving=[1]*6,dialysate_mmol_L=[0]*6,pre_mL=0,post_mL=0,
                   substitution_mmol_L=[0]*6,flush_in_mL=.5,flush_out_mL=0,flush_mmol_L=[0,154,0,154,0,0],rinseback=True)
            p.advance(q)
        after=p.snapshot()
        self.assertAlmostEqual(sum(after['volume_mL'][:2])-initial_body,50,places=7)
        self.assertAlmostEqual(after['flush_in_mL'],50,places=7)
        self.assertTrue(all(abs(x)<1e-6 for x in after['mass_residual_mmol']))
        q.update(sequence=100,time_ms=10000,draw_mL=.1)
        with self.assertRaises(ProtocolError):p.advance(q)
        self.assertEqual(p.snapshot(),after)
        q.update(draw_mL=0,rinseback=False)
        with self.assertRaises(ProtocolError):p.advance(q)

    def test_guided_machine_protocol_and_actual_lvgl_view(self):
        library=BUILD/'gui-lvgl/liblvgl.a'
        if not library.exists():self.skipTest('GUI build unavailable')
        deps=ROOT/'build/gui-deps/lvgl-9.6.0'
        with tempfile.TemporaryDirectory() as directory:
            binary=Path(directory)/'guided-view'
            command=['g++','-std=c++17','-Wall','-Wextra','-Werror','-O1','-I',str(ROOT/'src'),
                     '-I',str(deps/'include'),'-I',str(deps),'-I',str(ROOT/'src/ui'),
                     '-DLV_CONF_PATH="'+str(ROOT/'src/ui/lv_conf.h')+'"','-DLV_KCONFIG_IGNORE',
                     str(ROOT/'tests/guided_view.cpp'),str(ROOT/'src/ui/font.cpp'),str(library),'-lm','-pthread','-o',str(binary)]
            if 'DIALYSISLAB_SANITIZE:BOOL=ON' in (BUILD/'CMakeCache.txt').read_text():
                command+=['-fsanitize=address,undefined','-fno-sanitize-recover=all','-fno-omit-frame-pointer']
            subprocess.run(command,check=True,capture_output=True,text=True,timeout=120)
            output=os.environ.get('DIALYSISLAB_GUIDED_CAPTURES')
            result=subprocess.run([str(binary)]+([output] if output else []),capture_output=True,text=True,timeout=30)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            self.assertIn('passed',result.stdout)

    def test_in_process_hydraulics_complete_cycle_and_patient_transactions(self):
        from dialysislab import circuit,treatment,machine
        from unittest.mock import patch
        from dialysislab.protocol import expect
        with tempfile.TemporaryDirectory() as directory:
            binary=Path(directory)/'plant-driver'
            subprocess.run(['g++','-std=c++17','-O1','-Wall','-Wextra','-Werror',str(ROOT/'tests/guided_plant.cpp'),'-o',str(binary)],check=True,capture_output=True,timeout=90)
            for mode,sub in [('HD',0),('HDF_PRE',60),('HDF_POST',60)]:
                with self.subTest(mode=mode):
                    c=configuration();c['guided'].update(test_ms=1000,treatment_ms=6000,disinfection_ms=1000,return_mL=20);c['treatment'].update(mode=mode,replacement_mL_min=sub)
                    process=subprocess.Popen([str(binary)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
                    def call(role,*fields):
                        process.stdin.write(str(role)+' DL1 '+' '.join(str(x) for x in fields)+'\n');process.stdin.flush()
                        line=process.stdout.readline().strip().split()
                        self.assertTrue(line and line[0]=='DL1',line);self.assertNotIn('DRIVER_ERROR',line)
                        return line[1:]
                    try:
                        with patch.object(circuit,'rpc',side_effect=call),patch.object(treatment,'rpc',side_effect=call),patch.object(machine,'rpc',side_effect=call):
                            circuit.configure(0,c);treatment.configure(0,c);machine.configure(0,c)
                        patient=Compartments(c['patient'],online=True,lifecycle=True);stages=set();saw_return=False
                        actions={4:'PRIME',30:'CONNECT',31:'START',46:'RETURN',70:'DISCONNECT',71:'CLEAN'}
                        for n in range(125):
                            expect(call(0,'PREPARE',n,n*500,500,.5,'none','none'),'OK',1)
                            if n in actions:expect(call(1,'CHANGE5',n,n*500,actions[n]),'OK',1)
                            if n==33:
                                self.assertEqual(call(1,'RX5',n,n*500,{'HD':0,'HDF_PRE':1,'HDF_POST':2}[mode],200,6,30 if sub else 0),['REJECT','prescription_state'])
                            if n in (32,34,36):
                                blood={32:200,34:0,36:250}[n];replacement=(40 if n==36 else 30) if sub else 0
                                mode_id={'HD':0,'HDF_PRE':1,'HDF_POST':2}[mode]
                                expect(call(1,'RX5',n,n*500,mode_id,blood,5,replacement),'OK',1)
                            expect(call(3,n,n*500),'OK',1)
                            r=machine.committed(call(0,'COMMIT5',n,n*500));m=r['machine'];g=m['guided'];h=r['circuit'];o=r['online'];stages.add(m['stage'])
                            if 32<=n<=41:
                                self.assertEqual(m['stage'],'TREATMENT')
                                self.assertEqual(g['treatment_elapsed_ms'],(n-30)*500)
                            if n in (32,34,36):
                                self.assertEqual(m['blood_prescribed_mL_min'],blood)
                                self.assertEqual(m['replacement_prescribed_mL_min'],replacement)
                            rinse=bool(g['return_in_tick_mL'] or g['return_out_tick_mL']);saw_return |= rinse
                            q=dict(sequence=n,time_ms=n*500,dt_ms=500,draw_mL=h['draw_tick_mL']-m['flush_in_tick_mL'],return_mL=h['return_tick_mL']-m['flush_out_tick_mL'],uf_mL=h['uf_tick_mL'],stored_mL=h['stored_mL'],clearance_mL_min=h['clearance_mL_min'],sieving=c['circuit']['profile']['sieving'],dialysate_mmol_L=o['concentration_mmol_L'],pre_mL=o['pre_tick_mL'],post_mL=o['post_tick_mL'],substitution_mmol_L=o['concentration_mmol_L'],flush_in_mL=m['flush_in_tick_mL'],flush_out_mL=m['flush_out_tick_mL'],flush_mmol_L=[0,154,0,154,0,0] if rinse else o['concentration_mmol_L'],rinseback=rinse)
                            patient.advance(q)
                            self.assertEqual(m['alarm_mask'],0,m)
                        self.assertTrue(saw_return)
                        self.assertEqual(m['stage'],'CLEANED',stages)
                        self.assertFalse(g['patient_connected'])
                        self.assertTrue(all(abs(x)<1e-6 for x in patient.snapshot()['mass_residual_mmol']))
                    finally:
                        process.stdin.close();process.wait(timeout=5);process.stdout.close();errors=process.stderr.read();process.stderr.close()
                    self.assertEqual(process.returncode,0,errors)


class GuidedProcessTests(unittest.TestCase):
    def test_full_guided_cycle_preserves_water_solutes_and_stage_evidence(self):
        c=configuration();c['ticks']=125;c['guided'].update(test_ms=1000,treatment_ms=2000,disinfection_ms=1000,return_mL=20)
        c['workflow']=[dict(tick=t,action=a,values=[]) for t,a in [(4,'PRIME'),(30,'CONNECT'),(31,'START'),(40,'RETURN'),(70,'DISCONNECT'),(71,'CLEAN')]]
        for mode,sub in [('HD',0),('HDF_PRE',60),('HDF_POST',60)]:
            with self.subTest(mode=mode),LocalCluster(BUILD) as cluster,tempfile.TemporaryDirectory() as directory:
                c['treatment'].update(mode=mode,replacement_mL_min=sub)
                out=Path(directory)/'run';records,manifest=simulate(c,cluster.runtime,BUILD,out)
                self.assertEqual(manifest['outcome'],'completed',manifest['errors'])
                from dialysislab.trajectory import read_records
                rows=list(read_records(out/'trajectory.jsonl'))
                stages={r['machine']['stage'] for r in rows}
                self.assertTrue({'SELF_TEST','PRIMING','CONFIGURATION','CONNECTED','TREATMENT','FINISHED','RETURNING','DISCONNECTING','DISCONNECTED','CLEANING','CLEANED'}<=stages,stages)
                self.assertEqual(rows[-1]['machine']['stage'],'CLEANED')
                self.assertFalse(rows[-1]['machine']['guided']['patient_connected'])
                returned=[r for r in rows if r['machine']['guided']['integrated_stage']=='RETURNING']
                self.assertTrue(returned)
                self.assertTrue(all(r['uf_mL_min']==0 and r['machine']['flush_out_tick_mL']==0 for r in returned))
                verify(out,c,build_identity(BUILD)['source_sha256'])


if __name__=='__main__':unittest.main()
