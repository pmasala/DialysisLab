"""Versioned, bounded-memory trajectory storage and complete-prefix recovery."""
import hashlib
import itertools
import json
import math
from pathlib import Path
import tempfile

FORMAT = 'dialysislab.trajectory.jsonl.v1'
MAX_RECORD_BYTES = 16384


def strict_json(raw):
    """Bounded JSON with unique keys, finite numbers and at most 32 nesting levels."""
    if len(raw) > 1024 * 1024:
        raise ValueError('JSON size limit')
    if isinstance(raw, bytes):
        raw = raw.decode('utf-8')
    # Check depth before invoking the recursive decoder (including Python 3.9).
    depth, quoted, escaped = 0, False, False
    for char in raw:
        if quoted:
            if escaped: escaped = False
            elif char == '\\': escaped = True
            elif char == '"': quoted = False
        elif char == '"': quoted = True
        elif char in '[{':
            depth += 1
            if depth > 32: raise ValueError('JSON nesting limit')
        elif char in ']}': depth -= 1
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result: raise ValueError('duplicate JSON key')
            result[key] = value
        return result
    def bounded_integer(token):
        if len(token) > 128: raise ValueError('JSON integer length limit')
        return int(token)
    def nonfinite(token):
        raise ValueError('nonfinite JSON number: ' + token)
    def finite_float(token):
        value = float(token)
        if not math.isfinite(value):
            nonfinite(token)
        return value
    return json.loads(raw, parse_constant=nonfinite, parse_float=finite_float,
                      parse_int=bounded_integer, object_pairs_hook=unique)


def canonical(data):
    return json.dumps(data, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n'


def read_records(path, recover=False):
    """Read complete LF-terminated records; recovery ignores only a torn final line."""
    with Path(path).open('rb') as stream:
        for expected in itertools.count():
            raw = stream.readline(MAX_RECORD_BYTES + 1)
            if not raw:
                return
            if len(raw) > MAX_RECORD_BYTES:
                raise ValueError('trajectory record exceeds size bound')
            if not raw.endswith(b'\n'):
                if recover:
                    return
                raise ValueError('incomplete final trajectory record')
            record = strict_json(raw)
            if type(record.get('sequence')) is not int or record['sequence'] != expected:
                raise ValueError('trajectory sequence mismatch')
            yield record


def scan(path, recover=False):
    """Independent byte hash/count of the parseable complete prefix; no full copies."""
    hasher = hashlib.sha256()
    count = size = 0
    first = last = None
    with Path(path).open('rb') as stream:
        while True:
            raw = stream.readline(MAX_RECORD_BYTES + 1)
            if not raw:
                break
            if len(raw) > MAX_RECORD_BYTES:
                raise ValueError('trajectory record exceeds size bound')
            if not raw.endswith(b'\n'):
                if recover:
                    break
                raise ValueError('incomplete final trajectory record')
            record = strict_json(raw)
            if type(record.get('sequence')) is not int or record['sequence'] != count:
                raise ValueError('trajectory sequence mismatch')
            hasher.update(raw)
            size += len(raw)
            count += 1
            if first is None:
                first = record
            last = record
    return dict(format=FORMAT, records=count, complete_bytes=size, sha256=hasher.hexdigest(),
                discarded_tail_bytes=Path(path).stat().st_size - size, first=first, last=last)


class Trajectory:
    """Disk-backed result view. Index lookup scans; slices are lazy iterators."""
    def __init__(self, path, count=0, temporary=None):
        self.path = Path(path)
        self.count = count
        self._temporary = temporary  # Own temporary output for the lifetime of this view.

    def __len__(self):
        return self.count

    def __del__(self):
        if self._temporary is not None:
            self._temporary.cleanup()

    def __iter__(self):
        return read_records(self.path)

    def __getitem__(self, index):
        if isinstance(index, slice):
            start, stop, step = index.indices(self.count)
            if step < 1:
                raise ValueError('only forward streaming slices are supported')
            return itertools.islice(iter(self), start, stop, step)
        if index < 0:
            index += self.count
        if not 0 <= index < self.count:
            raise IndexError(index)
        return next(itertools.islice(iter(self), index, index + 1))


class TrajectoryWriter:
    def __init__(self, output=None):
        temporary = None
        if output is None:
            temporary = tempfile.TemporaryDirectory(prefix='dl-records-')
            directory = Path(temporary.name)
        else:
            directory = Path(output)
            directory.mkdir(parents=True, exist_ok=False)
        self.directory = directory
        self.trajectory = Trajectory(directory / 'trajectory.jsonl', temporary=temporary)
        self.stream = self.trajectory.path.open('xb', buffering=0)
        self.hasher = hashlib.sha256()
        self.bytes_written = 0

    def append(self, record):
        if record.get('sequence') != len(self.trajectory):
            raise ValueError('trajectory sequence mismatch')
        raw = canonical(record).encode('utf-8')
        if len(raw) > MAX_RECORD_BYTES:
            raise ValueError('trajectory record exceeds size bound')
        pending = memoryview(raw)
        while pending:
            written = self.stream.write(pending)
            if not written:
                raise OSError('trajectory write made no progress')
            # Hash exactly the prefix successfully written, including short writes.
            self.hasher.update(pending[:written])
            self.bytes_written += written
            pending = pending[written:]
        self.trajectory.count += 1

    def write_manifest(self, manifest):
        temporary = self.directory / 'manifest.json.tmp'
        temporary.write_text(json.dumps(manifest, indent=2, allow_nan=False) + '\n')
        temporary.replace(self.directory / 'manifest.json')

    def close(self):
        self.stream.close()
