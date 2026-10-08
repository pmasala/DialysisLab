#!/usr/bin/env python3
"""Launch actual separate native services and LVGL; operator UI has no clock access."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import signal
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'python'))
from dialysislab.runner import LocalCluster, simulate, validate, stop_plant


def main():
    def interrupt(signum, _frame): raise InterruptedError('demo signal ' + str(signum))
    signal.signal(signal.SIGTERM, interrupt); signal.signal(signal.SIGINT, interrupt)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build-dir', type=Path, default=ROOT / 'build/gui')
    parser.add_argument('--config', type=Path, default=ROOT / 'scenarios/device_interactive.json')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--wall-speed', type=float, default=1)
    parser.add_argument('--headless', action='store_true')
    parser.add_argument('--seconds', type=int, default=0, help='Optional wall duration; zero until operator closes window')
    args = parser.parse_args()
    if args.headless and not args.seconds: parser.error('headless demo requires --seconds')
    if not 0 <= args.seconds <= 86400 or not 0 < args.wall_speed <= 1000: parser.error('duration/speed range')
    config = validate(json.loads(args.config.read_text()))
    args.output.mkdir(parents=True, exist_ok=False)
    with LocalCluster(args.build_dir) as cluster, (args.output / 'device-ui.log').open('w') as log:
        argv = [str(args.build_dir.resolve() / 'device-ui'), '--runtime-dir', str(cluster.runtime),
                '--capture-dir', str(args.output.resolve() / 'captures'), '--duration-ms', str(args.seconds * 1000)]
        if args.headless: argv.append('--headless')
        ui = subprocess.Popen(argv, stdout=log, stderr=subprocess.STDOUT)
        window_closed = False
        def check_window(_tick=None):
            nonlocal window_closed
            if ui.poll() is not None:
                window_closed = True
                raise InterruptedError('device window closed, exit=' + str(ui.returncode))
        try:
            _, manifest = simulate(config, cluster.runtime, args.build_dir, args.output / 'run', check_window, args.wall_speed, wait_check=check_window)
            stopped = manifest.get('stop') or stop_plant(cluster.runtime / 'admin/plant.sock', True)
        finally:
            if ui.poll() is None: ui.terminate()
            try: ui.wait(timeout=5)
            except subprocess.TimeoutExpired: ui.kill(); ui.wait()
        result = dict(executed_at=datetime.now(timezone.utc).isoformat(), ui_command=argv, ui_exit=ui.returncode,
                      run_outcome=manifest['outcome'], run_errors=manifest['errors'], expected_window_closure=window_closed and ui.returncode == 0,
                      stop=stopped, display=os.environ.get('DISPLAY'), command=sys.argv)
        (args.output / 'demo.json').write_text(json.dumps(result, indent=2) + '\n')
        print(json.dumps(result, indent=2))
        expected = manifest['outcome'] == 'completed' or (window_closed and ui.returncode == 0
                   and manifest['errors'] == ['device window closed, exit=0'])
        return 0 if expected and ui.returncode == 0 and stopped.get('outputs_zero_observed', False) else 1


if __name__ == '__main__': sys.exit(main())
