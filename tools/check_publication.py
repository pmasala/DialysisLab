#!/usr/bin/env python3
"""Validate public file formats and the deny-by-default Docker context."""
import json
from pathlib import Path
from package_release import collect


def inspect_context(root, manifest):
    lines = [line.strip() for line in (root / '.dockerignore').read_text().splitlines()
             if line.strip() and not line.startswith('#')]
    if not lines or lines[0] != '**':
        raise ValueError('Docker context must start deny-all')
    paths = []
    for line in lines[1:]:
        if not line.startswith('!') or any(char in line[1:] for char in '*?[]'):
            raise ValueError('Docker context permits only explicit paths')
        name = line[1:]
        if name.endswith('/'):
            raise ValueError('Docker context must not admit whole directories')
        if name not in manifest['files']:
            raise ValueError('Docker input is not a reviewed public file: ' + name)
        paths.append(name)
    collect(root, {'files': paths})
    return paths


def main():
    root = Path(__file__).resolve().parents[1]
    manifest = json.loads((root / 'publication_manifest.json').read_text())
    files = collect(root, manifest)
    context = inspect_context(root, manifest)
    print(json.dumps({'reviewed_public_files': len(files), 'docker_context_files': context,
                      'scope': 'Allowlist/format checks; not a substitute for content/rights review.'}, indent=2))


if __name__ == '__main__':
    main()
