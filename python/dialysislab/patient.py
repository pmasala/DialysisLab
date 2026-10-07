"""Single synthetic fluid compartment. Only explicit ADVANCE integrates volume."""
import argparse
import json
from decimal import Decimal
import signal
import socket
import time
from pathlib import Path
from .protocol import ProtocolError, integer, message, read_line, real


class Patient:
    def __init__(self):
        self.initial = None
        self.volume = self.removed = 0.0
        self.next_sequence = self.time_ms = self.last_sequence = 0
        self.stopping = False
        self.numerical_correction = Decimal(0)
        self.numerical_correction_absolute = Decimal(0)
        self.compartments = None

    def status(self):
        return message('VOLUME', self.last_sequence, self.time_ms, self.volume, self.removed)

    def handle(self, request):
        if request == ['PING']:
            return 'DL1 OK'
        if request == ['STOP']:
            self.stopping = True
            return 'DL1 OK'
        if request == ['STATUS']:
            if self.compartments is not None:
                raise ProtocolError('coupled patient requires STATUS3')
            return self.status()
        if len(request) == 2 and request[0] in ('INIT3', 'INIT4') and self.initial is None and self.compartments is None:
            from .compartments import Compartments
            self.compartments = Compartments(json.loads(request[1]), online=request[0] == 'INIT4')
            return 'DL1 OK'
        if self.compartments is not None:
            version = '4' if self.compartments.online else '3'
            if request == ['STATUS' + version]:
                result = self.compartments.snapshot()
            elif len(request) == 2 and request[0] == 'ADVANCE' + version:
                result = self.compartments.advance(json.loads(request[1]))
            else:
                raise ProtocolError('coupled patient operation')
            return message('PATIENT' + version, json.dumps(result, sort_keys=True, separators=(',', ':'), allow_nan=False))
        if len(request) == 2 and request[0] == 'INIT' and self.initial is None:
            real(request[1], 1000, 100000)
            self.initial = self.volume = Decimal(request[1])
            self.removed = Decimal(0)
            return 'DL1 OK'
        if len(request) == 5 and request[0] in ('ADVANCE', 'FLUID2') and self.initial is not None:
            seq, start, dt = (integer(v) for v in request[1:4])
            if seq != self.next_sequence or start != self.time_ms or not 1 <= dt <= 1000:
                raise ProtocolError('tick order')
            if request[0] == 'ADVANCE':
                real(request[4], 0, 20 * dt / 60000)
            else:
                real(request[4], -100000, 100000)
            removed = Decimal(request[4])
            proposed = self.volume - removed
            correction = Decimal(0)
            if request[0] == 'FLUID2':
                bounded = max(Decimal(0), min(Decimal(100000), proposed))
                correction = bounded - proposed
                if abs(correction) > Decimal('1e-9') or self.numerical_correction_absolute + abs(correction) > Decimal('1e-8'):
                    raise ProtocolError('volume bounds / numerical correction budget')
                proposed = bounded
            if not 0 <= proposed <= 100000:
                raise ProtocolError('volume bounds')
            self.volume = proposed
            self.removed += removed
            self.numerical_correction += correction
            self.numerical_correction_absolute += abs(correction)
            self.last_sequence = seq
            self.next_sequence += 1
            self.time_ms += dt
            if request[0] == 'FLUID2':
                return message('FLUID_VOLUME2', self.last_sequence, self.time_ms, self.volume,
                               self.removed, self.numerical_correction)
            return self.status()
        raise ProtocolError('operation')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime-dir', required=True, type=Path)
    args = parser.parse_args()
    path = args.runtime_dir / 'patient/service.sock'
    patient = Patient()
    def stop(_signum, _frame):
        patient.stopping = True
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as listener:
        listener.bind(str(path))  # Never remove an existing socket implicitly.
        path.chmod(0o660)
        listener.listen(16)
        listener.settimeout(0.1)
        try:
            while not patient.stopping:
                try:
                    connection, _ = listener.accept()
                except socket.timeout:
                    continue
                with connection:
                    try:
                        request = read_line(connection, time.monotonic() + 0.5)
                        response = patient.handle(request)
                    except (OSError, ValueError, IndexError):
                        response = 'DL1 ERR protocol'
                    try:
                        connection.settimeout(0.05)
                        connection.sendall((response + '\n').encode('ascii'))
                    except OSError:
                        pass
        finally:
            path.unlink(missing_ok=True)


if __name__ == '__main__':
    main()
