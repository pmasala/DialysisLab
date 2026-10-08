#!/usr/bin/env python3
"""Reproduce the allowlisted source archive and build/test its extracted sources."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[1]


def sha(path):
    value=hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda:stream.read(65536),b''):value.update(chunk)
    return value.hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--deps-cache',type=Path,default=ROOT/'build/gui-deps')
    parser.add_argument('--xext-prefix',type=Path)
    parser.add_argument('--xext-library',type=Path)
    args=parser.parse_args();args.output=args.output.resolve()
    if args.output==ROOT or ROOT in args.output.parents:parser.error('package verification output must be outside repository')
    args.output.mkdir(parents=True,exist_ok=False)
    report=dict(schema_version=1,executed_at=datetime.now(timezone.utc).isoformat(),command=sys.argv,
                source_revision='unavailable',source_worktree_dirty=None,successful=False,steps=[])
    def run(name,command,cwd):
        log=args.output/(name+'.log');entry=dict(name=name,command=[str(x) for x in command],cwd=str(cwd));report['steps'].append(entry)
        with log.open('w') as stream:
            result=subprocess.run(entry['command'],cwd=cwd,env=dict(os.environ,SOURCE_REVISION='unavailable'),stdout=stream,stderr=subprocess.STDOUT,timeout=1200)
        entry.update(exit_code=result.returncode,log=str(log),log_sha256=sha(log))
        if result.returncode:raise RuntimeError(name+' failed: '+str(log))
    try:
        if (ROOT/'.git').exists():
            report['source_revision']=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
            report['source_worktree_dirty']=bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip())
        report['publication_manifest_sha256']=sha(ROOT/'publication_manifest.json')
        for index in (1,2):run('package-'+str(index),[sys.executable,ROOT/'tools/package_release.py','--output',args.output/('DialysisLab-'+str(index)+'.zip')],ROOT)
        one,two=[args.output/('DialysisLab-'+str(i)+'.zip') for i in (1,2)]
        if sha(one)!=sha(two):raise ValueError('source archive is not byte-reproducible')
        report['package_sha256']=sha(one);report['package_bytes']=one.stat().st_size
        with zipfile.ZipFile(one) as archive:
            expected={'DialysisLab/'+p for p in json.loads((ROOT/'publication_manifest.json').read_text())['files']}
            if set(archive.namelist())!=expected or len(archive.namelist())!=len(expected):raise ValueError('package differs from explicit allowlist')
            report['files']=sorted(expected);archive.extractall(args.output/'extracted')
        project=args.output/'extracted/DialysisLab';build=project/'build/gui'
        flags=['-DDIALYSISLAB_GUI=ON','-DDIALYSISLAB_GUI_DEPS='+str(args.deps_cache.resolve())]
        if args.xext_prefix:flags.append('-DDIALYSISLAB_XEXT_PREFIX='+str(args.xext_prefix.resolve()))
        if args.xext_library:flags.append('-DXEXT_LIB='+str(args.xext_library.resolve()))
        run('configure',['cmake','-S',project,'-B',build,'-DCMAKE_BUILD_TYPE=Release']+flags,project)
        run('build',['cmake','--build',build,'--parallel','3'],project)
        run('tests',[sys.executable,project/'tools/verify_m1.py','--build-dir',build,'--output',args.output/'tests.json'],project)
        for tool,label in [('verify_device_ui.py','device'),('verify_console.py','console')]:
            run(label,[sys.executable,project/'tools'/tool,'--build-dir',build,'--output',args.output/label],project)
        identity=json.loads((build/'build_identity.json').read_text())
        if identity['source_revision']!='unavailable':raise ValueError('extracted sources unexpectedly claim a Git revision')
        report['extracted_build']=identity
        report['actual_reports']={str(p.relative_to(args.output)):sha(p) for p in [args.output/'tests.json',args.output/'device/report.json',args.output/'console/report.json']}
        report['successful']=True
    except Exception as exc:
        report['error']=type(exc).__name__+': '+str(exc);raise
    finally:(args.output/'package-verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(successful=True,package_sha256=report['package_sha256'],files=len(report['files']))))


if __name__=='__main__':main()
