"""Dependency identities, generated SBOM and advisory pagination regressions."""
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'));sys.path.insert(0,str(ROOT/'python'))
from dependency_report import check,application_bom,validate_image_application,BINARY_NAMES
from security_scan import query_osv
from dialysislab.runner import build_identity
BUILD=Path(os.environ.get('DIALYSISLAB_BUILD_DIR',ROOT/'build/gui'))


class DependencyTests(unittest.TestCase):
    def test_container_sbom_uses_actual_image_binary_and_runtime_identities(self):
        inventory=check(ROOT);identity=build_identity(BUILD);expected=identity['source_sha256']
        actual=dict(schema_version=1,build=identity,binary_sha256={name:hashlib.sha256(name.encode()).hexdigest() for name in BINARY_NAMES},
                    runtime_source_sha256={k:v for k,v in expected.items() if k.startswith(('python/dialysislab/','scenarios/')) or k=='gui_dependencies.json'})
        self.assertEqual(validate_image_application(actual,expected),identity)
        bom=application_bom(inventory,identity,binary_hashes=actual['binary_sha256'],runtime_hashes=actual['runtime_source_sha256'])
        indexed={c['bom-ref']:c for c in bom['components']}
        for name,sha in actual['binary_sha256'].items():self.assertEqual(indexed['binary:'+name]['hashes'][0]['content'],sha)
        for name,sha in actual['runtime_source_sha256'].items():
            if name.startswith('python/dialysislab/'):self.assertEqual(indexed['module:'+name]['hashes'][0]['content'],sha)
        for kind in ('stale-build','changed-runtime','changed-lock','missing-role','partial-gui'):
            modified=copy.deepcopy(actual)
            if kind=='stale-build':modified['build']['source_sha256']['src/plant.cpp']='0'*64
            elif kind=='changed-runtime':modified['runtime_source_sha256']['python/dialysislab/runner.py']='0'*64
            elif kind=='changed-lock':modified['runtime_source_sha256']['gui_dependencies.json']='0'*64
            elif kind=='missing-role':del modified['binary_sha256']['protection']
            else:del modified['binary_sha256']['sim-console']
            with self.subTest(kind=kind),self.assertRaises(ValueError):validate_image_application(modified,expected)
        core=copy.deepcopy(actual)
        for name in ('device-ui','sim-console'):del core['binary_sha256'][name]
        del core['runtime_source_sha256']['gui_dependencies.json']
        validate_image_application(core,expected)
        core_bom=application_bom(inventory,identity,binary_hashes=core['binary_sha256'],runtime_hashes=core['runtime_source_sha256'])
        self.assertFalse({x['name'] for x in inventory['application']}&{x['name'] for x in core_bom['components']})

    def test_inventory_rejects_changed_pins_notices_and_ci_actions(self):
        original=json.loads((ROOT/'dependency_inventory.json').read_text())
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            for name in set(original['reviewed_files'])|{'dependency_inventory.json','.github/workflows/verify.yaml','Dockerfile'}:
                target=root/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,target)
            self.assertEqual(check(root),original)
            for name,old,new in [('gui_dependencies.json','9.6.0','9.6.1'),
                ('.github/workflows/verify.yaml','git init .','git init .\n      - uses: unreviewed/action@main'),
                ('Dockerfile',original['container_profile']['base'],'python:latest'),
                ('docs/dependencies/GUI_NOTICES.md','MIT','unreviewed')]:
                with self.subTest(path=name):
                    path=root/name;before=path.read_text();self.assertIn(old,before)
                    path.write_text(before.replace(old,new))
                    with self.assertRaises(ValueError):check(root)
                    path.write_text(before)
            altered=copy.deepcopy(original);altered['application'][0]['license']='unknown'
            (root/'dependency_inventory.json').write_text(json.dumps(altered))
            with self.assertRaises(ValueError):check(root)

    def test_sbom_reproducible_and_actual_binary_hashes(self):
        inventory=check(ROOT);identity=build_identity(BUILD)
        a=application_bom(inventory,identity,BUILD);b=application_bom(inventory,identity,BUILD)
        self.assertEqual(json.dumps(a,sort_keys=True),json.dumps(b,sort_keys=True))
        self.assertEqual(a['specVersion'],'1.6')
        indexed={c['bom-ref']:c for c in a['components']}
        self.assertEqual(len(indexed),len(a['components']))
        for role in ('plant','control','protection','child-guard'):
            self.assertEqual(indexed['binary:'+role]['hashes'][0]['content'],hashlib.sha256((BUILD/role).read_bytes()).hexdigest())
        for relation in a['dependencies']:
            self.assertTrue(all(reference in indexed for reference in relation['dependsOn']))
        core=[d for d in a['dependencies'] if d['ref'] in ('binary:control','binary:protection','binary:plant')]
        self.assertTrue(all(not d['dependsOn'] for d in core))

    def test_advisory_pagination_preserves_all_findings(self):
        item=dict(component='synthetic',scopes=['test'],query={'commit':'a'*40})
        pages=[{'vulns':[{'id':'TEST-1','modified':'2026-01-01T00:00:00Z'}],'next_page_token':'next'},
               {'vulns':[{'id':'TEST-2','modified':'2026-01-02T00:00:00Z'}]}]
        with patch('security_scan.urllib.request.urlopen',side_effect=[io.BytesIO(json.dumps(p).encode()) for p in pages]) as call:
            result=query_osv(item)
        self.assertEqual(result['status'],'FINDINGS')
        self.assertEqual([v['id'] for v in result['findings']],['TEST-1','TEST-2'])
        self.assertEqual(json.loads(call.call_args_list[1].args[0].data)['page_token'],'next')

    def test_advisory_errors_and_repeated_pages_are_blocked(self):
        item=dict(component='synthetic',scopes=['test'],query={'commit':'a'*40})
        with patch('security_scan.urllib.request.urlopen',side_effect=OSError('TLS/network unavailable')):
            self.assertEqual(query_osv(item)['status'],'BLOCKED')
        with patch('security_scan.urllib.request.urlopen',side_effect=[io.BytesIO(b'{"next_page_token":"same"}') for _ in range(2)]):
            self.assertEqual(query_osv(item)['status'],'BLOCKED')


if __name__=='__main__':unittest.main()
