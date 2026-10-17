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

    def session(self, *, interactive=False, mode="HD", ticks=None):
        p=subprocess.Popen([str(self.binary)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        def close():
            p.stdin.close();p.wait(timeout=10);p.stdout.close();p.stderr.close()
        self.addCleanup(close)
        def transport(role,frame):
            p.stdin.write(str(role)+' '+frame+'\n');p.stdin.flush();return p.stdout.readline().strip()
        c=json.loads((ROOT/'scenarios/preparation_hd.json').read_text());c['workflow']=[]
        c['treatment'].update(mode=mode,replacement_mL_min=0 if mode=='HD' else 60)
        if ticks is not None:c['ticks']=ticks
        return BrowserSession(c,transport,'0123456789abcdef0123456789abcdef',interactive=interactive)

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

    def test_delayed_manual_prime(self):
        for mode in ('HD', 'HDF_PRE', 'HDF_POST'):
            with self.subTest(mode=mode):
                s = self.session(interactive=True, mode=mode)
                for _ in range(2400):
                    r = s.step()
                    self.assertEqual(r['machine']['alarm_mask'], 0)
                self.assertGreater(s.n, s.config['ticks'])
                self.assertEqual(r['machine']['stage'], 'PREPARATION')
                self.assertEqual(r['time_ms'], 1200000)
                self.assertEqual(s.command(0, 'PRIME', s.epoch), 'queued')
                self.assertEqual(s.step()['machine']['stage'], 'PRIMING')
                self.assertEqual(json.loads(s.export())['execution_profile'], 'interactive')
                self.assertEqual(s.command(0, 'STOP', s.epoch), 'acknowledged')
                self.assertEqual(s.step()['machine']['stage'], 'STOPPED')

    def test_bounded_session_retains_tick_limit(self):
        s = self.session(ticks=3)
        for _ in range(3):s.step()
        with self.assertRaisesRegex(RuntimeError, 'configured tick limit reached'):
            s.step()
        self.assertEqual(s.n, 3)
        self.assertEqual(json.loads(s.export())['execution_profile'], 'bounded')

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
