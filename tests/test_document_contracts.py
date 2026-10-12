"""Protect document allocations and compare selected schemas with actual encoders."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'tools'), str(ROOT / 'python')]
import document_contracts
from dialysislab import machine, physical


class ContractRegisterTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for name in ('docs/design', 'assurance', 'tests'):
            (self.root / name).mkdir(parents=True)
        (self.root / 'tests/test_fixture.py').write_text('class Cases:\n    def test_exists(self): pass\n')
        (self.root / 'docs/design/a.md').write_text('Design')
        self.obligation = dict(id='ATOM-1', parent='REQ-001', statement='State', acceptance='Decision',
            design='docs/design/a.md', test='test_fixture.Cases.test_exists', coverage='Partial',
            approval='proposed; independent approval pending')
        self.wire = dict(sources=['docs/design/a.md'], messages=[dict(id='sample', tag='SAMPLE',
            endpoint='admin', direction='request', condition='fresh', reply='OK',
            fields=[dict(name='flow', type='real', unit='mL/min', bounds=[0,500])])])
        self.save()

    def save(self):
        def write(name, value):
            (self.root / name).write_text(json.dumps(value))
        write('docs/document-set.json', dict(contract_sources=['assurance/current-obligations.json','docs/wire-contract.json']))
        write('assurance/current-obligations.json', dict(obligations=[self.obligation]))
        self.wire['source_sha256']={p:hashlib.sha256((self.root/p).read_bytes()).hexdigest() for p in self.wire['sources']}
        write('docs/wire-contract.json', self.wire)

    def test_missing_method_cannot_be_accepted_as_coverage(self):
        self.obligation['test'] = 'test_fixture.Cases.test_missing'; self.save()
        with self.assertRaisesRegex(ValueError, 'missing executable'):
            document_contracts.render(self.root, ['REQ-001'])

    def test_source_edit_requires_contract_review(self):
        (self.root/'docs/design/a.md').write_text('Changed implementation')
        with self.assertRaisesRegex(ValueError, 'implementation changed'):
            document_contracts.render(self.root, ['REQ-001'])

    def test_unknown_parent_cannot_disappear_from_trace(self):
        with self.assertRaisesRegex(ValueError, 'unknown parent'):
            document_contracts.render(self.root, ['REQ-002'])

    def test_bad_wire_bounds_and_duplicate_fields_are_rejected(self):
        field = self.wire['messages'][0]['fields'][0]
        field['bounds'] = [500,0]; self.save()
        with self.assertRaisesRegex(ValueError, 'invalid wire bounds'):
            document_contracts.render(self.root, ['REQ-001'])
        field['bounds'] = [0,500]
        self.wire['messages'][0]['fields'].append(copy.deepcopy(field)); self.save()
        with self.assertRaisesRegex(ValueError, 'duplicate wire field'):
            document_contracts.render(self.root, ['REQ-001'])

    def test_unallocated_parent_and_partial_scope_remain_visible(self):
        rendered = document_contracts.render(self.root, ['REQ-001','REQ-002'])
        self.assertIn('REQ-002', rendered['docs/testing/COVERAGE.md'])
        self.assertIn('Partial', rendered['docs/testing/COVERAGE.md'])
        self.assertIn('independent approval pending', rendered['docs/ATOMIC_REQUIREMENTS.md'])


class WireWitnessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.tmp.cleanup)
        cls.binary = Path(cls.tmp.name) / 'wire'
        subprocess.run(['g++','-std=c++17','-O2','-Wall','-Wextra','-Werror',
            '-I'+str(ROOT/'src'),str(ROOT/'tests/wire_contract_witness.cpp'),'-o',str(cls.binary)],
            check=True, capture_output=True, timeout=60)
        cls.frames = subprocess.check_output([str(cls.binary)],text=True,timeout=10).splitlines()
        cls.schema = {m['id']:m for m in json.loads((ROOT/'docs/wire-contract.json').read_text())['messages']}

    def declared(self, ident, tokens):
        contract = self.schema[ident]
        self.assertEqual(tokens[0], contract['tag'])
        self.assertEqual(len(tokens)-1, len(contract['fields']))
        return dict(zip([f['name'] for f in contract['fields']], tokens[1:]))

    def test_actual_cpp_serializers_match_documented_positions_and_python_decoders(self):
        ids = ['machine-state5','machine-state8','observation5','observation8','observation9','observation10']
        for ident, frame in zip(ids, self.frames):
            with self.subTest(contract=ident):
                tokens = frame.split()[1:]
                fields = self.declared(ident,tokens)
                decoder = machine.metadata if ident.startswith('machine') else machine.observation
                decoded = decoder(tokens)
                self.assertEqual(decoded['sequence'],37); self.assertEqual(decoded['time_ms'],12345)
                if ident.startswith('machine'):
                    for key, value in dict(blood=311,net_uf=7,replacement=61,phase_flush=204,flush_in=205,
                        flush_out=206,expected_net=207,measured_net=208,flush_in_tick=2.1,flush_out_tick=2.2).items():
                        self.assertAlmostEqual(float(fields[key]),value)
                    if ident.endswith('8'):
                        self.assertEqual(decoded['guided']['integrated_stage'],'CONNECTED')
                        self.assertEqual(fields['test_duration'],'16000')
                        self.assertEqual(fields['clean_duration'],'17000')
                else:
                    for key,value in dict(blood_mL_min=311,pressure_mmHg=212,downstream_mmHg=92,air_signal=.1,leak_signal=.2).items():
                        self.assertAlmostEqual(float(fields[key]),value)
                        self.assertAlmostEqual(decoded[key],value)
                    if ident == 'observation10':
                        for key,value in dict(arterial_level=.41,venous_level=.62,dialysate_drain_mL_min=502,
                            uf_pump_mL_min=68,balance_position_mL=17,bypass=1,balance_capacity_mL=31,balance_phase=.75).items():
                            self.assertAlmostEqual(float(fields[key]),value)
                            self.assertAlmostEqual(decoded[key],value)

    def test_python_configuration_encoder_matches_documented_field_order(self):
        config=json.loads((ROOT/'scenarios/device_guided.json').read_text()); calls=[]
        def rpc(endpoint,*args): calls.append(list(args)); return ['OK']
        with patch.object(physical,'rpc',side_effect=rpc),patch.object(machine,'rpc',side_effect=rpc):
            machine.configure('admin',config)
        ids=['physical-request','fluid-request','dynamics-request','machine-request','guided-request']
        self.assertEqual(len(calls),len(ids))
        for ident,values in zip(ids,calls):
            with self.subTest(contract=ident):
                fields=self.declared(ident,values)
                if ident=='dynamics-request':self.assertEqual(fields,config['physical']['dynamics'])
                if ident=='guided-request':self.assertEqual(fields,config['guided'])
                if ident=='physical-request':
                    for key,value in config['physical']['blood'].items():self.assertEqual(fields[key],value)

    def test_documented_dynamic_parser_discrepancy_is_reproduced(self):
        # Diagnostic witness for DOC-13; passing this test does NOT approve the mismatch.
        tokens=self.frames[-1].split()
        fields=self.schema['observation10']['fields']
        pos=next(i for i,f in enumerate(fields) if f['name']=='arterial_level')+2
        tokens[pos]='1.5'
        cpp=subprocess.check_output([str(self.binary),'parse'],input=' '.join(tokens)+'\n',text=True,timeout=10)
        self.assertEqual(cpp.strip(),'rejected')
        self.assertEqual(machine.observation(tokens[1:])['arterial_level'],1.5)
