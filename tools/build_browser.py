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
    parser=argparse.ArgumentParser();parser.add_argument('--emsdk',type=Path,required=True);parser.add_argument('--cmake',default='cmake');parser.add_argument('--offline',action='store_true');args=parser.parse_args()
    os.chdir(ROOT);sdk=args.emsdk.resolve();em=sdk/'upstream/emscripten'
    version=subprocess.check_output([str(em/'emcc'),'--version'],text=True)
    if '4.0.15' not in version:raise ValueError('Emscripten 4.0.15 required')
    lock=json.loads((ROOT/'browser_dependencies.json').read_text());out=ROOT/'build/browser';out.mkdir(parents=True,exist_ok=True)
    for name,item in lock['pyodide']['artifacts'].items():
        target=out/'vendor/pyodide'/name;target.parent.mkdir(parents=True,exist_ok=True)
        if not target.exists() or digest(target)!=item['sha256']:
            if args.offline:raise ValueError('Missing or changed runtime: '+name)
            raw=urllib.request.urlopen(item['url'],timeout=120).read()
            if hashlib.sha256(raw).hexdigest()!=item['sha256']:raise ValueError('Runtime integrity: '+name)
            target.write_bytes(raw)
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
    paths += [ROOT/'browser_dependencies.json',ROOT/'tools/build_browser.py',ROOT/'scenarios/preparation_hd.json']
    inputs={str(p.relative_to(ROOT)):digest(p) for p in sorted(paths)}
    identity=dict(source_revision=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),dirty=bool(subprocess.check_output(['git','status','--porcelain'],text=True)),source_input_sha256=hashlib.sha256(json.dumps(inputs,sort_keys=True).encode()).hexdigest(),source_sha256=inputs,emscripten='4.0.15',pyodide='0.27.7',dependency_lock_sha256=digest(ROOT/'browser_dependencies.json'))
    identity['artifacts']={str(p.relative_to(out)):digest(p) for p in sorted(out.rglob('*')) if p.is_file() and p.name!='build-identity.json'}
    (out/'build-identity.json').write_text(json.dumps(identity,indent=2)+'\n')
    print('Built static candidate at build/browser; serve over HTTP. No computation backend.')
if __name__=='__main__':main()
