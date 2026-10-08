"""Own SDL/ImGui event harness, actual broker/services/rendered output."""
import json
import os
from pathlib import Path
import queue
import shutil
import subprocess
import sys
import threading
import time
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tests'))
from test_experiments import Fixture, wait_for
BUILD=Path(os.environ.get('DIALYSISLAB_GUI_BUILD_DIR',ROOT/'build/gui'))
EVIDENCE=Path(os.environ.get('DIALYSISLAB_CONSOLE_EVIDENCE',ROOT/'build/console-tests'))
GRAPHICAL=os.environ.get('DIALYSISLAB_CONSOLE_GRAPHICAL')=='1'


class Console:
    def __init__(self, api, output, command=None):
        output.mkdir(parents=True,exist_ok=False);self.output=output;self.queue=queue.Queue();self.lines=[];self.inputs=[]
        if command is None:
            command=[str(BUILD/'sim-console'),'--api-dir',str(api),'--capture-dir',str(output),'--test-input']
            if not GRAPHICAL:command+=['--headless']
        self.process=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,bufsize=1)
        def receive():
            for line in self.process.stdout:self.lines.append(line);self.queue.put(line)
        self.thread=threading.Thread(target=receive);self.thread.start()
    def send(self,text):
        self.inputs.append(text);self.process.stdin.write(text+'\n');self.process.stdin.flush()
    def snapshot(self):
        self.send('SNAPSHOT');deadline=time.monotonic()+3
        while time.monotonic()<deadline:
            try:line=self.queue.get(timeout=.2)
            except queue.Empty:
                if self.process.poll() is not None:raise AssertionError('console exited: '+''.join(self.lines))
                continue
            if line.startswith('SNAPSHOT '):return json.loads(line[9:])
        raise AssertionError('no snapshot: '+''.join(self.lines)[-2000:])
    def click(self,name):
        # The command adds ImGui mouse position/down/up events across rendered frames;
        # application callbacks are not invoked directly by the harness.
        self.send('CLICK '+name);time.sleep(.15)
    def set(self,name,value):self.send('SET '+name+' '+str(value).encode().hex())
    def capture(self,name):
        self.send('CAPTURE '+name)
        wait_for(lambda:(self.output/(name+'.ppm')).is_file())
    def close(self):
        if self.process.poll() is None:self.send('QUIT')
        self.process.wait(timeout=8);self.thread.join(timeout=2)
        self.process.stdin.close();self.process.stdout.close()
        (self.output/'output.log').write_text(''.join(self.lines));(self.output/'input.log').write_text('\n'.join(self.inputs)+'\n')
        if self.process.returncode!=0:raise AssertionError('console return '+str(self.process.returncode)+': '+''.join(self.lines))
        if any(s in ''.join(self.lines) for s in ('AddressSanitizer','LeakSanitizer','runtime error:')):raise AssertionError('sanitizer diagnostics')


class ConsoleTests(unittest.TestCase):
    def test_real_widgets_configure_pause_replay_compare_and_export(self):
        with Fixture() as f:
            ui=Console(f.root/'api',EVIDENCE/'workflow')
            try:
                wait_for(ui.snapshot,lambda s:s['connected'])
                ui.set('preset','machine_hdf_post');ui.click('LOAD')
                wait_for(lambda:f.call('DRAFT'),lambda c:c['treatment']['mode']=='HDF_POST')
                ui.set('speed',20);ui.click('START')
                started=wait_for(ui.snapshot,lambda s:s['state']=='running' and s['sequence']>=5)
                original=started['run_id'];ui.click('PAUSE')
                paused=wait_for(ui.snapshot,lambda s:s['state']=='paused')
                ui.capture('paused-truth');time.sleep(2.2)
                self.assertEqual(ui.snapshot()['sequence'],paused['sequence'])
                ui.click('RESUME');finished=wait_for(ui.snapshot,lambda s:s['state']=='completed',timeout=20)
                self.assertEqual(finished['sequence'],399)
                ui.capture('completed')
                ui.set('speed',0);ui.click('REPLAY')
                wait_for(ui.snapshot,lambda s:s['run_id']!=original and s['state']=='completed',timeout=20)
                ui.click('COMPARE')
                comparison=wait_for(lambda:f.call('STATUS')['job'],lambda j:j['state']=='completed')
                self.assertTrue(comparison['result']['exact_replay'],comparison)
                ui.click('EXPORT')
                exported=wait_for(lambda:f.call('STATUS')['job'],lambda j:j.get('operation')=='EXPORT' and j['state']=='completed')
                self.assertTrue((f.root/'runs'/exported['result']['file']).is_file())
                ui.click('RUNS');ui.capture('comparison-export')
                shutil.copytree(f.root/'runs',EVIDENCE/'workflow-results',ignore=shutil.ignore_patterns('*.zip','.broker.lock'))
            finally:ui.close()

    def test_stale_editor_cannot_overwrite_another_clients_configuration(self):
        with Fixture() as f:
            ui=Console(f.root/'api',EVIDENCE/'stale-editor')
            try:
                wait_for(ui.snapshot,lambda s:s['connected']);ui.click('DRAFT')
                original=wait_for(ui.snapshot,lambda s:s['revision']==1)
                old=f.call('DRAFT')
                f.configure('machine_hdf_post')
                time.sleep(.5)
                self.assertEqual(ui.snapshot()['revision'],original['revision'])
                ui.set('configuration',json.dumps(old));ui.click('VALIDATE')
                wait_for(ui.snapshot,lambda s:'stale draft revision' in s['feedback'])
                self.assertEqual(f.call('DRAFT')['treatment']['mode'],'HDF_POST')
                self.assertEqual(f.call('RUNS'),[])
            finally:ui.close()

    def test_invalid_draft_disconnect_and_reconnect_do_not_start_hidden_run(self):
        with Fixture() as f:
            ui=Console(f.root/'api',EVIDENCE/'invalid-reconnect')
            try:
                wait_for(ui.snapshot,lambda s:s['connected']);ui.click('DRAFT')
                ui.set('configuration','{"schema_version":5,"model":"bad"}');ui.click('VALIDATE')
                wait_for(ui.snapshot,lambda s:'ERROR' in s['feedback'] or 'error' in s['feedback'])
                self.assertEqual(f.call('RUNS'),[])
                f.server.shutdown();f.thread.join();f.server.server_close()
                disconnected=wait_for(ui.snapshot,lambda s:not s['connected']);self.assertEqual(disconnected['state'],'disconnected')
                from dialysislab.experiments import Server
                f.server=Server(f.root/'api',f.broker);f.thread=threading.Thread(target=f.server.serve_forever,kwargs=dict(poll_interval=.02));f.thread.start()
                wait_for(ui.snapshot,lambda s:s['connected']);self.assertEqual(f.call('RUNS'),[])
                ui.capture('reconnected')
            finally:ui.close()


if __name__=='__main__':unittest.main()
