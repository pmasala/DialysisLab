#!/usr/bin/env python3
"""Current coupled numerical/resource campaign. No clinical accuracy claim.

Uses the actual plant and patient over pipes; Unix IPC/containers are separate gates.
"""
import argparse
from datetime import datetime,timezone
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import time
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'python')]
from audit_fixture import Coupled,compile_driver
from dialysislab.trajectory import TrajectoryWriter,scan
from trajectory_memory_probe import rss_sample


def values(record):
    p=record['physical'];d=p['dynamics'];patient=record['patient']
    result={k:p[k] for k in ('arterial_mmHg','venous_mmHg','tmp_mmHg')}
    result.update({k:d[k] for k in ('arterial_level','venous_level','feed_mL_min','drain_mL_min')})
    result.update(net_patient_loss_mL=patient['net_patient_loss_mL'],urea_mmol_L=patient['concentration_mmol_L'][0][0],
                  outlet_urea_mmol_L=patient['distributed']['compartments'][13]['concentration_mmol_L'][0],
                  outlet_hematocrit=patient['distributed']['compartments'][13]['hematocrit'])
    return result


def convergence(binary):
    result=[]
    for mode in ('hd','hdf_pre','hdf_post'):
        series={};peaks={}
        for dt in (400,200,100):
            c=json.loads((ROOT/'scenarios'/('physical_'+mode+'.json')).read_text())
            c['dt_ms']=dt;c['guided'].update(test_ms=1200,treatment_ms=12000)
            f=Coupled(binary,c);samples={};water=solute=0.0
            try:
                for _ in range(2000):
                    elapsed=f.record['machine']['guided']['treatment_elapsed_ms'] if f.record else 0
                    rx=None
                    if f.stage=='TREATMENT' and elapsed in (4800,8000):
                        route={'hd':0,'hdf_pre':1,'hdf_post':2}[mode]
                        rx=(route,220 if elapsed==4800 else 300,5,40 if route else 0)
                    r=f.step(rx=rx);elapsed=r['machine']['guided']['treatment_elapsed_ms']
                    if r['machine']['guided']['integrated_stage']=='TREATMENT' and elapsed%400==0:samples[elapsed]=values(r)
                    water=max(water,abs(r['physical']['dynamics']['dialysate_residual_mL']))
                    solute=max(solute,max(map(abs,r['patient']['mass_residual_mmol'])))
                    if r['machine']['alarm_mask']:raise ValueError('unexpected convergence alarm')
                    if f.stage=='FINISHED':break
                if f.stage!='FINISHED' or len(samples)!=30:raise ValueError('incomplete convergence sample grid')
            finally:f.close()
            series[dt]=samples;peaks[dt]=dict(water_residual_mL=water,solute_residual_mmol=solute)
        differences={}
        for name in series[100][400]:
            def rms(a,b):return math.sqrt(sum((series[a][t][name]-series[b][t][name])**2 for t in series[a])/30)
            coarse=rms(400,200);fine=rms(200,100)
            differences[name]=dict(rms_400_200=coarse,rms_200_100=fine,ratio=fine/coarse if coarse else None,
                                   decreasing=fine<=coarse+1e-12)
        result.append(dict(mode=mode,dt_ms=[400,200,100],treatment_samples=30,step_elapsed_ms=[4800,8000],
                           differences=differences,peak_residuals=peaks))
    return dict(cases=result,decision='Measured refinement differences only. Finite outputs and conservation required; output-specific physical accuracy budgets and global envelope approval remain external. Valve discontinuities/phase quantization can make pointwise refinement nonmonotonic.')


def long_run(binary,directory,ticks):
    c=json.loads((ROOT/'scenarios/physical_hdf_post.json').read_text())
    c['ticks']=ticks;c['guided']['treatment_ms']=86400000;c['guided']['test_ms']=1000
    c['physical']['fluid']['acid_mL']=20000
    c['physical']['fluid']['bicarbonate_g']=2000
    writer=TrajectoryWriter(directory)
    (directory/'configuration.json').write_text(json.dumps(c,indent=2)+'\n')
    f=Coupled(binary,c);started=time.monotonic();treatment_ticks=0;peak=0
    try:
        for n in range(ticks):
            r=f.step();r.update(sequence=n,time_ms=f.time)
            writer.append(r)
            treatment_ticks+=r['machine']['guided']['integrated_stage']=='TREATMENT'
            if r['machine']['alarm_mask']:raise ValueError('unexpected long-run alarm at '+str(n))
            if n%1000==0:
                peak=max(peak,rss_sample()['peak_rss_bytes'])
                if n%10000==0:print('completed ticks '+str(n),file=sys.stderr,flush=True)
        peak=max(peak,rss_sample()['peak_rss_bytes'])
    finally:writer.close();f.close()
    report=scan(directory/'trajectory.jsonl')
    if report['records']!=ticks or peak>64*1024**2:raise ValueError('record/resource criterion')
    return dict(ticks=ticks,treatment_ticks=treatment_ticks,peak_rss_bytes=peak,trajectory=report,
                elapsed_seconds=time.monotonic()-started,scope='Actual coupled model and streaming writer in native pipe harness. Not a Compose isolation/cgroup measurement.')


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--mode',choices=('convergence','resource'),default='convergence');parser.add_argument('--ticks',type=int,default=100000)
    args=parser.parse_args()
    if not 1<=args.ticks<=100000:parser.error('ticks must be 1..100000')
    source_snapshot={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for folder in ('src','python/dialysislab') for p in sorted((ROOT/folder).rglob('*')) if p.suffix in ('.py','.hpp','.cpp')}
    harness_snapshot={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in ('tools/audit_campaign.py','tests/audit_fixture.py','tests/guided_plant.cpp')}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    try:
        with tempfile.TemporaryDirectory() as d:
            binary=compile_driver(d)
            result=convergence(binary) if args.mode=='convergence' else long_run(binary,args.output.with_suffix(''),args.ticks)
    except BaseException as error:
        failed=dict(successful=False,error=type(error).__name__+': '+str(error),mode=args.mode,
            source_sha256=source_snapshot,harness_sha256=harness_snapshot,
            retained_records=str(args.output.with_suffix('')),executed_at=datetime.now(timezone.utc).isoformat())
        args.output.write_text(json.dumps(failed,indent=2)+'\n')
        raise
    result.update(successful=True,executed_at=datetime.now(timezone.utc).isoformat(),mode=args.mode,
        source_sha256=source_snapshot,harness_sha256=harness_snapshot)
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('source_sha256','harness_sha256','cases','trajectory')},indent=2))


if __name__=='__main__':main()
