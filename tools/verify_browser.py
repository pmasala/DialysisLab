#!/usr/bin/env python3
"""Compare full production coupled records under CPython/native and Pyodide/Wasm."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'python'));sys.path.insert(0,str(ROOT/'tests/browser'))
from campaign import campaign

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True);parser.add_argument('--manual-delay-ticks',type=int,default=0);args=parser.parse_args()
    if args.manual_delay_ticks < 0:parser.error('manual delay must be nonnegative')
    output=Path(args.output);output.mkdir(parents=True,exist_ok=False)
    inputs={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for base in ['src','python/dialysislab','tests/browser','web','cmake/browser'] for p in sorted((ROOT/base).rglob('*')) if p.is_file() and '__pycache__' not in str(p)}
    report=dict(executed_at=datetime.now(timezone.utc).isoformat(),source_revision=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),source_sha256=inputs,successful=False,criteria='abs(a-b) <= 1e-8 + 1e-9*max(abs(a),abs(b)); discrete values exact; existing 1e-6 inventory bounds',scope='Portability of coupled models, not numerical closure or clinical validation')
    processes=[]
    def reset(epoch):
        if processes:
            p=processes[-1];p.stdin.close();p.wait(timeout=10);assert p.returncode==0
        processes.append(subprocess.Popen([str(ROOT/'build/browser-native-engine')],stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True))
    def transport(role,frame):
        p=processes[-1];p.stdin.write(str(role)+' '+frame+'\n');p.stdin.flush();return p.stdout.readline().strip()
    report['worktree_dirty_at_execution']=bool(subprocess.check_output(['git','status','--porcelain'],text=True))
    report['build_identity']=json.loads((ROOT/'build/browser/build-identity.json').read_text())
    for name,sha in report['build_identity']['source_sha256'].items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==sha, 'Rebuild changed input: '+name
    for name,sha in report['build_identity']['artifacts'].items():
        assert hashlib.sha256((ROOT/'build/browser'/name).read_bytes()).hexdigest()==sha, 'Changed binary/asset: '+name
    subprocess.run(['g++','-std=c++17','-O2','-Wall','-Wextra','-Werror','src/browser/engine.cpp','-o','build/browser-native-engine'],check=True)
    report['native_engine_sha256']=hashlib.sha256((ROOT/'build/browser-native-engine').read_bytes()).hexdigest()
    start=time.monotonic()
    try:
        config=json.loads((ROOT/'build/browser/scenario.json').read_text())
        report['manual_delay_ticks']=args.manual_delay_ticks
        report['configuration_sha256']=hashlib.sha256(json.dumps(config,sort_keys=True).encode()).hexdigest()
        with (output/'native.jsonl').open('x') as stream:campaign(config,transport,reset,lambda value:stream.write(value+'\n'),args.manual_delay_ticks)
        p=processes[-1];p.stdin.close();p.wait(timeout=10)
        execution=subprocess.run(['node','tests/browser/run_wasm.cjs','build/browser',str(output/'wasm.jsonl'),str(args.manual_delay_ticks)],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        report['wasm_output']=execution.stdout
        if execution.returncode:raise RuntimeError(execution.stdout)
        counts={};peak=0.;worst='';fields=0
        def compare(a,b,path):
            nonlocal peak,worst,fields
            if isinstance(a,bool) or a is None or isinstance(a,str):assert a==b,(path,a,b)
            elif isinstance(a,(int,float)):
                if type(a) is int:assert a==b,(path,a,b)
                else:
                    fields+=1;error=abs(a-b);ratio=error/(1e-8+1e-9*max(abs(a),abs(b)))
                    assert ratio<=1,(path,a,b,ratio)
                    if ratio>peak:peak=ratio;worst=path
            elif isinstance(a,list):
                assert len(a)==len(b)
                for i,(x,y) in enumerate(zip(a,b)):compare(x,y,path+'/'+str(i))
            else:
                assert a.keys()==b.keys()
                for k in a:compare(a[k],b[k],path+'/'+k)
        import itertools
        with (output/'native.jsonl').open() as a,(output/'wasm.jsonl').open() as b:
            for x,y in itertools.zip_longest(a,b):
                assert x and y
                aa,bb=json.loads(x),json.loads(y);compare(aa,bb,aa['mode']+'/'+str(aa['tick']));counts[aa['mode']]=counts.get(aa['mode'],0)+1
        assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==sha for p,sha in inputs.items()), 'Inputs changed during execution'
        report.update(successful=True,records=counts,numeric_comparisons=fields,peak_fraction_of_budget=peak,worst_field=worst)
    except Exception as exc:report['error']=repr(exc);raise
    finally:
        for p in processes:
            if p.poll() is None:p.terminate();p.wait()
        report['elapsed_s']=time.monotonic()-start
        for name in ['native.jsonl','wasm.jsonl']:
            p=output/name
            if p.exists():report[name+'_sha256']=hashlib.sha256(p.read_bytes()).hexdigest()
        (output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='source_sha256'},indent=2))
if __name__=='__main__':main()
