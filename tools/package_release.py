#!/usr/bin/env python3
"""Package reviewed public source files and individually registered owned captures. This is not release approval."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import zipfile
import xml.etree.ElementTree as ET


def validate_owned_svg(raw, asset):
    """Accept only registered project diagrams with a small passive SVG vocabulary."""
    if not isinstance(asset, dict) or asset.get('origin') != 'project-authored-diagram' or not asset.get('command'):
        raise ValueError('unregistered owned diagram')
    if asset.get('sha256') != hashlib.sha256(raw).hexdigest():
        raise ValueError('owned diagram digest')
    if b'<!' in raw or b'<?' in raw:
        raise ValueError('SVG declarations are not allowed')
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as error:
        raise ValueError('invalid SVG') from error
    namespace = '{http://www.w3.org/2000/svg}'
    if root.tag != namespace + 'svg':
        raise ValueError('invalid SVG root')
    tags = {'svg', 'title', 'desc', 'rect', 'path', 'circle', 'text'}
    attributes = {'width', 'height', 'viewBox', 'role', 'x', 'y', 'fill',
                  'font-family', 'font-size', 'font-weight', 'text-anchor',
                  'd', 'stroke', 'stroke-width', 'stroke-linejoin', 'stroke-linecap',
                  'stroke-dasharray', 'cx', 'cy', 'r'}
    for element in root.iter():
        if element.tag not in {namespace + name for name in tags}:
            raise ValueError('unsupported SVG element')
        for key, value in element.attrib.items():
            if key not in attributes or any(token in value.lower() for token in ('url', 'href', 'javascript:', 'data:')):
                raise ValueError('unsupported SVG attribute or resource')


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
        if path.suffix not in {'.md', '.json', '.jsonl', '.py', '.cpp', '.hpp', '.c', '.h', '.cmake', '.yaml', '.png', '.svg', '.js', '.cjs', '.html'} and name not in {
                '.gitignore', '.dockerignore', 'LICENSE', 'Dockerfile', 'CMakeLists.txt', 'cmake/browser/CMakeLists.txt'}:
            raise ValueError('unsupported publication format: ' + name)
        raw = path.read_bytes()
        if path.suffix == '.png':
            asset = manifest.get('owned_assets', {}).get(name)
            if not isinstance(asset, dict) or asset.get('origin') != 'project-rendered-ui' or not asset.get('command'):
                raise ValueError('unregistered owned image')
            if asset.get('sha256') != hashlib.sha256(raw).hexdigest(): raise ValueError('owned image digest')
            from capture_png import validate_owned_png
            validate_owned_png(raw)
            if hashlib.sha256(raw).hexdigest() in restricted_hashes: raise ValueError('restricted source detected')
            result.append((name, raw))
            continue
        if path.suffix == '.svg':
            validate_owned_svg(raw, manifest.get('owned_assets', {}).get(name))
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
    print(f'Packaged {len(files)} reviewed source/owned-asset files. Licensed sources excluded; no release approval implied.')


if __name__ == '__main__':
    main()
