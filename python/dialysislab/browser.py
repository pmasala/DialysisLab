"""Deterministic local scheduling of unchanged Plant and coupled patient equations."""
import copy
import json
from . import circuit, treatment, machine, physical
from .compartments import Compartments, validate_snapshot
from .protocol import message, expect, ProtocolError
from .runner import validate


class BrowserSession:
    def __init__(self, config, transport, epoch):
        self.config = validate(copy.deepcopy(config))
        if self.config['schema_version'] != 5 or 'physical' not in self.config:
            raise ValueError('browser requires coupled physical schema 5')
        if self.config['faults'] or self.config['workflow']:
            raise ValueError('browser interactive profile requires empty timelines')
        self.raw = transport
        self.epoch = epoch
        self.n = 0
        self.snapshot = None
        self.record = None
        self.failed = False
        # These modules use the same configuration encoders as the native runner.
        # One session owns each worker/interpreter; no concurrent global patching.
        for module in (circuit, treatment, machine, physical):
            module.rpc = self.call
        circuit.configure(0, self.config)
        treatment.configure(0, self.config)
        machine.configure(0, self.config)
        self.patient = Compartments(physical.patient_configuration(self.config), True, True)

    def call(self, role, *fields):
        frame = str(self.raw(int(role), message(*fields)))
        parts = frame.split()
        if not parts or parts[0] != 'DL1' or 'BROWSER_ERROR' in parts:
            raise ProtocolError(frame)
        return parts[1:]

    def command(self, role, action, epoch, values=''):
        if epoch != self.epoch:
            return 'rejected_old_session'
        channel = 5 + int(role)
        if action in ('STOP', 'ACK', 'SILENCE'):
            expect(self.call(channel, action+'6', epoch, *values.split()), 'OK', 1)
            return 'acknowledged'
        response = self.call(channel, 'PRESCRIBE6', epoch, *values.split()) if action == 'PRESCRIBE' else self.call(channel, 'REQUEST6', epoch, action)
        if response[0] == 'REJECT':
            return 'rejected_' + '_'.join(response[1:])
        token = expect(response, 'CONFIRM5', 2)[1]
        expect(self.call(channel, 'CONFIRM6', epoch, token), 'QUEUED5', 2)
        return 'queued'

    def views(self):
        return [str(self.raw(role, message('STATUS6', self.epoch))) for role in (5, 6)]

    def step(self):
        if self.failed:
            raise RuntimeError('session failed; reset required')
        if self.n >= self.config['ticks']:
            raise RuntimeError('configured tick limit reached')
        try:
            return self._step()
        except Exception:
            self.failed = True
            self.call(5, 'STOP6', self.epoch)
            raise

    def _step(self):
        c = self.config
        n, dt = self.n, c['dt_ms']
        t = n * dt
        if self.snapshot is not None:
            circuit.transport(0, c, self.snapshot['concentration_mmol_L'][2])
            physical.update_blood(0, self.snapshot)
        expect(self.call(0, 'PREPARE', n, t, dt, c['resistance_mmHg_min_mL'], 'none', 'none'), 'OK', 1)
        expect(self.call(3, 'STEP5', n, t), 'OK', 1)
        expect(self.call(4, 'STEP5', n, t), 'DECISION', 2)
        r = machine.committed(self.call(0, 'COMMIT5', n, t))
        m, h, o = r['machine'], r['circuit'], r['online']
        g = m['guided']
        rinse = bool(g['return_in_tick_mL'] or g['return_out_tick_mL'])
        q = dict(sequence=n, time_ms=t, dt_ms=dt,
                 draw_mL=max(0,h['draw_tick_mL']-m['flush_in_tick_mL']),
                 return_mL=max(0,h['return_tick_mL']-m['flush_out_tick_mL']),
                 uf_mL=h['uf_tick_mL'], stored_mL=h['stored_mL'],
                 clearance_mL_min=h['clearance_mL_min'], sieving=c['circuit']['profile']['sieving'],
                 dialysate_mmol_L=o['concentration_mmol_L'], pre_mL=o['pre_tick_mL'], post_mL=o['post_tick_mL'],
                 substitution_mmol_L=o['concentration_mmol_L'], flush_in_mL=m['flush_in_tick_mL'],
                 flush_out_mL=m['flush_out_tick_mL'], flush_mmol_L=[0,154,0,154,0,0] if rinse else o['concentration_mmol_L'],
                 rinseback=rinse)
        physical.attach_transaction(q, r, c)
        self.snapshot = validate_snapshot(self.patient.advance(q), True, True)
        r['patient'] = self.snapshot
        self.record = r
        self.n += 1
        return r

    def export(self):
        return json.dumps(dict(config=self.config, ticks=self.n, record=self.record), allow_nan=False)
