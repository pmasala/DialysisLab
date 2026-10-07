#!/usr/bin/env python3
"""Package reviewed public text files only. This is not release approval."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import zipfile


def collect(root, manifest):
    paths = manifest['files']
    if not paths or len(paths) != len(set(paths)):
        raise ValueError('publication list is empty or contains duplicates')
    sources = json.loads((root / 'assurance/standards/sources.json').read_text())
    restricted_hashes = {s['sha256'] for ref in sources['standards'] for s in ref['supplied_sources']}
    result = []
    for name in paths:
        posix = PurePosixPath(name)
        if posix.is_absolute() or '..' in posix.parts or '\\' in name:
            raise ValueError('unsafe publication path')
        path = root / name
        if any(p.is_symlink() for p in [path, *path.parents]):
            raise ValueError('symlink publication input rejected')
        if root not in path.resolve().parents:
            raise ValueError('publication input outside project')
        if path.suffix not in {'.md', '.json', '.py', '.cpp', '.hpp', '.yaml'} and name not in {
                '.gitignore', '.dockerignore', 'LICENSE', 'Dockerfile', 'CMakeLists.txt'}:
            raise ValueError('unsupported publication format: ' + name)
        raw = path.read_bytes()
        raw.decode('utf-8')
        if raw.startswith((b'%PDF-', b'PK\x03\x04')) or b'\x00' in raw:
            raise ValueError('binary content in text publication input')
        if hashlib.sha256(raw).hexdigest() in restricted_hashes:
            raise ValueError('restricted source detected')
        result.append((name, raw))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    manifest = json.loads((root / 'publication_manifest.json').read_text())
    files = collect(root, manifest)
    if args.output.resolve() == root or root in args.output.resolve().parents:
        raise ValueError('write the package outside the project')
    # Validate all inputs before opening the output, preserving any previous
    # package when the publication list fails validation.
    with zipfile.ZipFile(args.output, 'w', compression=zipfile.ZIP_DEFLATED) as out:
        for name, raw in files:
            info = zipfile.ZipInfo('DialysisLab/' + name, date_time=(2026, 10, 7, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            out.writestr(info, raw)
    print(f'Packaged {len(files)} reviewed text files. Licensed sources excluded; no release approval implied.')


if __name__ == '__main__':
    main()
