#!/usr/bin/env python3
"""Headless DX1 client; credentials stay in a private file, never command arguments."""
import argparse
import json
from pathlib import Path
import sys
import time
import uuid
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'python'))
from dialysislab.experiment_rpc import request
from dialysislab.trajectory import strict_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--api-dir', type=Path, required=True)
    parser.add_argument('--wait', action='store_true', help='Wait for started run/artifact job, reporting final status')
    parser.add_argument('operation', choices=('status','presets','draft','load','validate','start','pause','resume','stop','runs','replay','compare','export'))
    parser.add_argument('--config', type=Path)
    parser.add_argument('--preset')
    parser.add_argument('--revision', type=int)
    parser.add_argument('--run-id')
    parser.add_argument('--right')
    parser.add_argument('--request-id', default=uuid.uuid4().hex)
    parser.add_argument('--wall-speed', type=float, default=0)
    args = parser.parse_args()
    op = args.operation.upper()
    payload = {}
    if op in ('LOAD', 'VALIDATE', 'START'):
        revision = args.revision
        if revision is None: revision = request(args.api_dir, 'STATUS')['revision']
        payload['revision'] = revision
    if op == 'LOAD': payload['name'] = args.preset
    if op == 'VALIDATE':
        if not args.config: parser.error('--config required')
        payload['configuration'] = strict_json(args.config.read_bytes())
    if op in ('START', 'REPLAY'): payload.update(request_id=args.request_id, wall_speed=args.wall_speed)
    if op in ('PAUSE', 'RESUME', 'STOP', 'REPLAY', 'EXPORT'): payload['run_id'] = args.run_id
    if op == 'COMPARE': payload = dict(left=args.run_id, right=args.right)
    result = request(args.api_dir, op, payload)
    if args.wait and op in ('START', 'REPLAY', 'COMPARE', 'EXPORT'):
        identifier = result.get('run_id') or result['job_id']
        while True:
            status = request(args.api_dir, 'STATUS')
            if op in ('COMPARE', 'EXPORT'):
                result = status['job']
                if result['id'] != identifier: raise ValueError('artifact job replaced; query history before retry')
                if result['state'] != 'running': break
            else:
                if status['run_id'] != identifier: raise ValueError('run changed while waiting')
                result = status
                if result['state'] not in ('starting','running','pause_requested','paused','stopping'): break
            time.sleep(.1)
    print(json.dumps(result, indent=2, allow_nan=False))
    if args.wait and result.get('state') not in (None, 'completed'): return 1
    return 0


if __name__ == '__main__': sys.exit(main())
