"""Single synthetic fluid compartment. Only explicit ADVANCE integrates volume."""
import argparse
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

    def status(self):
        return message('VOLUME', self.last_sequence, self.time_ms, self.volume, self.removed)

    def handle(self, request):
        if request == ['PING']:
            return 'DL1 OK'
        if request == ['STOP']:
            self.stopping = True
            return 'DL1 OK'
        if request == ['STATUS']:
            return self.status()
        if len(request) == 2 and request[0] == 'INIT' and self.initial is None:
            real(request[1], 1000, 100000)
            self.initial = self.volume = Decimal(request[1])
            self.removed = Decimal(0)
            return 'DL1 OK'
        if len(request) == 5 and request[0] == 'ADVANCE' and self.initial is not None:
            seq, start, dt = (integer(v) for v in request[1:4])
            if seq != self.next_sequence or start != self.time_ms or not 1 <= dt <= 1000:
                raise ProtocolError('tick order')
            real(request[4], 0, 20 * dt / 60000)
            removed = Decimal(request[4])
            if removed > self.volume:
                raise ProtocolError('negative volume')
            self.volume -= removed
            self.removed += removed
            self.last_sequence = seq
            self.next_sequence += 1
            self.time_ms += dt
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
