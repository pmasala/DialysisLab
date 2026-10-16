"""Current animated UI regressions; synthetic fixtures, not clinical validation."""
import os
import json
import sys
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
BUILD=Path(os.environ.get('DIALYSISLAB_GUI_BUILD_DIR',os.environ.get('DIALYSISLAB_BUILD_DIR',ROOT/'build/gui'))).resolve()

class SynopticTests(unittest.TestCase):
    def test_post_tracer_enters_venous_chamber_before_return(self):
        # Independent scalar mixing oracle; this is not bubble-trap validation.
        sys.path.insert(0,str(ROOT/'python'))
        from dialysislab import physical
        from dialysislab.compartments import Compartments
        config=physical.patient_configuration(json.loads((ROOT/'scenarios/device_guided.json').read_text()))
        for row in config['concentration_mmol_L']:row[0]=0
        config['generation_mmol_min'][0]=0
        config['exchange_mL_min'][0]=0
        config['external_in_mL_min']=config['external_out_mL_min']=config['refill_mL_min']=0
        patient=Compartments(config,True,True)
        volumes=config['extracorporeal']['volumes_mL']
        q=dict(sequence=0,time_ms=0,dt_ms=1000,draw_mL=0,return_mL=0,uf_mL=0,stored_mL=0,
            clearance_mL_min=[0]*6,sieving=[1]*6,dialysate_mmol_L=[0]*6,pre_mL=0,post_mL=1,
            substitution_mmol_L=[1,0,0,0,0,0],flush_in_mL=0,flush_out_mL=0,flush_mmol_L=[0]*6,rinseback=False,
            distributed=dict(volumes_mL=volumes,filtration_mL=[0]*12,dialysate_mL_min=0,
                dialysate_storage_mL=0,dialysate_drain_mL_min=0,membrane_open=False))
        result=patient.advance(q);cells=result['distributed']['compartments']
        self.assertEqual(cells[14]['name'],'venous_chamber')
        for cell in cells[:14]:self.assertEqual(cell['concentration_mmol_L'][0],0)
        chamber=1/(volumes[14]+1)
        tube=chamber/(volumes[15]+1)
        self.assertAlmostEqual(cells[14]['concentration_mmol_L'][0],chamber,delta=1e-12)
        self.assertAlmostEqual(cells[15]['concentration_mmol_L'][0],tube,delta=1e-12)
        self.assertGreater(chamber,tube)
        self.assertLess(abs(result['mass_residual_mmol'][0]),1e-6)

    def test_motion_freshness_routes_and_inventory(self):
        with tempfile.TemporaryDirectory() as tmp:
            binary=Path(tmp)/'motion'
            subprocess.run(['g++','-std=c++17','-O1','-Wall','-Wextra','-Werror','-I'+str(ROOT/'src'),str(ROOT/'tests/synoptic_motion.cpp'),'-o',str(binary)],check=True,capture_output=True,text=True,timeout=60)
            result=subprocess.run([str(binary)],capture_output=True,text=True,timeout=10)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)

    def test_actual_lvgl_modes_responsive_touch_and_stale(self):
        library=BUILD/'gui-lvgl/liblvgl.a'
        if not library.exists():self.skipTest('actual GUI build unavailable')
        deps=ROOT/'build/gui-deps/lvgl-9.6.0'
        with tempfile.TemporaryDirectory() as tmp:
            binary=Path(tmp)/'synoptic'
            command=['g++','-std=c++17','-O1','-Wall','-Wextra','-Werror','-I'+str(ROOT/'src'),'-I'+str(deps/'include'),'-I'+str(deps),'-I'+str(ROOT/'src/ui'),'-DLV_CONF_PATH="'+str(ROOT/'src/ui/lv_conf.h')+'"','-DLV_KCONFIG_IGNORE',str(ROOT/'tests/synoptic_view.cpp'),str(ROOT/'src/ui/font.cpp'),str(library),'-lm','-pthread','-o',str(binary)]
            if 'DIALYSISLAB_SANITIZE:BOOL=ON' in (BUILD/'CMakeCache.txt').read_text():command+=['-fsanitize=address,undefined','-fno-sanitize-recover=all','-fno-omit-frame-pointer']
            subprocess.run(command,check=True,capture_output=True,text=True,timeout=120)
            capture=os.environ.get('DIALYSISLAB_SYNOPTIC_CAPTURES')
            result=subprocess.run([str(binary)]+([capture] if capture else []),capture_output=True,text=True,timeout=30)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            self.assertIn('passed',result.stdout)

    def test_sdl_resize_finger_input_and_focus_cancellation(self):
        library=BUILD/'gui-lvgl/liblvgl.a';sdl=BUILD/'gui-sdl/libSDL2.a'
        if not library.exists() or not sdl.exists():self.skipTest('actual GUI build unavailable')
        deps=ROOT/'build/gui-deps/lvgl-9.6.0'
        with tempfile.TemporaryDirectory() as tmp:
            binary=Path(tmp)/'app'
            command=['g++','-std=c++17','-O1','-Wall','-Wextra','-Werror','-I'+str(ROOT/'src'),'-I'+str(deps/'include'),'-I'+str(deps),'-I'+str(ROOT/'src/ui'),'-I'+str(ROOT/'build/gui-deps/SDL2-2.32.10/include'),'-DLV_CONF_PATH="'+str(ROOT/'src/ui/lv_conf.h')+'"','-DLV_KCONFIG_IGNORE',str(ROOT/'tests/synoptic_app.cpp'),str(ROOT/'src/ui/font.cpp'),str(library),str(sdl),'-lm','-pthread','-o',str(binary)]
            if 'DIALYSISLAB_SANITIZE:BOOL=ON' in (BUILD/'CMakeCache.txt').read_text():command+=['-fsanitize=address,undefined','-fno-sanitize-recover=all','-fno-omit-frame-pointer']
            subprocess.run(command,check=True,capture_output=True,text=True,timeout=120)
            result=subprocess.run([str(binary),str(Path(tmp)/'services')],env=dict(os.environ,SDL_VIDEODRIVER='dummy'),capture_output=True,text=True,timeout=30)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            self.assertIn('passed',result.stdout)
