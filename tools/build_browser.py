#!/usr/bin/env python3
"""Build a local-only browser candidate; downloads are pinned and hash-checked."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import urllib.request
ROOT=Path(__file__).resolve().parents[1]
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    parser=argparse.ArgumentParser()
    compiler=parser.add_mutually_exclusive_group(required=True)
    compiler.add_argument('--emsdk',type=Path)
    compiler.add_argument('--reuse-compiled',type=Path,help='Verified prior build for scripting-only changes')
    parser.add_argument('--cmake',default='cmake');parser.add_argument('--offline',action='store_true');args=parser.parse_args()
    os.chdir(ROOT)
    lock=json.loads((ROOT/'browser_dependencies.json').read_text());out=ROOT/'build/browser';out.mkdir(parents=True,exist_ok=True)
    reused=None
    if args.reuse_compiled:
        base=args.reuse_compiled.resolve()
        if base == out.resolve():raise ValueError('Reuse source must be separate from output')
        previous=json.loads((base/'build-identity.json').read_text())
        compiled_inputs={str(p.relative_to(ROOT)):digest(p) for folder in ('src','cmake/browser') for p in (ROOT/folder).rglob('*') if p.is_file()}
        recorded={p:sha for p,sha in previous['source_sha256'].items() if p.startswith(('src/','cmake/browser/'))}
        if compiled_inputs != recorded:raise ValueError('Compiled inputs changed; full rebuild required')
        if digest(ROOT/'browser_dependencies.json') != previous['dependency_lock_sha256']:raise ValueError('Runtime dependencies changed; rebuild required')
        # Older identities predate the explicit GUI lock hash; verify it at the recorded Git revision.
        old_gui=subprocess.check_output(['git','show',previous['source_revision']+':gui_dependencies.json'])
        if old_gui != (ROOT/'gui_dependencies.json').read_bytes():raise ValueError('GUI dependencies changed; rebuild required')
        for name,sha in previous['artifacts'].items():
            if digest(base/name) != sha:raise ValueError('Changed base artifact: '+name)
        if previous['emscripten'] != '4.0.15' or previous['pyodide'] != '0.27.7':raise ValueError('Base toolchain mismatch')
        for name in ['engine.js','engine.wasm','ui.js','ui.wasm']:
            if name not in previous['artifacts']:raise ValueError('Unrecorded compiled artifact: '+name)
            shutil.copy2(base/name,out/name)
        shutil.copytree(base/'vendor',out/'vendor',dirs_exist_ok=True)
        reused=dict(base_identity_sha256=digest(base/'build-identity.json'),base_source_revision=previous['source_revision'],compiled_artifacts={name:digest(out/name) for name in ['engine.js','engine.wasm','ui.js','ui.wasm']},gui_lock_sha256=digest(ROOT/'gui_dependencies.json'))
    for name,item in lock['pyodide']['artifacts'].items():
        target=out/'vendor/pyodide'/name;target.parent.mkdir(parents=True,exist_ok=True)
        if not target.exists() or digest(target)!=item['sha256']:
            if args.offline:raise ValueError('Missing or changed runtime: '+name)
            raw=urllib.request.urlopen(item['url'],timeout=120).read()
            if hashlib.sha256(raw).hexdigest()!=item['sha256']:raise ValueError('Runtime integrity: '+name)
            target.write_bytes(raw)
    if not args.reuse_compiled:
        sdk=args.emsdk.resolve();em=sdk/'upstream/emscripten'
        version=subprocess.check_output([str(em/'emcc'),'--version'],text=True)
        if '4.0.15' not in version:raise ValueError('Emscripten 4.0.15 required')
        subprocess.run(['python3','tools/fetch_gui.py','--cache','build/gui-deps','--offline'],check=True)
        subprocess.run([str(em/'emcmake'),args.cmake,'-S','cmake/browser','-B','build/browser-cmake','-DCMAKE_BUILD_TYPE=Release'],check=True)
        subprocess.run([args.cmake,'--build','build/browser-cmake','--parallel','4'],check=True)
    for p in (ROOT/'web').iterdir():
        if p.is_file():shutil.copy2(p,out/p.name)
    sources={p.name:p.read_text() for p in sorted((ROOT/'python/dialysislab').glob('*.py'))}
    (out/'python-sources.json').write_text(json.dumps(sources))
    shutil.copy2(ROOT/'scenarios/preparation_hd.json',out/'scenario.json')
    notices=out/'notices';notices.mkdir(exist_ok=True)
    for name in ['BROWSER_DEPENDENCIES.md','PYODIDE_LICENSE.md','CPYTHON_LICENSE.md','GUI_NOTICES.md','ROBOTO_NOTICE.md']:
        shutil.copy2(ROOT/'docs/dependencies'/name,notices/name)
    shutil.copy2(ROOT/'LICENSE',notices/'DIALYSISLAB_LICENSE.txt')
    paths=[p for base in ['src','python/dialysislab','web','cmake/browser'] for p in (ROOT/base).rglob('*') if p.is_file() and '__pycache__' not in str(p)]
    paths += [ROOT/'browser_dependencies.json',ROOT/'gui_dependencies.json',ROOT/'tools/build_browser.py',ROOT/'scenarios/preparation_hd.json']
    inputs={str(p.relative_to(ROOT)):digest(p) for p in sorted(paths)}
    identity=dict(source_revision=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),dirty=bool(subprocess.check_output(['git','status','--porcelain'],text=True)),source_input_sha256=hashlib.sha256(json.dumps(inputs,sort_keys=True).encode()).hexdigest(),source_sha256=inputs,emscripten='4.0.15',pyodide='0.27.7',dependency_lock_sha256=digest(ROOT/'browser_dependencies.json'))
    if reused:identity['reused_compilation']=reused
    identity['artifacts']={str(p.relative_to(out)):digest(p) for p in sorted(out.rglob('*')) if p.is_file() and p.name!='build-identity.json'}
    (out/'build-identity.json').write_text(json.dumps(identity,indent=2)+'\n')
    print('Built static candidate at build/browser; serve over HTTP. No computation backend.')
if __name__=='__main__':main()
