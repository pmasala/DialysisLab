"""Current animated UI regressions; synthetic fixtures, not clinical validation."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
BUILD=Path(os.environ.get('DIALYSISLAB_GUI_BUILD_DIR',os.environ.get('DIALYSISLAB_BUILD_DIR',ROOT/'build/gui'))).resolve()

class SynopticTests(unittest.TestCase):
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
