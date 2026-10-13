"""Executable closure of guided, interface and combined-arbitration audit cases."""
import copy
import itertools
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from audit_fixture import ROOT,Coupled,compile_driver
from dialysislab import physical,circuit,treatment,machine
from dialysislab.runner import validate
from dialysislab.compartments import Compartments


class AuditClosureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory();cls.addClassCleanup(cls.tmp.cleanup)
        cls.binary=compile_driver(cls.tmp.name)

    def test_complete_guided_state_guard_endpoint_and_hazard_mask_matrices(self):
        binary=Path(self.tmp.name)/'matrix'
        subprocess.run(['g++','-std=c++17','-O2','-Wall','-Wextra','-Werror','-I'+str(ROOT/'src'),str(ROOT/'tests/audit_machine.cpp'),'-o',str(binary)],check=True,capture_output=True,timeout=60)
        report=json.loads(subprocess.check_output([str(binary)],text=True,timeout=20))
        self.assertEqual(report['phase_action_guard_cases'],832)
        self.assertEqual(report['hazard_mask_state_cases'],131072)

    def test_dynamic_initial_volume_bounds_match_actual_plant_and_patient(self):
        original=json.loads((ROOT/'scenarios/device_guided.json').read_text())
        for volume in (50,1000):
            config=copy.deepcopy(original);config['physical']['dynamics']['dialysate_volume_mL']=volume
            validate(config);patient=Compartments(physical.patient_configuration(config),True,True)
            self.assertEqual(patient.snapshot()['distributed']['dialysate_volume_mL'],volume)
            fixture=Coupled(self.binary,config);fixture.close()
        for volume in (49,1001,2000):
            config=copy.deepcopy(original);config['physical']['dynamics']['dialysate_volume_mL']=volume
            with self.assertRaises(ValueError):validate(config)
            # Bypass Python validation only in this negative test to probe the actual plant parser.
            with patch.object(physical,'validate',return_value=config['physical']):
                with self.assertRaises(ValueError):Coupled(self.binary,config)

    def test_all_single_and_pair_hazards_defeat_hostile_control_in_active_phases(self):
        config=json.loads((ROOT/'scenarios/physical_hdf_post.json').read_text())
        config['guided']['treatment_ms']=3000
        fixture=Coupled(self.binary,config)
        states={};targets={'SELF_TEST','PRIMING','TREATMENT','RETURNING','CLEANING'}
        try:
            for _ in range(500):
                if fixture.stage in targets and fixture.stage not in states:
                    key=len(states);states[fixture.stage]=key;fixture.save(key)
                fixture.step()
                if fixture.stage=='CLEANED':break
            self.assertEqual(set(states),targets)
            masks=[1<<i for i in range(13)]+[(1<<i)|(1<<j) for i,j in itertools.combinations(range(13),2)]
            for stage,key in states.items():
                for mask in masks:
                    with self.subTest(stage=stage,mask=mask):
                        fixture.restore(key);r=fixture.step(mask=mask,auto=False)
                        self.assertEqual(r['machine']['alarm_mask'],mask)
                        self.assertEqual(r['uf_mL_min'],0)
                        self.assertEqual(r['online']['replacement_mL_min'],0)
                        if stage!='TREATMENT' or mask&4127:self.assertEqual(r['blood_mL_min'],0)
                        self.assertTrue(all(abs(x)<1e-6 for x in r['patient']['mass_residual_mmol']))
        finally:fixture.close()

    def test_each_freshness_fault_per_role_on_current_guided_model(self):
        config=json.loads((ROOT/'scenarios/physical_hd.json').read_text());fixture=Coupled(self.binary,config)
        try:
            for _ in range(200):
                fixture.step()
                if fixture.stage=='TREATMENT':break
            self.assertEqual(fixture.stage,'TREATMENT');fixture.save(0)
            for role in range(2):
                for fault in ('invalid','missing','stale','future','replay'):
                    with self.subTest(role=role,fault=fault):
                        fixture.restore(0);faults=['none','none'];faults[role]=fault
                        r=fixture.step(faults=faults,auto=False)
                        self.assertEqual(r['blood_mL_min'],0);self.assertEqual(r['uf_mL_min'],0)
                        if role==1:self.assertTrue(r['machine']['alarm_mask']&16)
        finally:fixture.close()


class GuidedPresetTests(unittest.TestCase):
    def test_catalog_default_and_loading_validate_complete_scheduled_guided_profiles(self):
        from dialysislab.experiments import Broker
        with tempfile.TemporaryDirectory() as directory:
            broker=Broker(ROOT/'build/gui',Path(directory)/'runs')
            try:
                self.assertIn('guided',broker.draft);self.assertTrue(broker.draft['workflow'])
                names=broker.dispatch('PRESETS',{})
                self.assertNotIn('device_guided',names)
                for name in ('physical_hd','physical_hdf_pre','physical_hdf_post'):
                    self.assertIn(name,names)
                    draft=broker.dispatch('LOAD',dict(name=name,revision=broker.revision))
                    validate(draft);self.assertIn('dynamics',draft['physical'])
                    self.assertEqual([e['action'] for e in draft['workflow']],['PRIME','CONNECT','START','RETURN','DISCONNECT','CLEAN'])
            finally:broker.close()

    def test_distributed_long_fixture_is_valid_and_has_no_early_return(self):
        import sys
        sys.path.insert(0,str(ROOT/'tools'))
        from verify_integrated import configurations
        cases=list(configurations('dynamic-long'));self.assertEqual(len(cases),1)
        _,c=cases[0];validate(c)
        self.assertEqual(c['ticks'],100000);self.assertEqual(c['dt_ms'],500)
        self.assertEqual([e['action'] for e in c['workflow']],['PRIME','CONNECT','START'])
        self.assertGreater(c['guided']['treatment_ms'],c['ticks']*c['dt_ms'])

    def test_dynamic_resource_retention_keeps_failed_run_evidence(self):
        import io,sys
        sys.path.insert(0,str(ROOT/'tools'))
        from retain_dynamic_resources import retain
        from ci_artifacts import recover
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);case=root/'integrated_dynamic_hdf_100000-1';case.mkdir()
            (case/'collection.json').write_text('{"compose_exit_code":1}')
            data=case/'results/run';data.mkdir(parents=True)
            (data/'manifest.json').write_text('{"outcome":"aborted"}')
            (root/'unrelated-private.txt').write_text('excluded')
            stream=io.StringIO();names=retain(root,stream)
            self.assertEqual(len(names),2);recover(io.StringIO(stream.getvalue()),root/'recovered')
            self.assertEqual((root/'recovered/dynamic-resources/integrated_dynamic_hdf_100000-1/results/run/manifest.json').read_text(),'{"outcome":"aborted"}')
            self.assertNotIn('excluded',stream.getvalue())
