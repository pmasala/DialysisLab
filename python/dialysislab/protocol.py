"""DL1 bounded local transport; no simulation time derived from wall time."""
import math
import socket
import time
from pathlib import Path


class ProtocolError(ValueError):
    pass


def message(*fields):
    return 'DL1 ' + ' '.join(format(x, '.17g') if isinstance(x, float) else str(x) for x in fields)


def read_line(connection, deadline):
    data = bytearray()
    while len(data) < 4096:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError('RPC deadline')
        connection.settimeout(remaining)
        char = connection.recv(1)
        if char == b'\n':
            try:
                tokens = data.decode('ascii').split()
            except UnicodeError as exc:
                raise ProtocolError('encoding') from exc
            if not tokens or tokens.pop(0) != 'DL1':
                raise ProtocolError('version')
            return tokens
        if not char or not 32 <= char[0] <= 126:
            raise ProtocolError('incomplete or non-ASCII frame')
        data.extend(char)
    raise ProtocolError('oversize')


def rpc(path, *fields):
    data = (message(*fields) + '\n').encode('ascii')
    if len(data) > 4096:
        raise ProtocolError('oversize')
    deadline = time.monotonic() + 0.5
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
        connection.settimeout(0.5)
        connection.connect(str(path))
        connection.sendall(data)
        response = read_line(connection, deadline)
    if not response or response[0] == 'ERR':
        raise ProtocolError('peer rejected request')
    return response


def expect(response, name, length):
    if len(response) != length or response[0] != name:
        raise ProtocolError('response schema')
    return response


def integer(value, maximum=100000000):
    if not isinstance(value, str) or not value.isascii() or not value.isdecimal():
        raise ProtocolError('integer')
    number = int(value)
    if number > maximum:
        raise ProtocolError('integer range')
    return number


def real(value, low, high):
    number = float(value)
    if not math.isfinite(number) or not low <= number <= high:
        raise ProtocolError('real range')
    return number


def wait_ready(runtime, timeout=10):
    deadline = time.monotonic() + timeout
    pending = [Path(runtime) / path for path in
               ('admin/plant.sock', 'control/service.sock', 'protection/service.sock', 'patient/service.sock')]
    while pending:
        for path in pending[:]:
            try:
                expect(rpc(path, 'PING'), 'OK', 1)
                pending.remove(path)
            except (OSError, ValueError):
                pass
        if time.monotonic() >= deadline:
            raise TimeoutError('services not ready: ' + ', '.join(str(p) for p in pending))
        if pending:
            time.sleep(0.02)


def heartbeat(runtime):
    for path in ('control/service.sock', 'protection/service.sock', 'admin/plant.sock'):
        expect(rpc(Path(runtime) / path, 'PING'), 'OK', 1)


def pause(runtime, seconds):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        heartbeat(runtime)
        time.sleep(min(0.1, max(0, deadline - time.monotonic())))


def state(response):
    expect(response, 'STATE', 11)
    return dict(sequence=integer(response[1]), time_ms=integer(response[2]),
                blood_mL_min=real(response[3], 0, 500), pressure_mmHg=real(response[4], 0, 1000),
                uf_mL_min=real(response[5], 0, 20), removed_total_mL=real(response[6], 0, 100000),
                removed_tick_mL=real(response[7], 0, 1), latched=bool(integer(response[8], 1)),
                clamp_closed=bool(integer(response[9], 1)), reason=response[10])


def observation(response):
    expect(response, 'OBS', 7)
    return dict(sequence=integer(response[1]), time_ms=integer(response[2]), valid=integer(response[3], 1),
                blood_mL_min=real(response[4], 0, 500), pressure_mmHg=real(response[5], 0, 1000),
                uf_mL_min=real(response[6], 0, 20))
