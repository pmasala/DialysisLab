"""Socket-independent parser/history regressions for the read-only inspector."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
BINARY = Path(os.environ.get('DIALYSISLAB_GUI_BUILD_DIR',
                            os.environ.get('DIALYSISLAB_BUILD_DIR', ROOT/'build/gui')))/'sim-console'


class InspectionTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which('g++'), 'C++ compiler unavailable')
    def test_nested_values_bounds_missing_samples_and_session_resets(self):
        source = r'''
#include "console/telemetry.hpp"
#include <cassert>
#include <iostream>
int main(){
    auto v=telemetry::Parser(R"({"truth":{"circuit":{"pressure_mmHg":[1.25,2]},"valid":false,"lost":null,"label":"a\\b"},"sequence":4})").parse();
    assert(v.numbers.at("truth.circuit.pressure_mmHg[0]")==1.25);
    assert(v.text.at("truth.valid")=="false");
    assert(!telemetry::get(v.numbers,"truth.lost"));
    for(const auto& bad: {std::string("{\"x\":1e999}"),std::string("{\"x\":01}"),std::string("{\"x\":1.}"),std::string("{} garbage"),std::string(262145,' '),std::string(34,'[')+"0"+std::string(34,']')}){
        bool rejected=false;try{telemetry::Parser(bad).parse();}catch(...){rejected=true;}assert(rejected);
    }
    telemetry::History h;
    for(int i=0;i<100000;++i)h.accept("epoch","run",i,i*.1,v);
    assert(h.samples.size()==telemetry::History::capacity);assert(h.samples.front().sequence==100000-telemetry::History::capacity);
    h.accept("epoch","run",99999,99999*.1,v);assert(h.samples.size()==telemetry::History::capacity);
    h.interrupt();h.accept("epoch","run",100000,10000,v);assert(h.samples.back().gap);
    h.accept("epoch","new-run",0,0,v);assert(h.samples.size()==1);
    h.accept("new-epoch","new-run",1,.1,v);assert(h.samples.size()==1);
    h.accept("new-epoch","new-run",0,0,v);assert(h.samples.size()==1);
    telemetry::Values large;for(int i=0;i<static_cast<int>(telemetry::History::max_metrics)+1;++i)large.numbers["truth."+std::to_string(i)]=i;
    bool rejected=false;try{h.accept("new-epoch","new-run",1,.1,large);}catch(...){rejected=true;}assert(rejected);
    assert(telemetry::unit("truth.online.conductivity_mS_cm")=="mS/cm");
    assert(telemetry::unit("truth.patient.concentration_mmol_L[0][2]")=="mmol/L");
    std::cout << "parser, bounded history, gaps, sessions and units passed\n";
}
'''
        with tempfile.TemporaryDirectory() as directory:
            cpp = Path(directory) / 'inspection.cpp'
            binary = Path(directory) / 'inspection'
            cpp.write_text(source)
            subprocess.run(['g++', '-std=c++17', '-Wall', '-Wextra', '-Werror', '-I', str(ROOT/'src'), str(cpp), '-o', str(binary)], check=True, capture_output=True)
            result = subprocess.run([str(binary)], check=True, capture_output=True, text=True, timeout=20)
            self.assertIn('passed', result.stdout)

    def test_recorded_console_is_read_only_and_hold_freezes_samples(self):
        import json
        import queue
        import threading
        import time
        binary = BINARY
        if not binary.exists():
            self.skipTest('GUI build unavailable')
        trajectory = next((ROOT/'assurance/evidence/m7').rglob('trajectory.jsonl'))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            # Use real retained simulation records, without starting or impersonating services.
            lines = trajectory.read_text().splitlines()[:30]
            recording = path/'recorded.jsonl'
            recording.write_text('\n'.join(lines)+'\n')
            process = subprocess.Popen([str(binary), '--headless', '--test-input', '--recorded', str(recording), '--capture-dir', str(path)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            messages = queue.Queue()
            thread = threading.Thread(target=lambda: [messages.put(line) for line in process.stdout], daemon=True)
            thread.start()
            def send(line):
                process.stdin.write(line+'\n');process.stdin.flush()
            def snapshot():
                send('SNAPSHOT')
                deadline = time.monotonic()+5
                while time.monotonic()<deadline:
                    line = messages.get(timeout=5)
                    if line.startswith('SNAPSHOT '):return json.loads(line[9:])
                raise AssertionError('no console snapshot')
            try:
                def wait_state(predicate):
                    deadline=time.monotonic()+5
                    while time.monotonic()<deadline:
                        state=snapshot()
                        if predicate(state):return state
                        time.sleep(.02)
                    raise AssertionError('console state timeout: '+str(state))
                def click(name):
                    wait_state(lambda s:name in s['widgets'])
                    send('CLICK '+name)
                    return wait_state(lambda s:s['pending_clicks']==0)
                first = wait_state(lambda s:s['telemetry_samples']>0)
                self.assertFalse(first['connected'])
                self.assertFalse(first['telemetry_live'])
                self.assertGreater(first['telemetry_samples'], 0)
                self.assertNotIn('START', first['widgets'])
                click('REPLAY_PAUSE')
                paused = wait_state(lambda s:s['state']=='recording paused');time.sleep(.4)
                self.assertEqual(snapshot()['sequence'], paused['sequence'])
                for tab, page in [('TAB_TRENDS',1),('TAB_INSPECT',2),('TAB_ADMIN',3),('TAB_LIVE',0)]:
                    click(tab)
                    self.assertEqual(snapshot()['page'],page)
                click('TAB_ADMIN');click('REPLAY')
                self.assertIn('read only', snapshot()['feedback'])
                click('REPLAY_PAUSE')
                self.assertGreater(wait_state(lambda s:s['sequence']>paused['sequence'])['sequence'],paused['sequence'])
            finally:
                send('QUIT');process.wait(timeout=5);thread.join(timeout=2)
                process.stdin.close();process.stdout.close()
            self.assertEqual(process.returncode,0)

    def test_history_controls_fit_and_receive_pointer_clicks_with_setup_open(self):
        from console_regressions import Console
        from test_experiments import wait_for
        import time
        if not BINARY.exists():
            self.skipTest('GUI build unavailable')
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            ui = Console(path/'absent-api', path/'captures', command=[
                str(BINARY), '--headless', '--test-input', '--api-dir', str(path/'absent-api'),
                '--capture-dir', str(path/'captures')])
            try:
                time.sleep(.5)
                ui.pointer_click('TAB_ADMIN')
                wait_for(ui.snapshot, lambda s: s['page']==3)
                for setup_open in (True, False):
                    with self.subTest(setup_open=setup_open):
                        ui.pointer_click('SETUP')
                        state = wait_for(ui.snapshot, lambda s: ('LOAD' in s['widgets'])==setup_open)
                        self.assertEqual('LOAD' in state['widgets'], setup_open)
                        for name in ('configuration', 'left', 'right', 'RUNS', 'REPLAY', 'COMPARE', 'EXPORT'):
                            x, y, width, height = state['widgets'][name]
                            self.assertGreaterEqual(x, 0, name)
                            self.assertGreaterEqual(y, 0, name)
                            self.assertLessEqual(x+width, 1440, name)
                            self.assertLessEqual(y+height, 960, name)
                        for name in ('REPLAY', 'COMPARE', 'EXPORT'):
                            ui.click(name)
                            wait_for(ui.snapshot, lambda s: s['last_action']==name, timeout=3)
                ui.capture('history-controls')
            finally:
                ui.close()
