"""Native contracts for the browser-local transport; full Wasm campaign is separate."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'python'))
from dialysislab.browser import BrowserSession
from dialysislab import machine

class BrowserRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory();cls.addClassCleanup(cls.tmp.cleanup)
        cls.binary=Path(cls.tmp.name)/'engine'
        subprocess.run(['g++','-std=c++17','-O1','-Wall','-Wextra','-Werror',str(ROOT/'src/browser/engine.cpp'),'-o',str(cls.binary)],check=True,capture_output=True)

    def session(self):
        p=subprocess.Popen([str(self.binary)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        def close():
            p.stdin.close();p.wait(timeout=10);p.stdout.close();p.stderr.close()
        self.addCleanup(close)
        def transport(role,frame):
            p.stdin.write(str(role)+' '+frame+'\n');p.stdin.flush();return p.stdout.readline().strip()
        c=json.loads((ROOT/'scenarios/preparation_hd.json').read_text());c['workflow']=[]
        return BrowserSession(c,transport,'0123456789abcdef0123456789abcdef')

    def test_native_tick_stop_and_old_session(self):
        s=self.session()
        self.assertEqual(s.command(0,'STOP','f'*32),'rejected_old_session')
        for _ in range(3):record=s.step()
        self.assertEqual(record['time_ms'],1500)
        self.assertEqual(record['patient']['time_ms'],1500)
        self.assertEqual(s.command(0,'STOP',s.epoch),'acknowledged')
        view=machine.view(['VIEW5',*s.views()[0].split()[3:]])
        self.assertEqual(view['machine']['stage'],'STOPPED')

    def test_bad_sequence_stops_session_and_rejects_further_ticks(self):
        s=self.session();s.step();s.n=0
        with self.assertRaises(Exception):s.step()
        self.assertTrue(s.failed)
        with self.assertRaisesRegex(RuntimeError,'reset required'):s.step()

    @unittest.skipUnless(os.environ.get('DIALYSISLAB_BROWSER_ACCEPTANCE'), 'explicit browser build/runtime acceptance required')
    def test_full_wasm_portability(self):
        output=Path(os.environ['DIALYSISLAB_BROWSER_ACCEPTANCE'])/'portability';output.parent.mkdir(parents=True,exist_ok=True)
        result=subprocess.run([sys.executable,str(ROOT/'tools/verify_browser.py'),'--output',str(output)],cwd=ROOT,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=300)
        self.assertEqual(result.returncode,0,result.stdout)
        self.assertTrue(json.loads((output/'report.json').read_text())['successful'])

    @unittest.skipUnless(os.environ.get('DIALYSISLAB_BROWSER_ACCEPTANCE'), 'explicit Chromium/Wasm acceptance required')
    def test_real_browser_ui(self):
        output=Path(os.environ['DIALYSISLAB_BROWSER_ACCEPTANCE'])/'ui';output.parent.mkdir(parents=True,exist_ok=True)
        result=subprocess.run(['node',str(ROOT/'tests/browser/ui.cjs'),str(output)],cwd=ROOT,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=300)
        self.assertEqual(result.returncode,0,result.stdout)
        self.assertTrue(json.loads((output/'report.json').read_text())['passed'])
