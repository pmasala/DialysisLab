"""DX1 bounded administrative channel, separate from device DL1 endpoints."""
import json
from pathlib import Path
import re
import socket
import time
from .trajectory import strict_json

MAX_JSON = 262144
MAX_FRAME = MAX_JSON * 2 + 256
TOKEN = re.compile(r'[0-9a-f]{64}\Z')
IDENTIFIER = re.compile(r'r[0-9a-f]{16}\Z')
REQUEST_ID = re.compile(r'[0-9a-f]{32}\Z')


def payload(value):
    raw = json.dumps(value, ensure_ascii=True, separators=(',', ':'), allow_nan=False).encode('ascii')
    if len(raw) > MAX_JSON: raise ValueError('JSON size limit')
    return raw.hex()


def decode(value):
    if len(value) > MAX_JSON * 2 or not re.fullmatch(r'(?:[0-9a-f]{2})*', value):
        raise ValueError('invalid encoded JSON')
    return strict_json(bytes.fromhex(value).decode('utf-8'))


def line(connection):
    data = bytearray()
    deadline = time.monotonic() + 2
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0: raise TimeoutError('frame deadline')
        connection.settimeout(remaining)
        block = connection.recv(min(65536, MAX_FRAME + 1 - len(data)))
        if not block: raise ValueError('incomplete frame')
        data.extend(block)
        if len(data) > MAX_FRAME: raise ValueError('frame size limit')
        if b'\n' in block:
            if data.count(b'\n') != 1 or not data.endswith(b'\n'): raise ValueError('extra frame data')
            return data[:-1].decode('ascii')


def request(directory, op, value=None, token=None, timeout=2):
    directory = Path(directory)
    if token is None: token = (directory / 'token').read_text().strip()
    if not TOKEN.fullmatch(token): raise ValueError('credential format')
    if not re.fullmatch('[A-Z]+', op): raise ValueError('operation format')
    raw = ('DX1 ' + token + ' ' + op + ' ' + payload(value or {}) + '\n').encode('ascii')
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
        connection.settimeout(timeout)
        connection.connect(str(directory / 'broker.sock'))
        connection.sendall(raw)
        parts = line(connection).split(' ', 7)
    if len(parts) != 8 or parts[0] != 'DX1' or parts[1] not in ('OK', 'ERROR'): raise ValueError('reply schema')
    result = decode(parts[7])
    if parts[1] == 'ERROR': raise ValueError(result['error'])
    return result
