#!/usr/bin/env python3
"""Capture project-owned build inputs; never inspect restricted source material."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--compiler-id', required=True)
    parser.add_argument('--compiler-version', required=True)
    parser.add_argument('--build-type', required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    revision = os.environ.get('SOURCE_REVISION', 'unavailable')
    dirty = None
    if (root / '.git').exists():
        revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
        dirty = bool(subprocess.check_output(['git', 'status', '--porcelain'], cwd=root, text=True).strip())
    paths = [root / 'CMakeLists.txt', root / 'tools/build_identity.py']
    paths += sorted((root / 'src').rglob('*'))
    paths += sorted((root / 'cmake').glob('*.cmake'))
    paths += [root / 'gui_dependencies.json', root / 'tools/fetch_gui.py']
    paths += sorted((root / 'python/dialysislab').glob('*.py'))
    paths += sorted((root / 'scenarios').glob('*.json'))
    hashes = {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths if p.is_file()}
    identity = dict(source_revision=revision, worktree_dirty_at_configure=dirty,
                    compiler_id=args.compiler_id, compiler_version=args.compiler_version,
                    build_type=args.build_type, source_sha256=hashes)
    args.output.write_text(json.dumps(identity, indent=2) + '\n')


if __name__ == '__main__':
    main()
