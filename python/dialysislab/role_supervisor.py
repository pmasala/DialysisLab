"""One fixed service per container; activation contains an identifier, never truth."""
import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
from .experiment_rpc import IDENTIFIER
from .experiments import atomic, bounded_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--role', required=True, choices=('plant', 'control', 'protection', 'patient'))
    parser.add_argument('--runtime-dir', type=Path, default=Path('/run/dialysis'))
    parser.add_argument('--activation-dir', type=Path, default=Path('/activation'))
    parser.add_argument('--build-dir', type=Path, default=Path('/opt/bin'))
    args = parser.parse_args()
    stopping, process, current, log, temporary, owner_dir = False, None, None, None, None, None
    def interrupt(_signum, _frame):
        nonlocal stopping
        stopping = True
    signal.signal(signal.SIGTERM, interrupt); signal.signal(signal.SIGINT, interrupt)
    def finish():
        nonlocal process, log, temporary
        if process:
            if process.poll() is None: process.terminate()
            try: process.wait(timeout=3)
            except subprocess.TimeoutExpired: process.kill(); process.wait(timeout=3)
            log.close()
            atomic(owner_dir / 'exited.json', dict(role=args.role, returncode=process.returncode))
            temporary.cleanup()
            process, log, temporary = None, None, None
    try:
        while not stopping:
            try:
                record = bounded_json(args.activation_dir / 'active.json')
                if set(record) != {'schema_version', 'run_id'} or record['schema_version'] != 1:
                    raise ValueError('activation schema')
                active = record['run_id']
                if active is not None and (not isinstance(active, str) or not IDENTIFIER.fullmatch(active)):
                    raise ValueError('activation identifier')
            except FileNotFoundError: active = None
            if active != current:
                finish()
                current = active
                if active:
                    roles = {'plant': ('admin', 'control', 'protection'), 'control': ('control',),
                             'protection': ('protection',), 'patient': ('patient',)}[args.role]
                    temporary = tempfile.TemporaryDirectory(prefix='dl-role-')
                    runtime = Path(temporary.name)
                    for role in roles:
                        path = args.runtime_dir / role / active
                        path.mkdir(parents=True, exist_ok=True)
                        if path.is_symlink(): raise ValueError('unsafe role path')
                        (runtime / role).symlink_to(path)
                    if args.role in ('control', 'protection'):
                        device = args.runtime_dir / 'device' / args.role
                        endpoint = device / active
                        endpoint.mkdir()
                        (runtime / 'device').mkdir()
                        (runtime / 'device' / args.role).symlink_to(endpoint)
                    owner_dir = args.runtime_dir / ('admin' if args.role == 'plant' else args.role) / active
                    log = (owner_dir / (args.role + '.log')).open('x')
                    command = [sys.executable, '-m', 'dialysislab.patient'] if args.role == 'patient' else [str(args.build_dir / args.role)]
                    guarded = [str(args.build_dir / 'child-guard'), str(os.getpid())] + command
                    process = subprocess.Popen(guarded + ['--runtime-dir', str(runtime)], stdout=log, stderr=log)
                    if args.role in ('control', 'protection'):
                        link = device / 'service.sock.tmp'
                        link.symlink_to(Path(active) / 'service.sock')
                        os.replace(link, device / 'service.sock')
            # Never restart a crashed child in the same session. The runner sees
            # the process loss; only a new activation ID can launch fresh state.
            time.sleep(.02)
    finally: finish()


if __name__ == '__main__': main()
