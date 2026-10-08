#!/usr/bin/env python3
"""Read fixed application paths inside an immutable DialysisLab image."""
import hashlib
import json
from pathlib import Path


def digest(path):
    hasher=hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda:stream.read(65536),b''):hasher.update(chunk)
    return hasher.hexdigest()


def inspect_application():
    root=Path('/opt/dialysislab');binary=Path('/opt/bin')
    path=binary/'build_identity.json'
    if path.stat().st_size>1024*1024:raise ValueError('build identity too large')
    raw=path.read_bytes()
    files=list(sorted((root/'python/dialysislab').glob('*.py')))
    files+=list(sorted((root/'scenarios').glob('*.json')))
    if (root/'gui_dependencies.json').exists():files.append(root/'gui_dependencies.json')
    return dict(schema_version=1,build=json.loads(raw),build_file_sha256=hashlib.sha256(raw).hexdigest(),
                binary_sha256={name:digest(binary/name) for name in
                    ('plant','control','protection','child-guard','device-ui','sim-console') if (binary/name).is_file()},
                runtime_source_sha256={str(p.relative_to(root)):digest(p) for p in files},
                build_packages_sha256=digest(binary/'build-packages.txt'))


if __name__=='__main__':print(json.dumps(inspect_application(),sort_keys=True,indent=2))
