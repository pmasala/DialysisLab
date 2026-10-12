#!/usr/bin/env python3
"""Fetch exact GUI archives over verified TLS; validate cached extracted contents."""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import tarfile
import tempfile
import urllib.request

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''): h.update(block)
    return h.hexdigest()


def fetch(cache, offline=False):
    lock = json.loads((ROOT / 'gui_dependencies.json').read_text())
    cache.mkdir(parents=True, exist_ok=True)
    for item in lock['components']:
        archive, destination = cache / item['archive'], cache / item['directory']
        if not archive.exists():
            if offline: raise ValueError('missing pinned archive: ' + str(archive))
            temporary = archive.with_suffix('.download')
            try:
                with urllib.request.urlopen(item['url'], timeout=60) as response, temporary.open('xb') as output:
                    shutil.copyfileobj(response, output)
                if digest(temporary) != item['sha256']: raise ValueError('archive digest mismatch')
                os.replace(temporary, archive)
            finally:
                temporary.unlink(missing_ok=True)
        if digest(archive) != item['sha256']: raise ValueError('cached archive digest mismatch: ' + str(archive))
        # Derive the expected tree from verified archive bytes, not a writable stamp.
        with tarfile.open(archive, 'r:gz') as source:
            expected = {}
            members = source.getmembers()
            excluded = set(item.get('excluded_archive_links', []))
            if {m.name for m in members if m.issym()} != excluded:
                raise ValueError('unexpected archive link inventory')
            members = [m for m in members if m.name not in excluded]
            for entry in members:
                parts = PurePosixPath(entry.name)
                if parts.is_absolute() or '..' in parts.parts or '\\' in entry.name or parts.parts[0] != item['directory']:
                    raise ValueError('unsafe archive path')
                if not (entry.isfile() or entry.isdir()): raise ValueError('unsupported archive member')
                if entry.isfile():
                    expected[str(parts)] = hashlib.sha256(source.extractfile(entry).read()).hexdigest()
            if destination.exists():
                actual = {}
                for path in destination.rglob('*'):
                    if path.is_symlink(): raise ValueError('dependency symlink')
                    if path.is_file(): actual[str(path.relative_to(cache))] = digest(path)
                if actual != expected: raise ValueError('modified extracted dependency: ' + str(destination))
            else:
                with tempfile.TemporaryDirectory(prefix='gui-', dir=cache) as temporary:
                    staging = Path(temporary)
                    for entry in members:
                        path = staging / entry.name
                        if entry.isdir(): path.mkdir(parents=True, exist_ok=True)
                        else:
                            path.parent.mkdir(parents=True, exist_ok=True)
                            with source.extractfile(entry) as inp, path.open('xb') as out: shutil.copyfileobj(inp, out)
                    os.replace(staging / item['directory'], destination)
        print(item['name'], item['version'], item['sha256'], 'verified')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache', type=Path, default=ROOT / 'build/gui-deps')
    parser.add_argument('--offline', action='store_true')
    args = parser.parse_args()
    fetch(args.cache.resolve(), args.offline)


if __name__ == '__main__': main()
