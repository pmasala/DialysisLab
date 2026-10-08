#!/usr/bin/env python3
"""Run bounded software CI and retain explicit reports; never approve release gates."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--report-only',action='store_true')
    args=parser.parse_args();output=args.output.resolve()
    if ROOT not in output.parents:parser.error('CI output must be within this checkout')
    report_path=output/'ci-report.json'
    if args.report_only:
        if not report_path.is_file():raise SystemExit('CI report missing; execution did not complete initialization')
        report=json.loads(report_path.read_text())
        # Explicit report filenames only: no environment dump, recursive source
        # upload, credentials, standards, images or arbitrary workspace archives.
        print('DIALYSISLAB_CI_REPORT_BEGIN\n'+report_path.read_text()+'DIALYSISLAB_CI_REPORT_END')
        for item in report['steps']:
            log=output/(item['name']+'.log')
            if log.is_file() and not log.is_symlink():
                raw=log.read_bytes()
                if len(raw)>1048576:
                    raw=raw[:524288]+b'\n[LOG MIDDLE OMITTED; ORIGINAL SIZE/HASH IN REPORT]\n'+raw[-524288:]
                print('DIALYSISLAB_COMMAND_LOG '+item['name']+'\n'+raw.decode('utf-8',errors='replace')+'\nDIALYSISLAB_COMMAND_LOG_END')
        for name in report['public_reports']:
            path=output/name
            if path.is_file() and not path.is_symlink():
                value=json.loads(path.read_text())
                print('DIALYSISLAB_REPORT '+name+'\n'+json.dumps(value,sort_keys=True)+'\nDIALYSISLAB_REPORT_END')
        summary=os.environ.get('GITHUB_STEP_SUMMARY')
        if summary:
            with open(summary,'a') as stream:
                stream.write('## DialysisLab software verification\n\nCommit: `'+report['source_revision']+'`\n\n')
                stream.write('| Check | Result |\n| --- | --- |\n')
                for item in report['steps']:stream.write('| '+item['name']+' | '+item['status']+' |\n')
                stream.write('\nRelease gate: **'+report['release_gate']+'**. Software tests do not establish clinical or regulatory conformity. Full identified JSON reports are in this job log; raw workspaces expire.\n')
        return
    output.mkdir(parents=True,exist_ok=False)
    revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    report=dict(schema_version=1,source_revision=revision,started_at=datetime.now(timezone.utc).isoformat(),
                command=sys.argv,steps=[],release_gate='NOT_RUN',public_reports=[],successful=False)
    env=dict(os.environ,SOURCE_REVISION=revision,PYTHONDONTWRITEBYTECODE='1')
    def save():report_path.write_text(json.dumps(report,indent=2)+'\n')
    def step(name,command,requires=True,timeout=1200,json_report=None,release=False):
        entry=dict(name=name,command=[str(x) for x in command],status='BLOCKED',exit_code=None)
        report['steps'].append(entry)
        if not requires:entry['reason']='Prerequisite step failed';save();return False
        log=output/(name+'.log')
        try:
            with log.open('w') as stream:
                result=subprocess.run(entry['command'],cwd=ROOT,env=env,stdout=stream,stderr=subprocess.STDOUT,timeout=timeout)
            entry['exit_code']=result.returncode;entry['status']='PASS' if result.returncode==0 else 'FAIL'
            if release:
                value=json.loads(log.read_text())
                if value.get('structural_errors'):raise ValueError('release checker structural errors')
                if result.returncode==1:entry['status']='BLOCKED';entry['reason']='Outstanding recorded release obligations'
                elif result.returncode!=0:raise ValueError('unexpected release checker error')
                if entry['status']=='BLOCKED':report['release_gate']='BLOCKED'
                elif report['release_gate']!='BLOCKED':report['release_gate']='PASS_REQUIRES_HUMAN_ASSESSMENT'
        except (OSError,ValueError,subprocess.TimeoutExpired) as exc:
            entry.update(status='FAIL',error=str(exc))
        if log.exists():
            entry['log_sha256']=hashlib.sha256(log.read_bytes()).hexdigest()
            entry['log_bytes']=log.stat().st_size
        if json_report and (output/json_report).is_file():
            entry['report']=json_report;entry['report_sha256']=hashlib.sha256((output/json_report).read_bytes()).hexdigest()
            report['public_reports'].append(json_report)
        save();print(name+': '+entry['status'],flush=True)
        return entry['status']=='PASS'
    save()
    trace=step('traceability',['python3','tools/check_traceability.py','assurance/traceability.json'])
    standards=step('standards',['python3','tools/check_standards.py'])
    publication=step('publication',['python3','tools/check_publication.py'])
    step('release-traceability',['python3','tools/check_traceability.py','assurance/traceability.json','--release'],requires=trace,release=True)
    step('release-standards',['python3','tools/check_standards.py','--release'],requires=standards,release=True)
    fetched=step('fetch-gui',['python3','tools/fetch_gui.py','--cache','build/gui-deps'])
    flags=['-DDIALYSISLAB_GUI=ON']
    local_prefix=ROOT/'build/dependency-inspection/xext-platform/usr'
    if (local_prefix/'include/X11/extensions/Xext.h').is_file():
        flags+=['-DDIALYSISLAB_XEXT_PREFIX='+str(local_prefix),'-DXEXT_LIB=/lib/x86_64-linux-gnu/libXext.so.6']
    for profile,build_type,extra in [('native','Release',[]),('sanitizer','Debug',['-DDIALYSISLAB_SANITIZE=ON'])]:
        build=output/profile
        configured=step(profile+'-configure',['cmake','-S','.', '-B',build,'-DCMAKE_BUILD_TYPE='+build_type]+flags+extra,requires=fetched)
        built=step(profile+'-build',['cmake','--build',build,'--parallel','3'],requires=configured)
        step(profile+'-tests',['python3','tools/verify_m1.py','--build-dir',build,'--output',output/(profile+'-tests.json')],requires=built,json_report=profile+'-tests.json')
        if profile=='native':
            native=built
            for tool,label in [('verify_device_ui.py','device'),('verify_console.py','console')]:
                step(label+'-widgets',['python3','tools/'+tool,'--build-dir',build,'--output',output/label],requires=built,json_report=label+'/report.json')
    images=step('docker-build',['docker','compose','--profile','device-ui','build'])
    step('compose',['python3','tools/verify_compose.py','--output',output/'compose'],requires=images,json_report='compose/compose-results.json')
    step('experiments',['python3','tools/verify_experiments_compose.py','--output',output/'experiments'],requires=images,json_report='experiments/report.json')
    step('device-compose',['python3','tools/verify_ui_compose.py','--output',output/'device-compose'],requires=images,json_report='device-compose/report.json')
    step('dependencies',['python3','tools/dependency_report.py','--build-dir',output/'native','--output',output/'dependencies','--images','dialysislab-m1:local','dialysislab-ui:local'],requires=native and images,json_report='dependencies/report.json')
    package=Path('/tmp')/('DialysisLab-ci-'+revision+'.zip')
    step('package',['python3','tools/package_release.py','--output',package],requires=publication)
    if package.is_file():report['package_sha256']=hashlib.sha256(package.read_bytes()).hexdigest()
    report['finished_at']=datetime.now(timezone.utc).isoformat()
    report['successful']=all(s['status']=='PASS' for s in report['steps'] if not s['name'].startswith('release-'))
    save()
    if not report['successful']:raise SystemExit(1)


if __name__=='__main__':main()
