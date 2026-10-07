"""M4 independent balances, quality faults and direct actuator arbitration."""
import copy
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'python'))
sys.path.insert(0, str(ROOT / 'tools'))
from dialysislab import circuit, treatment
from dialysislab.compartments import Compartments
from dialysislab.protocol import rpc, ProtocolError
from dialysislab.runner import LocalCluster, simulate, validate
import dialysislab.runner as runner
import verify_models

BUILD = Path(os.environ.get('DIALYSISLAB_BUILD_DIR', ROOT / 'build'))


def config(name='hdf_post', ticks=100):
    c = json.loads((ROOT / ('scenarios/treatment_' + name + '.json')).read_text())
    c['ticks'] = ticks
    return c


class TreatmentTests(unittest.TestCase):
    def test_modes_independent_gross_net_water_and_solutes(self):
        outputs = {}
        for mode in ('hd', 'hdf_pre', 'hdf_post', 'hdf_large', 'hdf_imbalance'):
            c = config(mode)
            with LocalCluster(BUILD) as cluster, tempfile.TemporaryDirectory() as tmp:
                records, manifest = simulate(c, cluster.runtime, BUILD, Path(tmp) / 'run')
                self.assertEqual(manifest['outcome'], 'completed', manifest['errors'])
                verified = verify_models.verify(Path(tmp) / 'run', c, manifest['build']['source_sha256'])
                self.assertLess(verified['maximum_mass_error_mmol'], 1e-6)
                replacement = 0
                initial_mass = [math.fsum(c['patient']['volume_mL'][j] * c['patient']['concentration_mmol_L'][j][i] / 1000 for j in range(2))
                                + c['patient']['prime_mL'] * c['patient']['concentration_mmol_L'][0][i] / 1000 for i in range(6)]
                sub_mass, diff, conv = [0.0]*6, [0.0]*6, [0.0]*6
                for r in records:
                    o, p, physical = r['online'], r['patient'], r['circuit']
                    sub = o['pre_tick_mL'] + o['post_tick_mL']; replacement += sub
                    self.assertAlmostEqual(math.fsum(p['volume_mL']) + r['removed_total_mL'],
                                           c['patient_volume_mL'] + c['patient']['prime_mL'] + replacement, delta=1e-7)
                    self.assertAlmostEqual(p['net_patient_loss_mL'], r['removed_total_mL'] - replacement + physical['stored_mL'], delta=1e-7)
                    for i in range(6):
                        cc = p['concentration_mmol_L'][2][i]
                        sub_mass[i] += sub * o['concentration_mmol_L'][i] / 1000
                        diff[i] += physical['clearance_mL_min'][i] * c['dt_ms'] / 60000 * (cc-o['concentration_mmol_L'][i])/1000
                        conv[i] += physical['uf_tick_mL'] * c['circuit']['profile']['sieving'][i] * cc/1000
                        actual = math.fsum(row[i] for row in p['mass_mmol'])+diff[i]+conv[i]
                        expected = initial_mass[i]+sub_mass[i]+c['patient']['generation_mmol_min'][i]*r['time_ms']/60000
                        self.assertAlmostEqual(actual, expected, delta=1e-7)
                    self.assertEqual(o['post_tick_mL'] if mode == 'hdf_pre' else o['pre_tick_mL'], 0)
                outputs[mode] = records[-1]
        self.assertEqual(outputs['hd']['patient']['substitution_mL'], 0)
        self.assertGreater(outputs['hdf_post']['patient']['substitution_mL'], outputs['hdf_pre']['patient']['substitution_mL'])
        self.assertNotEqual(outputs['hdf_pre']['patient']['diffusive_mmol'][0], outputs['hdf_post']['patient']['diffusive_mmol'][0])

    def test_reservoir_analytic_mixing_temperature_and_filter_hydraulics(self):
        c = config(ticks=40)
        c['faults'] = [dict(tick=10,target='online:ratio',value=.041),dict(tick=10,target='online:temperature',value=38)]
        with LocalCluster(BUILD) as cluster:
            records, manifest = simulate(c, cluster.runtime, BUILD)
        self.assertEqual(manifest['outcome'], 'completed', manifest['errors'])
        prior_t, prior_c = 37, [0,140,4,105,24,2.4]
        for r in records:
            n,o = r['sequence'], r['online'];dt=c['dt_ms']/60000;v=50;q=560;k=30
            ratio, target = (.04,37) if n<10 else (.041,38)
            expected_t=(v*prior_t+dt*q*37+dt*v*k*target)/(v+dt*q+dt*v*k)
            expected_c=[(v*old+dt*q*ratio*stock)/(v+dt*q) for old,stock in zip(prior_c,c['treatment']['concentrate_mmol_L'])]
            self.assertAlmostEqual(o['temperature_C'],expected_t,delta=1e-12)
            for a,b in zip(o['concentration_mmol_L'],expected_c): self.assertAlmostEqual(a,b,delta=1e-10)
            expected_flow=60/(1+60*.5/600)
            self.assertAlmostEqual(o['replacement_mL_min'],expected_flow,delta=1e-10)
            self.assertAlmostEqual(o['filter1_pressure_mmHg'],expected_flow*.2,delta=1e-10)
            prior_t,prior_c=expected_t,expected_c

    def test_reservoir_first_order_convergence(self):
        errors=[]
        # Tiny safe ratio step; compare with the continuous mixed-tank exponential.
        for dt in (1000,500,250):
            c=config(ticks=2000//dt);c['dt_ms']=dt
            c['faults']=[dict(tick=0,target='online:ratio',value=.041)]
            with LocalCluster(BUILD) as cluster: records,manifest=simulate(c,cluster.runtime,BUILD)
            self.assertEqual(manifest['outcome'],'completed',manifest['errors'])
            actual=records[-1]['online']['concentration_mmol_L'][1]
            expected=143.5+(140-143.5)*math.exp(-560/50*2/60)
            errors.append(abs(actual-expected))
        self.assertGreater(errors[0]/errors[1],1.8);self.assertGreater(errors[1]/errors[2],1.8)

    def test_quality_faults_observation_bound_and_blood_specific_action(self):
        reasons={'temperature':'temperature','ratio':'composition','supply':'supply','integrity':'integrity','route':'route','filter1':'filter_pressure'}
        for name,reason in reasons.items():
            c=config(name,150)
            with self.subTest(name=name),LocalCluster(BUILD) as cluster:
                records,manifest=simulate(c,cluster.runtime,BUILD)
                self.assertEqual(manifest['outcome'],'completed',manifest['errors'])
                first=next(r for r in records if r['online']['quality_latched'])
                self.assertEqual(first['online']['reason'],reason)
                self.assertLessEqual(first['time_ms']-3000,10000+c['dt_ms'])
                observed=first['observations']['protection']
                if reason=='temperature': self.assertGreater(observed['temperature_C'],39)
                if reason=='composition': self.assertGreater(observed['conductivity_mS_cm'],16)
                for r in records:
                    if r['online']['quality_latched']:
                        self.assertEqual(r['uf_mL_min'],0);self.assertEqual(r['online']['replacement_mL_min'],0)
                        self.assertEqual(r['circuit']['clearance_mL_min'],[0]*6)
                        self.assertGreater(r['blood_mL_min'],0)
                        self.assertFalse(r['latched'])

    def test_quality_latch_cannot_be_overridden_by_conflicting_control(self):
        c=config('integrity',50)
        actual_rpc=runner.rpc
        with LocalCluster(BUILD) as cluster:
            def conflicting(path,*fields):
                if str(path).endswith('control/service.sock') and fields[0]=='STEP4':
                    # Bypass the cooperative control implementation; plant sees a hostile demand.
                    _,n,t,*_=fields
                    actual_rpc(cluster.runtime/'control/plant.sock','DEMAND4',n,t,300,20,120)
                    return ['OK']
                return actual_rpc(path,*fields)
            with patch('dialysislab.runner.rpc',side_effect=conflicting): records,manifest=simulate(c,cluster.runtime,BUILD)
        self.assertEqual(manifest['outcome'],'completed',manifest['errors'])
        for r in records:
            if r['sequence']>=30:
                self.assertEqual(r['online']['reason'],'integrity')
                self.assertEqual(r['online']['replacement_mL_min'],0);self.assertEqual(r['uf_mL_min'],0)
                self.assertGreater(r['blood_mL_min'],0)

    def test_hidden_contamination_is_not_a_protective_sensor(self):
        c=config('contaminant',100)
        with LocalCluster(BUILD) as cluster:
            records,manifest=simulate(c,cluster.runtime,BUILD)
            with self.assertRaises(ProtocolError): rpc(cluster.runtime/'protection/plant.sock','STATUS4')
        self.assertEqual(manifest['outcome'],'completed',manifest['errors'])
        self.assertGreater(records[-1]['online']['delivered_contaminant'],100)
        for r in records:
            self.assertFalse(r['online']['quality_latched'])
            self.assertFalse(r['latched'])
            self.assertNotIn('contaminant',json.dumps(r['observations']))
            self.assertGreater(r['online']['replacement_mL_min'],0)

    def test_hard_pressure_and_invalid_sensor_stop_all_treatment_outputs(self):
        for kind in ('occlusion', 'invalid'):
            c=config('hdf_pre',100)
            c['faults']=[dict(tick=30,target='edge:1',value=dict(resistance=.5,closed=True))] if kind=='occlusion' else [dict(tick=30,target='protection_sensor',value='invalid')]
            with self.subTest(kind=kind),LocalCluster(BUILD) as cluster:
                records,manifest=simulate(c,cluster.runtime,BUILD)
            self.assertEqual(manifest['outcome'],'completed',manifest['errors'])
            stopped=[r for r in records if r['latched']]
            self.assertTrue(stopped)
            self.assertLessEqual(stopped[0]['time_ms'],5000)
            self.assertEqual(stopped[0]['reason'],'pressure' if kind=='occlusion' else 'measurement')
            for r in stopped:
                self.assertEqual(r['blood_mL_min'],0);self.assertEqual(r['uf_mL_min'],0)
                self.assertEqual(r['online']['replacement_mL_min'],0)
                self.assertEqual(r['circuit']['clearance_mL_min'],[0]*6)

    def test_step_loss_halts_all_three_outputs_and_pending_tick(self):
        for role in ('control','protection'):
            c=config(ticks=10);actual_rpc=runner.rpc;calls=[]
            with self.subTest(role=role),LocalCluster(BUILD) as cluster:
                def lost(path,*fields):
                    calls.append((str(path),fields));response=actual_rpc(path,*fields)
                    if str(path).endswith(role+'/service.sock') and fields[:2]==('STEP4',5): raise TimeoutError('lost accepted STEP4 reply')
                    return response
                with patch('dialysislab.runner.rpc',side_effect=lost): records,manifest=simulate(c,cluster.runtime,BUILD)
                self.assertEqual(manifest['outcome'],'aborted');self.assertEqual(len(records),5)
                self.assertTrue(manifest['stop']['outputs_zero_observed'])
                self.assertEqual(manifest['stop']['observed_state']['online']['replacement_mL_min'],0)
                self.assertNotIn(('COMMIT4',5,500),[f for _,f in calls])
                with self.assertRaises(ProtocolError): actual_rpc(cluster.runtime/'admin/plant.sock','COMMIT4',5,500)

    def test_patient_replacement_ledger_and_atomic_rejection(self):
        patient=Compartments(config()['patient'],online=True)
        before=patient.snapshot()
        transaction=dict(sequence=0,time_ms=0,dt_ms=100,draw_mL=0,return_mL=0,uf_mL=0,stored_mL=0,
                         clearance_mL_min=[0]*6,sieving=[1]*6,dialysate_mmol_L=[0]*6,pre_mL=.1,post_mL=.1,substitution_mmol_L=[0,140,4,105,24,2.4])
        with self.assertRaises(ValueError): patient.advance(transaction)
        self.assertEqual(patient.snapshot(),before)
        transaction['pre_mL']=0
        state=patient.advance(transaction)
        self.assertAlmostEqual(state['substitution_mL'],.1,delta=1e-12)
        self.assertAlmostEqual(state['net_patient_loss_mL'],-.1,delta=1e-8)
        self.assertAlmostEqual(state['substitution_mmol'][1],.014,delta=1e-12)

    def test_reproducibility_and_configuration_rejection(self):
        hashes=[]
        for _ in range(2):
            with LocalCluster(BUILD) as cluster:
                _,manifest=simulate(config('hdf_pre',20),cluster.runtime,BUILD)
                self.assertEqual(manifest['outcome'],'completed',manifest['errors']);hashes.append(manifest['trajectory_sha256'])
        self.assertEqual(*hashes)
        for key,value in [('mode','HDF'),('replacement_mL_min',121),('ratio',1),('reservoir_mL',0)]:
            c=config();c['treatment'][key]=value
            with self.assertRaises(ValueError):validate(c)

if __name__=='__main__': unittest.main()
