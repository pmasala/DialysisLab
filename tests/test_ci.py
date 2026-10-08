"""CI error classification and exact, independently recoverable hosted evidence."""
import copy
import hashlib
import io
import json
from pathlib import Path
import sys
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from ci_artifacts import emit,recover,PREFIX
from ci_verify import release_result,software_success,dependency_reports,register_reports,retain
import ci_verify


class CITests(unittest.TestCase):
    def test_release_checker_crash_and_timeout_fail_actual_orchestration(self):
        for failure in ('crash','timeout','malformed'):
            with self.subTest(failure=failure),tempfile.TemporaryDirectory(dir=ROOT/'build') as tmp:
                output=Path(tmp)/'ci'
                def run(command,**kwargs):
                    stream=kwargs['stdout']
                    if '--release' in command and 'tools/check_traceability.py' in command:
                        if failure=='timeout':raise subprocess.TimeoutExpired(command,1200)
                        stream.write('Traceback: checker failed' if failure=='crash' else '{}')
                        return subprocess.CompletedProcess(command,2 if failure=='crash' else 1)
                    if '--release' in command:
                        stream.write(json.dumps(dict(structural_errors=[],open_checklist_entries=184,open_gaps=12)))
                        return subprocess.CompletedProcess(command,1)
                    if '--output' in command:
                        destination=Path(command[command.index('--output')+1])
                        if destination.suffix=='.json':destination.parent.mkdir(parents=True,exist_ok=True);destination.write_text('{}')
                        elif destination.suffix!='.zip':
                            destination.mkdir(parents=True,exist_ok=True)
                            names=[Path(name).name for name in dependency_reports(2)] if destination.name=='dependencies' else ['report.json','compose-results.json','integration.json']
                            for name in names:(destination/name).write_text('{}')
                    return subprocess.CompletedProcess(command,0)
                with patch.object(sys,'argv',['ci_verify.py','--output',str(output)]),patch('ci_verify.subprocess.check_output',return_value='a'*40),patch('ci_verify.subprocess.run',side_effect=run),patch('sys.stdout',io.StringIO()):
                    with self.assertRaises(SystemExit) as raised:ci_verify.main()
                self.assertEqual(raised.exception.code,1)
                report=json.loads((output/'ci-report.json').read_text())
                self.assertFalse(report['successful']);self.assertEqual(report['release_gate'],'CHECK_ERROR')
                self.assertEqual(next(s for s in report['steps'] if s['name']=='release-traceability')['status'],'FAIL')
                self.assertTrue(all(s['status']=='PASS' for s in report['steps'] if not s['name'].startswith('release-')))

    def test_only_valid_outstanding_release_obligations_are_exempt(self):
        fixtures=[('release-traceability',dict(structural_errors=[],release_gaps=['Human approval pending'],recorded_release_gate_passed=False)),
                  ('release-standards',dict(structural_errors=[],open_checklist_entries=184,open_gaps=12))]
        for name,value in fixtures:
            with self.subTest(name=name):
                self.assertEqual(release_result(name,1,json.dumps(value)),'BLOCKED')
                for code in (0,2,-9,124):
                    with self.assertRaises(ValueError):release_result(name,code,json.dumps(value))
                for raw in ('Traceback: crash','{}','null',json.dumps(dict(value,structural_errors=['broken link']))):
                    with self.assertRaises(ValueError):release_result(name,1,raw)
        passed=dict(structural_errors=[],release_gaps=[],recorded_release_gate_passed=True)
        self.assertEqual(release_result('release-traceability',0,json.dumps(passed)),'PASS')
        self.assertTrue(software_success([dict(name='release-traceability',status='BLOCKED',validated_release_obligations=True)]))
        for status in ('FAIL','BLOCKED'):
            self.assertFalse(software_success([dict(name='release-traceability',status=status)]))

    def test_exact_byte_retention_includes_every_sbom_and_platform_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);output=root/'ci';output.mkdir()
            expected={name:(' { "z" : 1, "a":"é", "file":'+json.dumps(name)+' }\r\n').encode()
                      for name in dependency_reports(2)}
            expected['native-tests.json']=b'{\n  "successful": true\n}\n'
            for name,raw in expected.items():
                path=output/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
            (output/'private-standard.txt').write_text('must never be retained')
            log=b'command output\r\n'+bytes(range(256))*40
            (output/'dependencies.log').write_bytes(log)
            report=dict(schema_version=2,steps=[dict(name='dependencies',log_sha256=hashlib.sha256(log).hexdigest())],public_reports=[],report_sha256={})
            register_reports(output,report,dependency_reports(2)+['native-tests.json'])
            (output/'ci-report.json').write_text(json.dumps(report,indent=2)+'\n')
            stream=io.StringIO();retain(output,report,stream)
            hosted=io.StringIO(''.join('2026-10-08T01:00:00Z '+line+'\n' for line in stream.getvalue().splitlines()))
            recovered=root/'recovered';headers=recover(hosted,recovered)
            expected.update({'commands/dependencies.log':log,'ci-report.json':(output/'ci-report.json').read_bytes()})
            self.assertEqual({p.name for p in recovered.glob('private*')},set())
            self.assertEqual({x['name'] for x in headers},set(expected))
            for name,raw in expected.items():
                self.assertEqual((recovered/name).read_bytes(),raw)
                self.assertEqual(next(x['sha256'] for x in headers if x['name']==name),hashlib.sha256(raw).hexdigest())
            (output/'native-tests.json').write_bytes(b'{}')
            with self.assertRaisesRegex(ValueError,'changed'):retain(output,report,io.StringIO())

    def test_corruption_order_truncation_and_path_escape_are_rejected(self):
        stream=io.StringIO();emit('report.json',b'x'*4000,stream=stream)
        lines=stream.getvalue().splitlines()
        variants=[lines[:-1],lines[:1]+[lines[2],lines[1]]+lines[3:],lines+lines]
        for index,kind in enumerate(('hash','path','length')):
            variant=lines.copy();header=json.loads(variant[0][len(PREFIX):])
            if kind=='hash':header['sha256']='0'*64
            elif kind=='path':header['name']='../escape'
            else:header['bytes']=16*1024*1024+1
            variant[0]=PREFIX+json.dumps(header);variants.append(variant)
        with tempfile.TemporaryDirectory() as tmp:
            for index,variant in enumerate(variants):
                with self.subTest(index=index),self.assertRaises(ValueError):
                    recover(io.StringIO('\n'.join(variant)),Path(tmp)/str(index))
            self.assertFalse((Path(tmp)/'escape').exists())
            self.assertTrue((Path(tmp)/'0/report.json.partial').is_file())


if __name__=='__main__':unittest.main()
