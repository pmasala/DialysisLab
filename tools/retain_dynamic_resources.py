#!/usr/bin/env python3
"""Retain only named current resource reports; trajectories remain archived locally."""
import argparse
import json
from pathlib import Path
from ci_artifacts import emit


def retain(root, stream=None):
    names=['integration.json','integrated_dynamic_hdf_100000.json']
    for repetition in (1,2):
        folder='integrated_dynamic_hdf_100000-'+str(repetition)+'/'
        names += [folder+name for name in ('collection.json','compose.log','services.log','RECOVERY.txt',
            'results/run/manifest.json','results/run/trajectory-storage.json')]
    found=[]
    for name in names:
        path=root/name
        if path.is_file() and not path.is_symlink():
            emit('dynamic-resources/'+name,path.read_bytes(),stream=stream);found.append(name)
    return found


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--root',type=Path,required=True)
    args=parser.parse_args();files=retain(args.root)
    print(json.dumps(dict(retained=files,scope='Identified reports/logs only; no claim that failed or absent runs passed. Full raw trajectories are not uploaded.')))


if __name__=='__main__':main()
