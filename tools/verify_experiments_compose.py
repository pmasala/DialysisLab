#!/usr/bin/env python3
"""Actual repeated experiments and ImGui inputs across isolated role containers."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import sys
import time
import traceback
import uuid
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'python'),str(ROOT/'tools'),str(ROOT/'tests')]
from verify_compose import command,inspect_services
from capture_png import convert
from console_regressions import Console
import ui_regressions
from dialysislab.trajectory import scan


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--graphical',action='store_true');p.add_argument('--with-device',action='store_true');args=p.parse_args();args.output.mkdir(parents=True,exist_ok=False)
    project='dl-m7-'+uuid.uuid4().hex[:10]
    prefix=['docker','compose','-p',project,'-f',str(ROOT/'compose.experiments.yaml')]
    if args.graphical:prefix+=['-f',str(ROOT/'compose.experiments-x11.yaml')]
    prefix+=['--profile','console']
    if args.with_device:prefix+=['--profile','device-ui']
    report=dict(schema_version=1,executed_at=datetime.now(timezone.utc).isoformat(),command=sys.argv,project=project,graphical=args.graphical,successful=False,primary_exit=0,primary_error=None,collection_errors=[],cleanup_errors=[],resources_retained=True)
    report['simultaneous_device']=args.with_device
    ui=None;device=None;broker_id=None;ui_name=project+'-console';device_name=project+'-device';extracted=set()
    def call(op,params=None):
        code="import json;from dialysislab.experiment_rpc import request;print(json.dumps(request('/experiment',"+repr(op)+","+repr(params or {})+")))"
        return json.loads(command(['docker','exec',broker_id,'python3','-c',code]))
    def until(fn,test,timeout=30):
        deadline=time.monotonic()+timeout
        while time.monotonic()<deadline:
            value=fn()
            if test(value):return value
            time.sleep(.1)
        raise RuntimeError('condition timeout: '+str(value)[:2000])
    try:
        report['startup']=command(prefix+['up','-d','--no-build','plant','control','protection','patient','scenario-runner'])
        broker_id=command(prefix+['ps','-q','scenario-runner']).strip()
        until(lambda:call('STATUS'),lambda s:s['state']=='idle')
        argv=prefix+['run','-T','--no-deps','--name',ui_name,'sim-console','/opt/bin/sim-console','--api-dir','/experiment','--capture-dir','/captures','--test-input']
        if not args.graphical:argv+=['--headless']
        ui=Console('/unused',args.output/'widget-events',argv)
        until(ui.snapshot,lambda s:s['connected'])
        if args.with_device:
            ui_regressions.EVIDENCE=args.output/'device-widget-events'
            argv=prefix+['run','-T','--no-deps','--name',device_name,'device-ui','/opt/bin/device-ui','--runtime-dir','/run/dialysis','--capture-dir','/captures','--test-input']
            if not args.graphical:argv+=['--headless']
            device=ui_regressions.UserInterface('/unused','simultaneous',argv=argv)
        ui.set('preset','machine_hdf_pre');ui.click('LOAD')
        until(lambda:call('DRAFT'),lambda c:c['treatment']['mode']=='HDF_PRE')
        ui.set('speed',4);ui.click('START')
        running=until(ui.snapshot,lambda s:s['state']=='running' and s['sequence']>=5)
        original=running['run_id']
        if device:
            report['device_treatment']=until(device.snapshot,lambda s:s.get('stage')=='TREATMENT' and s['display_status']=='LIVE' and s.get('blood_mL_min',0)>0 and s.get('uf_mL_min',0)>0)
            assert report['device_treatment']['blood_mL_min']>0 and report['device_treatment']['uf_mL_min']>0
        ui.click('PAUSE');paused=until(ui.snapshot,lambda s:s['state']=='paused')
        time.sleep(2.2);assert ui.snapshot()['sequence']==paused['sequence']
        if device:
            report['device_paused']=device.snapshot('simultaneous-paused')
            assert report['device_paused']['display_status']=='STALE'
            # Real device widget sends a request; scheduled ownership rejects it.
            device.send('CLICK PRIME')
            until(device.snapshot,lambda s:s['pending'])
            device.send('CLICK CONFIRM')
            report['device_rejected_request']=until(device.snapshot,lambda s:s['result']=='REJECT scheduled')
            assert not report['device_rejected_request']['pending']
        ui.send('CAPTURE compose-paused');time.sleep(.2)
        ui.click('RESUME');complete=until(ui.snapshot,lambda s:s['state']=='completed')
        assert complete['sequence']==399
        report['first']=call('STATUS')['experiment']
        ui.set('speed',0);ui.click('REPLAY');second=until(ui.snapshot,lambda s:s['state']=='completed' and s['run_id']!=original)
        ui.click('COMPARE');compared=until(lambda:call('STATUS')['job'],lambda j:j['state']=='completed')
        assert compared['result']['exact_replay'],compared
        report['comparison']=compared
        ui.click('EXPORT');exported=until(lambda:call('STATUS')['job'],lambda j:j.get('operation')=='EXPORT' and j['state']=='completed');report['export']=exported
        ui.send('CAPTURE compose-export');time.sleep(.2)
        report['console_memory']=command(['docker','exec',ui_name,'cat','/proc/1/status'])
        report['console_cgroup_peak']=command(['docker','exec',ui_name,'cat','/sys/fs/cgroup/memory.peak'])
        probe="""from pathlib import Path
import socket
from dialysislab.experiment_rpc import request
for path in ('/activation','/results','/run/dialysis/admin','/run/dialysis/patient','/run/dialysis/control'):
 assert not Path(path).exists() or not list(Path(path).iterdir()), path
try: request('/experiment','STATUS',token='0'*64)
except ValueError as error: assert 'unauthorized' in str(error)
else: raise AssertionError('bad credential accepted')
print('PASS console mounts; incorrect token denied')
"""
        report['isolation']=command(['docker','exec',ui_name,'python3','-c',probe])
        # A third fresh activation is aborted while paused; preserve its partial artifacts.
        third=call('START',dict(revision=call('STATUS')['revision'],request_id=uuid.uuid4().hex,wall_speed=1))['run_id']
        until(lambda:call('STATUS'),lambda s:s['sequence']>=(100 if device else 2))
        if device:
            report['device_fresh_run']=until(device.snapshot,lambda s:s.get('stage')=='TREATMENT' and s['display_status']=='LIVE' and s['generation']>report['device_treatment']['generation'])
            assert not report['device_fresh_run']['pending']
        call('PAUSE',dict(run_id=third));before_stop=until(lambda:call('STATUS'),lambda s:s['state']=='paused')
        if device:
            started=time.monotonic();device.send('CLICK STOP')
        else:call('STOP',dict(run_id=third))
        stopped=until(lambda:call('STATUS'),lambda s:s['state']=='aborted',timeout=5 if device else 30)
        if device:
            report['device_stop_wall_seconds']=time.monotonic()-started
            assert report['device_stop_wall_seconds']<5 and stopped['sequence']==before_stop['sequence']
            report['device_after_stop']=device.snapshot('simultaneous-stopped')
            report['device_memory']=command(['docker','exec',device_name,'cat','/proc/1/status'])
            report['device_cgroup_peak']=command(['docker','exec',device_name,'cat','/sys/fs/cgroup/memory.peak'])
        assert stopped['experiment']['stop']['outputs_zero_observed'];report['aborted']=stopped['experiment']
        report['runs']=[original,second['run_id'],third]
        ui.close();ui=None
        if device:device.close();device=None
    except Exception as exc:
        report['primary_exit']=getattr(exc,'returncode',1);report['primary_error']=type(exc).__name__+': '+str(exc);report['primary_traceback']=traceback.format_exc()
    finally:
        if ui:
            try:ui.close()
            except Exception as exc:report['collection_errors'].append(dict(stage='console_close',error=str(exc)))
        if device:
            try:device.close()
            except Exception as exc:report['collection_errors'].append(dict(stage='device_close',error=str(exc)))
        # Stop the broker first: its signal handler preserves actual HALT and partial manifest.
        try:command(prefix+['stop','scenario-runner'])
        except Exception as exc:report['collection_errors'].append(dict(stage='broker_stop',error=str(exc)))
        logs=[('services.log',prefix+['logs','--no-color','--timestamps']),('console.log',['docker','logs',ui_name])]
        if args.with_device:logs.append(('device.log',['docker','logs',device_name]))
        for name,argv in logs:
            try:(args.output/name).write_text(command(argv))
            except Exception as exc:report['collection_errors'].append(dict(stage=name,error=str(exc)))
        try:report['services']=inspect_services(prefix)
        except Exception as exc:report['collection_errors'].append(dict(stage='inspect',error=str(exc)))
        sources=[('results',(broker_id or project+'-scenario-runner-1')+':/results/.'),('captures',ui_name+':/captures/.')]
        if args.with_device:sources.append(('device-captures',device_name+':/captures/.'))
        for name,source in sources:
            try:command(['docker','cp',source,str(args.output/name)]);extracted.add(name)
            except Exception as exc:report['collection_errors'].append(dict(stage=name,error=str(exc)))
        if extracted=={name for name,_ in sources} and not report['collection_errors']:
            try:command(prefix+['down','--volumes','--remove-orphans']);report['resources_retained']=False
            except Exception as exc:report['cleanup_errors'].append(str(exc))
        else:
            try:command(prefix+['stop'])
            except Exception as exc:report['cleanup_errors'].append(str(exc))
            report['recovery_commands']=['docker cp '+(broker_id or project+'-scenario-runner-1')+':/results/. /tmp/'+project+'-results','docker cp '+ui_name+':/captures/. /tmp/'+project+'-captures',' '.join(prefix+['down','--volumes','--remove-orphans'])]
            if args.with_device:report['recovery_commands'].insert(-1,'docker cp '+device_name+':/captures/. /tmp/'+project+'-device-captures')
    try:
        if report['primary_exit'] or report['collection_errors'] or report['cleanup_errors']:raise ValueError('execution/collection failure')
        summaries=[]
        for identifier in report['runs']:
            data=args.output/'results'/identifier/'data';manifest=json.loads((data/'manifest.json').read_text());measured=scan(data/'trajectory.jsonl')
            assert manifest['trajectory_sha256']==measured['sha256'] and manifest['completed_ticks']==measured['records']
            summaries.append(dict(run_id=identifier,manifest=manifest,trajectory={k:v for k,v in measured.items() if k not in ('first','last')}))
        report['run_evidence']=summaries
        console=next(s for s in report['services'] if s['service']=='sim-console')
        mounts={'/experiment','/captures'}|({'/tmp/.X11-unix/X0'} if args.graphical else set())
        # tmpfs /tmp is a declared sandbox resource, not an administrative volume.
        assert set(console['mounts'])-{'/tmp'}==mounts
        if args.with_device:
            device_service=next(s for s in report['services'] if s['service']=='device-ui')
            expected={'/run/dialysis/device/control','/run/dialysis/device/protection','/captures'}|({'/tmp/.X11-unix/X0'} if args.graphical else set())
            assert set(device_service['mounts'])-{'/tmp'}==expected
        for s in report['services']:
            assert s['network']=='none' and s['read_only'] and not s['oom_killed'] and s['memory_limit_bytes']==128*1024**2
        for path in (args.output/'captures').glob('*.ppm'):convert(path,path.with_suffix('.png'))
        if args.with_device:
            for path in (args.output/'device-captures').glob('*.ppm'):convert(path,path.with_suffix('.png'))
        report['successful']=True
    except Exception as exc:report['validation_error']=str(exc)
    report['artifacts']={str(p.relative_to(args.output)):hashlib.sha256(p.read_bytes()).hexdigest() for p in args.output.rglob('*') if p.is_file()}
    (args.output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report.get(k) for k in ('successful','primary_exit','primary_error','validation_error','collection_errors','resources_retained')},indent=2))
    return report['primary_exit'] or (0 if report['successful'] else 1)


if __name__=='__main__':sys.exit(main())
