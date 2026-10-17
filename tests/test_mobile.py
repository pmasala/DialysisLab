"""Phone layout and fluid semantics: synthetic, no iPhone hardware or clinical claim."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
class MobileTests(unittest.TestCase):
    def test_fluid_quality_and_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            binary=Path(tmp)/'colors'
            subprocess.run(['g++','-std=c++17','-Wall','-Wextra','-Werror','-I'+str(ROOT/'src'),str(ROOT/'tests/mobile_colors.cpp'),'-o',str(binary)],check=True,capture_output=True,text=True)
            subprocess.run([str(binary)],check=True,capture_output=True,text=True)
    def test_lvgl_phone_layout(self):
        build=Path(os.environ.get('DIALYSISLAB_GUI_BUILD_DIR',ROOT/'build/gui'))
        library=build/'gui-lvgl/liblvgl.a'
        if not library.exists():self.skipTest('actual LVGL build required')
        deps=ROOT/'build/gui-deps/lvgl-9.6.0'
        with tempfile.TemporaryDirectory() as tmp:
            binary=Path(tmp)/'mobile'
            command=['g++','-std=c++17','-O1','-Wall','-Wextra','-Werror','-I'+str(ROOT/'src'),'-I'+str(deps/'include'),'-I'+str(deps),'-I'+str(ROOT/'src/ui'),'-DLV_CONF_PATH="'+str(ROOT/'src/ui/lv_conf.h')+'"','-DLV_KCONFIG_IGNORE',str(ROOT/'tests/mobile_view.cpp'),str(ROOT/'src/ui/font.cpp'),str(library),'-lm','-pthread','-o',str(binary)]
            compiled=subprocess.run(command,capture_output=True,text=True)
            self.assertEqual(compiled.returncode,0,compiled.stderr)
            capture=os.environ.get('DIALYSISLAB_MOBILE_CAPTURES','')
            result=subprocess.run([str(binary),capture],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)

    def test_sdl_mobile_window_dimensions(self):
        build=Path(os.environ.get('DIALYSISLAB_GUI_BUILD_DIR',ROOT/'build/gui'))
        if not (build/'gui-sdl/libSDL2.a').exists():self.skipTest('actual SDL build required')
        deps=ROOT/'build/gui-deps/lvgl-9.6.0'
        with tempfile.TemporaryDirectory() as tmp:
            source=Path(tmp)/'window.cpp';binary=Path(tmp)/'window'
            source.write_text('#define main device_ui_unused_main\n#include "'+str(ROOT/'src/ui/device_ui.cpp')+'"\n#undef main\n#include <cassert>\nint main(){SDL_setenv("SDL_VIDEODRIVER","dummy",1);App app("/tmp/dialysislab-mobile-test",false,"");for(int w:{320,390,430,844}){int h=w<700?2320:890,x=0,y=0;SDL_SetWindowSize(app.window,w,h);app.resize(w,h);app.events();SDL_GetWindowSize(app.window,&x,&y);assert(x==w&&y==h);assert(app.width==w&&app.height==h);}}')
            includes=[ROOT/'src',ROOT/'src/ui',deps,deps/'include',build/'gui-sdl/include',build/'gui-sdl/include/SDL2',build/'gui-sdl/include-config-release/SDL2']
            command=['g++','-std=c++17','-O1']+['-I'+str(p) for p in includes]+['-DLV_CONF_PATH="'+str(ROOT/'src/ui/lv_conf.h')+'"','-DLV_KCONFIG_IGNORE',str(source),str(ROOT/'src/ui/font.cpp'),str(build/'gui-lvgl/liblvgl.a'),str(build/'gui-sdl/libSDL2.a'),'-lm','-pthread','-o',str(binary)]
            result=subprocess.run(command,capture_output=True,text=True);self.assertEqual(result.returncode,0,result.stderr)
            result=subprocess.run([str(binary)],capture_output=True,text=True);self.assertEqual(result.returncode,0,result.stdout+result.stderr)
