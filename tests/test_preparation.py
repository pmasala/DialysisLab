"""CR-MIX-001: prospective physical, control and final-delivery acceptance."""
import copy
import hashlib
import json
import os
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
from dialysislab.protocol import expect
from dialysislab.runner import validate


class PreparationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory();cls.addClassCleanup(cls.tmp.cleanup)
        cls.directory=Path(cls.tmp.name)
        for source,name in [('preparation_model.cpp','model'),('guided_plant.cpp','plant')]:
            result=subprocess.run(['g++','-std=c++17','-O2','-Wall','-Wextra','-Werror',str(ROOT/'tests'/source),'-o',str(cls.directory/name)],text=True,capture_output=True)
            if result.returncode:raise RuntimeError(result.stdout+result.stderr)

    def run_case(self,name):
        result=subprocess.run([str(self.directory/'model'),name],text=True,capture_output=True,timeout=60)
        folder=os.environ.get('DIALYSISLAB_PREPARATION_CAPTURE')
        if folder:
            path=Path(folder);path.mkdir(parents=True,exist_ok=True)
            (path/(name+'.json')).write_text(json.dumps(dict(case=name,returncode=result.returncode,stdout=result.stdout,stderr=result.stderr),indent=2)+'\n')
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)

    def test_line_air_water_and_concentrate_displacement(self):self.run_case('line')
    def test_distinct_pump_displacement_pressure_and_air_efficiency(self):self.run_case('pump')
    def test_cartridge_liquid_gas_and_solute_storage(self):self.run_case('cartridge')
    def test_saturation_and_finite_dissolution_with_solid_remaining(self):self.run_case('dissolution')
    def test_solid_exhaustion_preserves_dissolved_washout(self):self.run_case('washout')
    def test_mixed_tank_matches_independent_exponential(self):self.run_case('mixing')
    def test_startup_all_occupancies_and_independent_balances(self):self.run_case('startup')
    def test_acid_concentration_step_and_bag_depletion(self):self.run_case('acid_step')
    def test_delayed_stale_invalid_sensors_and_control_input_boundary(self):self.run_case('sensors')
    def test_pi_saturation_antiwindup_and_invalid_freeze(self):self.run_case('pi')
    def test_compensating_errors_and_continuous_dwell(self):self.run_case('qualification')
    def test_pressure_stop_and_bounded_startup_failures(self):self.run_case('faults')
    def test_time_refinement_against_predeclared_budget(self):self.run_case('refinement')
    def test_eight_hours_depletion_and_boundary_balances(self):self.run_case('endurance')

    def configuration(self,mode):
        c=json.loads((ROOT/'scenarios/preparation_hd.json').read_text())
        c['workflow']=[];c['treatment'].update(mode=mode,replacement_mL_min=0 if mode=='HD' else 60)
        return c

    def cycle(self,mode,inject=False):
        c=self.configuration(mode);validate(c)
        process=subprocess.Popen([str(self.directory/'plant')],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        def call(role,*fields):
            process.stdin.write(str(role)+' DL1 '+' '.join(str(x) for x in fields)+'\n');process.stdin.flush()
            line=process.stdout.readline().strip().split()
            self.assertTrue(line and line[0]=='DL1',line);self.assertNotIn('DRIVER_ERROR',line)
            return line[1:]
        stage='SELF_TEST';snapshot=None;stages=set();treatment_ticks=0;first_ready=None;fault_tick=None;peak_residual=0
        try:
            with patch.object(circuit,'rpc',side_effect=call),patch.object(treatment,'rpc',side_effect=call),patch.object(machine,'rpc',side_effect=call),patch.object(physical,'rpc',side_effect=call):
                circuit.configure(0,c);treatment.configure(0,c);machine.configure(0,c)
                patient=Compartments(physical.patient_configuration(c),online=True,lifecycle=True)
                for n in range(2200):
                    if snapshot:physical.update_blood(0,snapshot)
                    if inject and treatment_ticks==10 and fault_tick is None:
                        expect(call(0,'PREPFAULT11','sensor_invalid',1),'OK',1);fault_tick=n
                    expect(call(0,'PREPARE',n,n*500,500,.5,'none','none'),'OK',1)
                    view=machine.view([*call(1,'VIEW5'),'INTENT5','0','none','none'])
                    self.assertIn('preparation_ready',view['observation'])
                    action={'PREPARATION':'PRIME','CONFIGURATION':'CONNECT','CONNECTED':'START','FINISHED':'RETURN','DISCONNECTING':'DISCONNECT','DISCONNECTED':'CLEAN'}.get(stage)
                    if action:expect(call(1,'CHANGE5',n,n*500,action),'OK',1)
                    if fault_tick is not None:
                        # Deliberately lie through both normal decision interfaces.
                        expect(call(1,'DEMAND5',n,n*500,300,65,60),'OK',1)
                        expect(call(2,'PROTECT5',n,n*500,0,1),'OK',1)
                    else:expect(call(3,n,n*500),'OK',1)
                    r=machine.committed(call(0,'COMMIT5',n,n*500));m=r['machine'];g=m['guided'];h=r['circuit'];o=r['online'];p=r['physical']['preparation']
                    stage=m['stage'];stages.add(stage)
                    peak_residual=max(peak_residual,abs(p['water_residual_mL']),abs(p['cartridge_gas_residual_mL']),abs(p['line_gas_residual_mL']),*[abs(x) for x in p['mass_residual_mmol']])
                    self.assertLessEqual(peak_residual,1e-6)
                    if p['ready'] and first_ready is None:first_ready=(n+1)*.5
                    if first_ready is None:
                        self.assertEqual(o['pre_tick_mL']+o['post_tick_mL']+m['flush_in_tick_mL'],0)
                        self.assertEqual(r['physical']['dynamics']['feed_mL_min'],0)
                    if fault_tick is not None:
                        self.assertEqual(o['pre_tick_mL']+o['post_tick_mL']+h['uf_tick_mL'],0)
                        self.assertEqual(r['physical']['dynamics']['feed_mL_min'],0)
                        self.assertNotEqual(m['alarm_mask'],0)
                        if n>=fault_tick+3:break
                    else:self.assertEqual(m['alarm_mask'],0,(n,m,p))
                    rinse=bool(g['return_in_tick_mL'] or g['return_out_tick_mL'])
                    q=dict(sequence=n,time_ms=n*500,dt_ms=500,draw_mL=h['draw_tick_mL']-m['flush_in_tick_mL'],return_mL=h['return_tick_mL']-m['flush_out_tick_mL'],uf_mL=h['uf_tick_mL'],stored_mL=h['stored_mL'],clearance_mL_min=h['clearance_mL_min'],sieving=c['circuit']['profile']['sieving'],dialysate_mmol_L=o['concentration_mmol_L'],pre_mL=o['pre_tick_mL'],post_mL=o['post_tick_mL'],substitution_mmol_L=o['concentration_mmol_L'],flush_in_mL=m['flush_in_tick_mL'],flush_out_mL=m['flush_out_tick_mL'],flush_mmol_L=[0,154,0,154,0,0] if rinse else o['concentration_mmol_L'],rinseback=rinse)
                    physical.attach_transaction(q,r,c);snapshot=patient.advance(q)
                    self.assertTrue(all(abs(x)<1e-6 for x in snapshot['mass_residual_mmol']))
                    if g['integrated_stage']=='TREATMENT':treatment_ticks+=1
                    if stage=='CLEANED':break
                self.assertIsNotNone(first_ready);self.assertLessEqual(first_ready,600)
                if inject:self.assertIsNotNone(fault_tick)
                else:self.assertEqual(stage,'CLEANED',stages);self.assertEqual(treatment_ticks,120)
                folder=os.environ.get('DIALYSISLAB_PREPARATION_CAPTURE')
                if folder:(Path(folder)/(mode+('-fault' if inject else '')+'.json')).write_text(json.dumps(dict(mode=mode,fault=inject,first_ready_s=first_ready,stages=sorted(stages),treatment_ticks=treatment_ticks,peak_balance_residual=peak_residual,configuration=c),indent=2)+'\n')
        finally:
            process.stdin.close();process.wait(timeout=5);process.stdout.close();errors=process.stderr.read();process.stderr.close()
        self.assertEqual(process.returncode,0,errors)

    def test_actual_hd_pre_post_startup_and_complete_patient_cycles(self):
        for mode in ('HD','HDF_PRE','HDF_POST'):
            with self.subTest(mode=mode):self.cycle(mode)

    def test_final_authority_blocks_unqualified_fluid_despite_forged_permits(self):self.cycle('HDF_POST',True)

    def test_configuration_and_wire_reject_malformed_inputs(self):
        c=self.configuration('HD');validate(c)
        for key,value in [('step_s',0),('sensor_latency_s',.6),('initial_line_occupancy',1.5),('cartridge_target_mL',119)]:
            bad=copy.deepcopy(c);bad['physical']['preparation'][key]=value
            with self.assertRaises(ValueError):validate(bad)
        with self.assertRaises(ValueError):physical.state(['PHYSICS9','PREPARATION11','0'])

    def test_evidence_identity_changes_with_source_and_configuration(self):
        sys.path.insert(0,str(ROOT/'tools'))
        from verify_preparation import inputs,applicable
        report=dict(schema_version=1,source_sha256=inputs(),successful=True,tests_run=1,cases=[dict(result='passed')])
        self.assertTrue(applicable(report))
        for path in ('src/preparation.hpp','scenarios/preparation_hd.json','docs/testing/PREPARATION.md'):
            bad=copy.deepcopy(report);bad['source_sha256'][path]='0'*64
            self.assertFalse(applicable(bad))
        for changes in (dict(successful=False),dict(cases=[]),dict(cases=[dict(result='skipped')])):
            bad=dict(report,**changes);self.assertFalse(applicable(bad))


if __name__=='__main__':unittest.main()
