#!/usr/bin/env python3
"""Execute the predeclared M9 matrix with actual processes or isolated containers."""
import argparse
import copy
from datetime import datetime,timezone
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'python'))
from dialysislab.runner import LocalCluster,simulate,build_identity,stop_plant,validate
from dialysislab.trajectory import read_records
from verify_models import verify
from verify_compose import collect_case,ComposeRunFailure


def load(name):return json.loads((ROOT/'scenarios'/(name+'.json')).read_text())


def configurations(group):
    if group=='matrix':
        for mode in ('hd','hdf_pre','hdf_post'):
            for patient in ('baseline','overload','imbalance'):
                for dialyzer in ('small','large'):
                    config=load('machine_'+mode)
                    config['patient']=copy.deepcopy(load('patient_'+patient)['patient'])
                    config['patient']['prime_mL']=20
                    config['patient_volume_mL']=sum(config['patient']['volume_mL'])
                    config['transport']['blood_mmol_L']=config['patient']['concentration_mmol_L'][0].copy()
                    if dialyzer=='large':
                        profile=copy.deepcopy(load('treatment_hdf_large')['circuit']['profile'])
                        profile.update(id='synthetic-integration-large',resistance_mmHg_min_mL=0.9,kuf_mL_min_mmHg=1)
                        config['circuit']['profile']=profile
                    yield 'integrated_'+mode+'_'+patient+'_'+dialyzer,config
    elif group=='long':
        config=load('machine_hdf_post');config.update(ticks=100000,dt_ms=1000)
        config['treatment']['replacement_mL_min']=70
        config['workflow']=[dict(tick=tick,action=action,values=[]) for tick,action in
            ((4,'PRIME'),(90,'CONFIGURE'),(94,'START'),(99990,'FINISH'),(99994,'CLEAN'))]
        yield 'integrated_hdf_100000',config
    elif group=='dynamic-short':
        config=load('physical_hdf_post')
        # Preserve the scheduled preparation/return margins, extending only therapy.
        extra=(600000-config['guided']['treatment_ms'])//config['dt_ms']
        config['guided']['treatment_ms']=600000
        config['ticks']+=extra
        for event in config['workflow']:
            if event['action'] in ('RETURN','DISCONNECT','CLEAN'):event['tick']+=extra
        yield 'integrated_dynamic_hdf_10min',config
    elif group=='dynamic-long':
        config=load('physical_hdf_post');config.update(ticks=100000,dt_ms=500)
        config['guided']['treatment_ms']=86400000
        config['physical']['fluid'].update(acid_mL=20000,bicarbonate_g=2000)
        config['workflow']=[e for e in config['workflow'] if e['action'] in ('PRIME','CONNECT','START')]
        yield 'integrated_dynamic_hdf_100000',config
    elif group=='faults':
        for name in ('machine_air','machine_balance','machine_invalid','machine_leak','machine_pressure',
                     'machine_quality','machine_recovery','machine_stall','treatment_contaminant','treatment_filter1',
                     'treatment_integrity','treatment_ratio','treatment_route','treatment_supply','treatment_temperature'):
            yield name,load(name)
    else:raise ValueError('unknown integration group')


def write_configuration(path,config,container_readable=False):
    with path.open('x') as stream:stream.write(json.dumps(config,indent=2)+'\n')
    # These are generated, public synthetic fixtures. The container's UID10001
    # must read this one bind-mounted file even when its host owner uses umask077.
    if container_readable:path.chmod(0o644)


def write_report(path,report):
    temporary=path.with_suffix(path.suffix+'.tmp')
    temporary.write_text(json.dumps(report,indent=2)+'\n')
    temporary.replace(path)


def archive_trajectory(path,expected_sha256):
    """Lossless storage only after verification; raw data survive any failure."""
    path=Path(path);target=path.with_suffix(path.suffix+'.gz');temporary=target.with_suffix(target.suffix+'.partial')
    if target.exists() or temporary.exists():raise ValueError('archive already exists')
    original=hashlib.sha256();size=0
    with path.open('rb') as source,temporary.open('xb') as destination,gzip.GzipFile(filename='',fileobj=destination,mode='wb',mtime=0) as output:
        for chunk in iter(lambda:source.read(65536),b''):
            original.update(chunk);size+=len(chunk);output.write(chunk)
    if original.hexdigest()!=expected_sha256:raise ValueError('trajectory changed before archive')
    restored=hashlib.sha256();restored_size=0
    with gzip.open(temporary,'rb') as source:
        for chunk in iter(lambda:source.read(65536),b''):restored.update(chunk);restored_size+=len(chunk)
    if restored.hexdigest()!=expected_sha256 or restored_size!=size:raise ValueError('archive round trip failed')
    archive_hash=hashlib.sha256()
    with temporary.open('rb') as source:
        for chunk in iter(lambda:source.read(65536),b''):archive_hash.update(chunk)
    temporary.rename(target)
    result=dict(path=str(target),sha256=archive_hash.hexdigest(),bytes=target.stat().st_size,
                original_path=str(path),original_sha256=expected_sha256,original_bytes=size,
                recovery_argv=['gzip','-dc',str(target)],recovery_output=str(path),round_trip_verified=True)
    # Persist recovery instructions before dropping only the verified raw duplicate.
    (target.parent/'trajectory-storage.json').write_text(json.dumps(result,indent=2)+'\n')
    path.unlink()
    return result


def acceptance(directory,config,group,name):
    integrated_treatment_ms=0;treatment_ticks=0;stages=set();stage_order=[];treatment_elapsed_ms=0;last_stage=None;first_alarm=None;first_expected=None;first_quality=None;recovered=False
    expected_mask={'machine_air':4,'machine_balance':2048,'machine_invalid':16,'machine_leak':8,
                   'machine_pressure':1,'machine_quality':256,'machine_recovery':4,'machine_stall':2}.get(name)
    for record in read_records(directory/'trajectory.jsonl'):
        if type(record.get('time_ms')) is not int or record['time_ms']!=(record['sequence']+1)*config['dt_ms']:
            raise ValueError('trajectory virtual timestamp differs from declared tick')
        if record.get('online',{}).get('quality_latched') and first_quality is None:first_quality=record['time_ms']
        machine=record.get('machine')
        if machine:
            stages.add(machine['stage'])
            last_stage=machine['stage']
            if not stage_order or stage_order[-1]!=last_stage:stage_order.append(last_stage)
            treatment_elapsed_ms=machine.get('guided',{}).get('treatment_elapsed_ms',0)
            treatment_ticks+=machine['stage']=='TREATMENT'
            if machine.get('guided',{}).get('integrated_stage')=='TREATMENT':integrated_treatment_ms+=config['dt_ms']
            if machine['alarm_mask'] and first_alarm is None:first_alarm=record['time_ms']
            if expected_mask and machine['alarm_mask']&expected_mask and first_expected is None:first_expected=record['time_ms']
            if name=='machine_recovery' and record['sequence']>=150 and machine['stage']=='TREATMENT' and not machine['alarm_mask']:recovered=True
    if group=='dynamic-short':
        required=['SELF_TEST','PREPARATION','PRIMING','CONFIGURATION','CONNECTED','TREATMENT',
                  'FINISHED','RETURNING','DISCONNECTING','DISCONNECTED','CLEANING','CLEANED']
        if stage_order!=required:raise ValueError('short dynamic lifecycle order incomplete')
        if treatment_elapsed_ms!=600000 or integrated_treatment_ms!=600000:raise ValueError('short dynamic therapy duration differs from ten minutes')
        if last_stage!='CLEANED':raise ValueError('short dynamic final state is not CLEANED')
    if group in ('matrix','long','dynamic-long','dynamic-short'):
        if first_alarm is not None:raise ValueError('unexpected alarm in nominal integrated run')
        if treatment_ticks<(99001 if group in ('long','dynamic-long') else 100):raise ValueError('insufficient actual treatment')
        if group=='matrix' and 'CLEANED' not in stages:raise ValueError('lifecycle did not reach CLEANED')
    if group=='faults':
        event=config['faults'][0]['tick']*config['dt_ms']
        if expected_mask and (first_expected is None or not event<=first_expected<=event+2*config['dt_ms']):
            raise ValueError('intended machine alarm missed its two-observation-cycle bound')
        if name=='machine_recovery' and not recovered:raise ValueError('permitted post-fault treatment recovery missing')
        if name.startswith('treatment_') and name!='treatment_contaminant':
            if first_quality is None or not event<=first_quality<=event+10000+config['dt_ms']:raise ValueError('online fault missed predeclared bound')
        if name=='treatment_contaminant' and first_quality is not None:raise ValueError('hidden contamination invented an observable detector')
    return dict(integrated_treatment_ms=integrated_treatment_ms,treatment_ticks=treatment_ticks,treatment_elapsed_ms=treatment_elapsed_ms,stage_order=stage_order,stages=sorted(stages),first_alarm_ms=first_alarm,
                expected_mask=expected_mask,first_expected_alarm_ms=first_expected,first_quality_ms=first_quality,recovered=recovered)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--group',choices=('matrix','faults','long','dynamic-long','dynamic-short'),default='matrix')
    parser.add_argument('--build-dir',type=Path,default=ROOT/'build/gui')
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--compose',action='store_true')
    parser.add_argument('--compose-timeout',type=int,help='Wall-clock seconds per Compose repetition; default 2400 for endurance, 900 otherwise')
    parser.add_argument('--archive',action='store_true',help='Losslessly compress verified trajectories and retain recovery records')
    args=parser.parse_args()
    if args.compose_timeout is not None and not 1<=args.compose_timeout<=86400:parser.error('compose timeout must be 1..86400 seconds')
    args.output=args.output.resolve();args.output.mkdir(parents=True,exist_ok=False)
    report=dict(schema_version=1,executed_at=datetime.now(timezone.utc).isoformat(),command=sys.argv,
                build=build_identity(args.build_dir),group=args.group,compose=args.compose,successful=False,cases=[])
    expected=report['build']['source_sha256']
    try:
        for name,config in configurations(args.group):
            validate(config);configuration=args.output/(name+'.json');write_configuration(configuration,config,args.compose)
            hashes=[]
            for repeat in (1,2):
                required_disk_mib=5120 if args.group=='dynamic-long' else 2048
                if args.group in ('long','dynamic-long') and shutil.disk_usage(args.output).free<required_disk_mib*1024**2:
                    raise OSError('less than '+str(required_disk_mib)+'MiB free for long trajectory and extraction; preserve prior artifacts')
                observed=None;collection=None
                if args.compose:
                    override=args.output/(name+'-compose.json')
                    override.write_text(json.dumps({'services':{'runner':{
                        'command':['python3','-m','dialysislab.runner','--config','/scenario.json','--output','/results/run','--build-dir','/opt/bin','--progress-every','100'],
                        'volumes':[{'type':'bind','source':str(configuration),'target':'/scenario.json','read_only':True}]}}},indent=2)+'\n')
                    collection=collect_case(name,repeat,args.output,compose_files=[ROOT/'compose.yaml',override],timeout=args.compose_timeout or (2400 if args.group=='dynamic-long' else 900),live=True)
                    if collection['compose_exit_code'] or collection['collection_errors'] or collection['cleanup_errors']:raise ComposeRunFailure(collection)
                    directory=Path(collection['directory'])/'results/run'
                else:
                    directory=args.output/(name+'-'+str(repeat))
                    with LocalCluster(args.build_dir) as cluster:
                        simulate(config,cluster.runtime,args.build_dir,directory,progress_every=100)
                        observed=stop_plant(cluster.runtime/'admin/plant.sock',online=True)
                        if not observed['acknowledged'] or not observed['outputs_zero_observed']:raise ValueError('final plant stop unconfirmed')
                case=verify(directory,config,expected)
                criteria=acceptance(directory,config,args.group,name)
                if args.group=='long':
                    if case['scan']['last']['removed_total_mL']<=100000:raise ValueError('gross UF stress boundary not exercised')
                if args.group in ('long','dynamic-long','dynamic-short') and case['manifest']['memory']['peak_rss_bytes']>64*1024**2:raise ValueError('runner RSS exceeds 64MiB acceptance')
                if collection:
                    for service in collection['services']:
                        if service['oom_killed'] or service['memory_limit_bytes']!=128*1024**2:raise ValueError('container resource acceptance')
                case.update(name=name,repeat=repeat,directory=str(directory),acceptance=criteria,observed_stop=observed,collection=collection)
                hashes.append(case['scan']['sha256']);report['cases'].append(case)
                if args.archive:case['archive']=archive_trajectory(directory/'trajectory.jsonl',case['scan']['sha256'])
                write_report(args.output/'integration.json',report)
                print(name+' '+str(repeat)+': verified',flush=True)
            if hashes[0]!=hashes[1]:raise ValueError('same-build exact replay failed: '+name)
        report['successful']=True
    except Exception as exc:
        report['error']=type(exc).__name__+': '+str(exc)
        raise
    finally:write_report(args.output/'integration.json',report)
    print(json.dumps(dict(successful=True,runs=len(report['cases']))))


if __name__=='__main__':main()
