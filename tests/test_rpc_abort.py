"""Real plant/decision processes with STEP replies discarded after acceptance."""
import json
import os
from pathlib import Path
import socket
import sys
import threading
import time
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'python'))
from dialysislab import runner
from dialysislab.protocol import ProtocolError, read_line, rpc, state

BUILD = Path(os.environ.get('DIALYSISLAB_BUILD_DIR', ROOT / 'build'))
CONFIG = json.loads((ROOT / 'scenarios/hd_nominal.json').read_text())


class RpcAbortTests(unittest.TestCase):
    def exercise(self, role, halt_failure=None, status_failure=False):
        with runner.LocalCluster(BUILD) as cluster:
            proxy_path = cluster.runtime / 'discard.sock'
            accepted = []
            proxy_errors = []
            calls = []
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as listener:
                listener.bind(str(proxy_path))
                listener.listen(1)
                listener.settimeout(5)

                def discard_reply():
                    try:
                        connection, _ = listener.accept()
                        with connection:
                            fields = read_line(connection, time.monotonic() + 1)
                            # The real service waits for the plant's acknowledgment
                            # before replying. Deliberately discard that STEP reply.
                            accepted.append(rpc(cluster.runtime / role / 'service.sock', *fields))
                    except BaseException as exc:
                        proxy_errors.append(exc)

                proxy = threading.Thread(target=discard_reply)
                proxy.start()

                def routed(path, *fields):
                    calls.append((str(path.relative_to(cluster.runtime)), fields))
                    if path == cluster.runtime / role / 'service.sock' and fields[:3] == ('STEP', 5, 500):
                        return rpc(proxy_path, *fields)
                    if fields == ('HALT',) and halt_failure:
                        if halt_failure == 'lost_reply':
                            rpc(path, *fields)
                        raise TimeoutError('injected HALT ' + halt_failure)
                    if fields == ('STATUS',) and status_failure:
                        raise ConnectionError('injected observation failure')
                    return rpc(path, *fields)

                try:
                    with patch.object(runner, 'rpc', side_effect=routed):
                        records, manifest = runner.simulate(CONFIG, cluster.runtime, BUILD)
                finally:
                    proxy.join(timeout=6)
                self.assertFalse(proxy.is_alive())
                self.assertFalse(proxy_errors, proxy_errors)
                self.assertEqual(accepted, [['OK']] if role == 'control' else [['DECISION', 'none']])
            self.assertEqual(manifest['outcome'], 'aborted')
            self.assertEqual(len(records), 5)
            self.assertTrue(manifest['rpc_failures'][0].startswith(role + ':'))
            tail = [(path, fields[0]) for path, fields in calls if fields[0] in ('STEP', 'HALT', 'STATUS')][-4:]
            self.assertEqual(tail, [('control/service.sock', 'STEP'), ('protection/service.sock', 'STEP'),
                                    ('admin/plant.sock', 'HALT'), ('admin/plant.sock', 'STATUS')])
            self.assertFalse(any(fields[0] in ('COMMIT', 'ADVANCE') and fields[1] == 5 for _, fields in calls))
            stop = manifest['stop']
            self.assertEqual(stop['acknowledged'], halt_failure is None)
            if status_failure:
                self.assertIsNone(stop['outputs_zero_observed'])
                self.assertIsNone(stop['observed_state'])
            elif halt_failure == 'before_delivery':
                self.assertFalse(stop['outputs_zero_observed'])
                self.assertEqual(stop['observed_state']['blood_mL_min'], 300)
            else:
                self.assertTrue(stop['outputs_zero_observed'])
                self.assertEqual(stop['observed_state']['time_ms'], 500)
            if halt_failure:
                self.assertIsNone(stop['pending_tick_cancelled'])
                self.assertIsNotNone(stop['request_error'])
            if halt_failure == 'before_delivery':
                # HALT was never delivered. Independently observe the wall lease;
                # the manifest must not retroactively claim this later observation.
                time.sleep(2.15)
            observed = state(rpc(cluster.runtime / 'admin/plant.sock', 'STATUS'))
            self.assertTrue(observed['latched'] and observed['clamp_closed'])
            self.assertEqual(observed['blood_mL_min'], 0)
            self.assertEqual(observed['time_ms'], 500)
            self.assertAlmostEqual(observed['removed_total_mL'], 5 * 10 * 100 / 60000)
            for command in [('COMMIT', 5, 500), ('PREPARE', 5, 500, 100, 0.5, 'none', 'none'),
                            ('PERMIT', 5, 500), ('DEMAND', 5, 500, 300, 10)]:
                path = ('protection' if command[0] == 'PERMIT' else
                        'control' if command[0] == 'DEMAND' else 'admin')
                with self.assertRaises(ProtocolError):
                    rpc(cluster.runtime / path / 'plant.sock', *command)
            after = state(rpc(cluster.runtime / 'admin/plant.sock', 'STATUS'))
            self.assertEqual(after, observed)
            return manifest

    def test_control_step_reply_lost_after_plant_acceptance(self):
        self.exercise('control')

    def test_protection_step_reply_lost_after_plant_acceptance(self):
        self.exercise('protection')

    def test_halt_not_delivered_reports_observed_running_outputs(self):
        self.exercise('control', halt_failure='before_delivery')

    def test_halt_reply_lost_keeps_acknowledgment_distinct_from_observation(self):
        self.exercise('protection', halt_failure='lost_reply')

    def test_halt_and_status_failures_leave_output_state_unknown(self):
        self.exercise('control', halt_failure='before_delivery', status_failure=True)

    def test_halt_acknowledgment_is_not_an_output_observation(self):
        self.exercise('protection', status_failure=True)
