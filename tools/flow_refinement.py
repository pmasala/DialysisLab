#!/usr/bin/env python3
"""Separate sampling windows, valve events, initial-state and transport effects."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'tests'), str(ROOT/'python')]
from audit_fixture import Coupled, compile_driver

STEPS = (400, 200, 100, 50, 25)
WINDOW_MS = 400
DURATION_MS = 12000


def analytic_volume(seconds, position=0, hold=0):
    """Independent constant-rate pulse train, rate 500 mL/min, capacity 30 mL."""
    rate = 500/60
    active = max(0.0, seconds-hold)
    first = (30-position)/rate
    if active <= first:
        return rate*active
    remainder = active-first
    cycle = .03+30/rate
    complete = math.floor(remainder/cycle)
    tail = remainder-complete*cycle
    return 30-position+30*complete+rate*max(0.0, tail-.03)


def valve_campaign(directory):
    binary = Path(directory)/'flow-valves'
    subprocess.run(['g++','-std=c++17','-O2','-Wall','-Wextra','-Werror','-I'+str(ROOT/'src'),
                    str(ROOT/'tests/flow_valves.cpp'),'-o',str(binary)], check=True, capture_output=True)
    lines = subprocess.check_output([str(binary)], text=True).splitlines()
    cases = {}
    for line in lines:
        kind, start, dt, tick, value = line.split()
        start, dt, value = int(start), int(dt), float(value)
        key = (start,dt)
        case = cases.setdefault(key,dict(start=start,dt_ms=dt,samples=[],events_s=[],maximum_volume_error_mL=0,maximum_event_error_s=0))
        position, hold = (29.9 if start==1 else 0), (.017 if start==2 else 0)
        if kind=='sample':
            expected = analytic_volume(int(tick)/1000,position,hold)
            case['maximum_volume_error_mL'] = max(case['maximum_volume_error_mL'],abs(value-expected))
            case['samples'].append(dict(time_ms=int(tick),volume_mL=value,analytic_mL=expected))
        else:
            expected = hold+(30-position)*60/500+(int(tick)-1)*(30*60/500+.03)
            case['maximum_event_error_s'] = max(case['maximum_event_error_s'],abs(value-expected))
            case['events_s'].append(value)
    if len(cases)!=24 or any(len(c['samples'])!=30 or len(c['events_s'])!=(4 if c['start']==1 else 3) or c['maximum_volume_error_mL']>1e-8 or c['maximum_event_error_s']>1e-8 for c in cases.values()):
        raise ValueError('analytic valve displacement/event criterion')
    return dict(criteria=dict(volume_absolute_mL=1e-8,event_absolute_s=1e-8),cases=list(cases.values()),successful=True)


def configuration(mode, dt):
    c=json.loads((ROOT/'scenarios'/('physical_'+mode+'.json')).read_text())
    c['dt_ms']=dt
    c['guided'].update(test_ms=1200,treatment_ms=100000)
    return c


def connected(binary, config):
    f=Coupled(binary,config)
    try:
        for _ in range(10000):
            if f.stage=='CONNECTED':return f
            f.step()
        raise ValueError('did not reach connected state')
    except BaseException:
        f.close();raise


def sample_run(f, dt):
    f.config['dt_ms']=dt
    before=f.record
    identity=hashlib.sha256(json.dumps(before,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    initial = dict(time_ms=f.time,sequence=f.sequence,record_sha256=identity,
                   machine=before['machine'],dynamics=before['physical']['dynamics'])
    cumulative=[0.0,0.0];window=[0.0,0.0];samples=[];events=[]
    cycle=before['physical']['dynamics']['balance_cycles']
    water=solute=0.0;reverse_faces=0;minimum_face=0.0
    old_storage=before['physical']['dynamics']['dialysate_storage_mL']
    for elapsed in range(0,DURATION_MS,dt):
        rx=None
        if elapsed in (4800,8000):
            route={'HD':0,'HDF_PRE':1,'HDF_POST':2}[f.config['treatment']['mode']]
            rx=(route,220 if elapsed==4800 else 300,5,40 if route else 0)
        r=f.step(rx=rx);p=r['physical'];d=p['dynamics']
        if r['machine']['alarm_mask'] or r['machine']['guided']['integrated_stage']!='TREATMENT':
            raise ValueError('unexpected alarm or non-treatment tick')
        # Independently reconstruct signed INTERNAL face volumes from continuity.
        filtration=[s['uf_mL_min']*dt/60000 for s in p['segments']]
        delta=(d['dialysate_storage_mL']-old_storage)/12
        for face in range(1,12):
            q=d['feed_mL_min']*dt/60000+math.fsum(filtration[face:])-(12-face)*delta
            if q < -1e-8:reverse_faces+=1
            minimum_face=min(minimum_face,q)
        old_storage=d['dialysate_storage_mL']
        for i,k in enumerate(('feed_mL_min','drain_mL_min')):
            volume=d[k]*dt/60000
            cumulative[i]+=volume;window[i]+=volume
        new_cycle=d['balance_cycles']
        if new_cycle!=cycle:
            if new_cycle!=cycle+1:raise ValueError('more than one event per observation interval')
            events.append(dict(cycle=int(new_cycle),lower_ms=elapsed,upper_ms=elapsed+dt));cycle=new_cycle
        water=max(water,abs(d['dialysate_residual_mL']))
        solute=max(solute,max(map(abs,r['patient']['mass_residual_mmol'])),
                   max(abs(c) for c in r['patient']['distributed']['dialysate_residual_mmol']))
        if (elapsed+dt)%WINDOW_MS==0:
            samples.append(dict(time_ms=elapsed+dt,feed_tick_mean_mL_min=d['feed_mL_min'],
                drain_tick_mean_mL_min=d['drain_mL_min'],feed_volume_mL=cumulative[0],drain_volume_mL=cumulative[1],
                feed_window_mean_mL_min=window[0]*60000/WINDOW_MS,drain_window_mean_mL_min=window[1]*60000/WINDOW_MS))
            window=[0.0,0.0]
    if len(samples)!=30 or water>1e-6 or solute>1e-6:raise ValueError('sample count or conservation criterion')
    return dict(dt_ms=dt,initial=initial,samples=samples,event_brackets=events,
                reverse_internal_face_count=reverse_faces,minimum_internal_face_mL=minimum_face,
                maximum_water_residual_mL=water,maximum_solute_residual_mmol=solute)


def compare(runs):
    differences=[]
    for a,b in zip(runs,runs[1:]):
        metrics={}
        for key in a['samples'][0]:
            if key=='time_ms':continue
            errors=[x[key]-y[key] for x,y in zip(a['samples'],b['samples'])]
            metrics[key]=dict(rms=math.sqrt(math.fsum(e*e for e in errors)/len(errors)),maximum_absolute=max(map(abs,errors)))
        events=[]
        for x,y in zip(a['event_brackets'],b['event_brackets']):
            events.append(dict(cycle_a=x['cycle'],cycle_b=y['cycle'],
                possible_separation_ms=[x['lower_ms']-y['upper_ms'],x['upper_ms']-y['lower_ms']]))
        differences.append(dict(coarse_ms=a['dt_ms'],fine_ms=b['dt_ms'],metrics=metrics,event_separation_intervals=events))
    keys=('feed_window_mean_mL_min','drain_window_mean_mL_min','feed_volume_mL','drain_volume_mL')
    trend={key:all(b['metrics'][key]['rms']<=a['metrics'][key]['rms']+1e-9 for a,b in zip(differences,differences[1:])) for key in keys}
    return dict(adjacent=differences,common_metric_rms_decreases=trend)


def coupled_campaign(binary):
    cases=[]
    for origin in ('fresh_workflow','identical_checkpoint'):
        for mode in ('hd','hdf_pre','hdf_post'):
            runs=[];f=None
            try:
                if origin=='identical_checkpoint':
                    f=connected(binary,configuration(mode,100))
                    for _ in range(40):f.step()
                    f.save(0)
                for dt in STEPS:
                    if origin=='fresh_workflow':f=connected(binary,configuration(mode,dt))
                    else:f.restore(0)
                    runs.append(sample_run(f,dt))
                    if origin=='fresh_workflow':f.close();f=None
            finally:
                if f is not None:f.close()
            comparison=compare(runs)
            if origin=='identical_checkpoint':
                if len({r['initial']['record_sha256'] for r in runs})!=1:raise ValueError('initial state mismatch')
                if not all(comparison['common_metric_rms_decreases'].values()):raise ValueError('checkpoint refinement regression')
            cases.append(dict(origin=origin,mode=mode,runs=runs,comparison=comparison))
    return cases


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();args.output.parent.mkdir(parents=True,exist_ok=True)
    if args.output.exists():parser.error('output exists; retain evidence and use a fresh filename')
    paths=[p for folder in ('src','python/dialysislab') for p in (ROOT/folder).rglob('*') if p.suffix in ('.py','.cpp','.hpp')]
    paths += [ROOT/p for p in ('tests/audit_fixture.py','tests/guided_plant.cpp','tests/flow_valves.cpp','tools/flow_refinement.py')]
    paths += [ROOT/'scenarios'/('physical_'+m+'.json') for m in ('hd','hdf_pre','hdf_post')]
    report=dict(schema_version=1,executed_at=datetime.now(timezone.utc).isoformat(),successful=False,
        source_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)},
        configuration_rule='Source-identified physical mode, test_ms=1200, treatment_ms=100000; fresh runs start CONNECTED; common checkpoint after 40 treatment ticks of 100 ms. Blood steps at 4800/8000 ms; active substitution 40 mL/min, net UF 5 mL/min.',
        comparison_window_ms=WINDOW_MS,duration_ms=DURATION_MS,steps_ms=STEPS,
        criteria='Analytic constant-rate valve volume/event error <=1e-8. Every coupled tick conserves water/solute <=1e-6 and has no alarm. Identical-checkpoint common-window and cumulative RMS differences decrease across refinements (1e-9 absolute numerical slack). Fresh-workflow differences are measured, not assumed monotonic. These engineering regressions are not calibrated physical-accuracy budgets.')
    try:
        with tempfile.TemporaryDirectory() as directory:
            report['valves']=valve_campaign(directory)
            report['coupled']=coupled_campaign(compile_driver(directory))
        report['successful']=True
    except BaseException as exc:
        report['error']=type(exc).__name__+': '+str(exc);raise
    finally:args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(successful=True,valve_cases=len(report['valves']['cases']),coupled_cases=len(report['coupled'])*len(STEPS))))

if __name__=='__main__':main()
