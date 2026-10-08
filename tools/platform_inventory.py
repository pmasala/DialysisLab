#!/usr/bin/env python3
"""Read installed Debian/Ubuntu platform metadata, separate from application licenses."""
import hashlib
import json
from pathlib import Path
import platform
import re
import subprocess
import sys


def inventory(include_python_packages=False):
    fields = '${binary:Package}\t${Version}\t${source:Package}\t${source:Version}\n'
    rows = subprocess.check_output(['dpkg-query', '-W', '-f=' + fields], text=True).splitlines()
    packages = []
    for row in rows:
        name, version, source, source_version = row.split('\t')
        path = Path('/usr/share/doc') / name.split(':')[0] / 'copyright'
        notice = None
        if path.is_file():
            raw = path.read_bytes()
            labels = sorted(set(re.findall(r'^License:\s*(.+)$', raw.decode('utf-8', errors='replace'), re.M)))
            notice = dict(path=str(path), sha256=hashlib.sha256(raw).hexdigest(), declared_labels=labels)
        packages.append(dict(name=name, version=version, source=source or name.split(':')[0],
                             source_version=source_version or version, copyright=notice))
    executable = Path(sys.executable).resolve()
    python_packages=[]
    if include_python_packages:
        from importlib.metadata import distributions
        for distribution in distributions():
            metadata=distribution.metadata
            python_packages.append(dict(name=metadata['Name'],version=distribution.version,
                license=metadata.get('License-Expression') or metadata.get('License'),
                metadata_sha256=hashlib.sha256((distribution.read_text('METADATA') or '').encode()).hexdigest()))
    return dict(schema_version=1, os_release=Path('/etc/os-release').read_text(),
                machine=platform.machine(), packages=packages,
                python_packages=sorted(python_packages,key=lambda p:p['name']),
                python=dict(version=platform.python_version(), executable=str(executable),
                            sha256=hashlib.sha256(executable.read_bytes()).hexdigest(),
                            license='Python-2.0; bundled/platform terms require separate assessment'),
                scope='Installed package inventory and supplied copyright labels, not complete license clearance. '
                      'No inferred license for missing/non-machine-readable notices; no host secrets or datasets read.')


if __name__ == '__main__':
    print(json.dumps(inventory('--python-packages' in sys.argv), indent=2, sort_keys=True))
