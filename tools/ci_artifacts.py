#!/usr/bin/env python3
"""Recover original CI report/log bytes from bounded, hashed base64 envelopes."""
import argparse
import base64
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys

PREFIX='DIALYSISLAB_ARTIFACT_V2 '
CHUNK=3072
MAX_BYTES=16*1024*1024


def safe_name(name):
    if not isinstance(name,str) or len(name)>240 or not re.fullmatch(r'[A-Za-z0-9_.\-/]+',name):
        raise ValueError('artifact filename')
    path=PurePosixPath(name)
    if path.is_absolute() or any(p in ('.','..') or p.endswith('.partial') for p in path.parts) or name!=str(path):
        raise ValueError('unsafe artifact path')
    return name


def emit(name,raw,expected_sha256=None,stream=None):
    stream=stream or sys.stdout;safe_name(name)
    if len(raw)>MAX_BYTES:raise ValueError('artifact exceeds retention limit: '+name)
    digest=hashlib.sha256(raw).hexdigest()
    if expected_sha256 is not None and digest!=expected_sha256:raise ValueError('artifact changed before retention: '+name)
    count=(len(raw)+CHUNK-1)//CHUNK
    header=dict(kind='begin',name=name,bytes=len(raw),sha256=digest,chunks=count,encoding='base64')
    print(PREFIX+json.dumps(header,separators=(',',':')),file=stream)
    for index,start in enumerate(range(0,len(raw),CHUNK)):
        print(PREFIX+json.dumps(dict(kind='data',index=index,data=base64.b64encode(raw[start:start+CHUNK]).decode()),separators=(',',':')),file=stream)
    print(PREFIX+json.dumps(dict(kind='end',name=name),separators=(',',':')),file=stream)


def recover(log,output):
    output=Path(output);output.mkdir(parents=True,exist_ok=False,mode=0o700)
    active=None;stream=None;seen=set();artifacts=[]
    try:
        for line in log:
            start=line.find(PREFIX)
            if start<0:continue
            encoded=line[start+len(PREFIX):].strip()
            if len(encoded)>8192:raise ValueError('artifact envelope size')
            value=json.loads(encoded)
            if value.get('kind')=='begin':
                if active is not None:raise ValueError('nested or incomplete artifact')
                name=safe_name(value['name'])
                if name in seen:raise ValueError('duplicate artifact')
                if (type(value['bytes']) is not int or not 0<=value['bytes']<=MAX_BYTES
                        or type(value['chunks']) is not int or value['chunks']!=(value['bytes']+CHUNK-1)//CHUNK
                        or value['encoding']!='base64' or not re.fullmatch('[0-9a-f]{64}',value['sha256'])):
                    raise ValueError('artifact header')
                path=output/name;path.parent.mkdir(parents=True,exist_ok=True)
                if path.exists():raise ValueError('artifact path collision')
                partial=path.with_name(path.name+'.partial');stream=partial.open('xb')
                active=dict(header=value,path=path,partial=partial,index=0,bytes=0,hasher=hashlib.sha256())
            elif value.get('kind')=='data':
                if active is None or type(value['index']) is not int or value['index']!=active['index']:raise ValueError('artifact chunk order')
                raw=base64.b64decode(value['data'],validate=True)
                expected=min(CHUNK,active['header']['bytes']-active['bytes'])
                if len(raw)!=expected or expected<=0:raise ValueError('artifact chunk length')
                stream.write(raw);active['hasher'].update(raw);active['bytes']+=len(raw);active['index']+=1
            elif value.get('kind')=='end':
                if (active is None or value['name']!=active['header']['name'] or active['index']!=active['header']['chunks']
                        or active['bytes']!=active['header']['bytes'] or active['hasher'].hexdigest()!=active['header']['sha256']):
                    raise ValueError('artifact count/digest mismatch')
                stream.close();stream=None;active['partial'].replace(active['path']);seen.add(value['name'])
                artifacts.append(active['header']);active=None
            else:raise ValueError('artifact envelope kind')
        if active is not None:raise ValueError('incomplete final artifact; partial bytes preserved')
        if not artifacts:raise ValueError('no version-2 artifacts in log')
        return artifacts
    finally:
        if stream:stream.close()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--log',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    with args.log.open(encoding='utf-8') as log:result=recover(log,args.output)
    print(json.dumps(dict(recovered=len(result),artifacts=result),indent=2))


if __name__=='__main__':main()
