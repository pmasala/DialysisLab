#!/usr/bin/env python3
"""Fit public in-vitro references; export an explicitly partial scenario profile."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'python'))
from dialysislab.calibration import fit


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--references',type=Path,default=ROOT/'references/dialyzer_benchmarks.json')
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--profile',choices=['reference-fx60','reference-fx80','reference-fx100'])
    parser.add_argument('--scenario',type=Path,default=ROOT/'scenarios/device_guided.json')
    args=parser.parse_args();raw=args.references.read_bytes();data=json.loads(raw)
    results=[fit(p) for p in data['profiles']]
    report=dict(schema_version=1,reference_sha256=hashlib.sha256(raw).hexdigest(),source=data['source'],
        qualification=data['qualification'],results=results,successful=all(p['accepted'] for p in results))
    args.output.mkdir(parents=True,exist_ok=False)
    (args.output/'calibration.json').write_text(json.dumps(report,indent=2)+'\n')
    if args.profile:
        from dialysislab.runner import validate
        p=next(p for p in data['profiles'] if p['id']==args.profile);f=next(f for f in results if f['id']==args.profile)
        if not f['accepted']:raise ValueError('holdout failed; profile not exported')
        c=json.loads(args.scenario.read_text());b=c['physical']['blood']
        c['patient']['prime_mL']+=p['blood_volume_mL']-b['filter_mL'];b['filter_mL']=p['blood_volume_mL']
        b['kuf_mL_min_mmHg']=p['kuf_mL_h_mmHg']/60
        c['circuit']['profile']['koa_mL_min'][0]=f['effective_urea_koa_mL_min']
        c['circuit']['profile']['id']=args.profile+'-partial-fit'
        validate(c)
        (args.output/'scenario.json').write_text(json.dumps(c,indent=2)+'\n')
    print(json.dumps(report))
    if not report['successful']:raise SystemExit(1)


if __name__=='__main__':main()
