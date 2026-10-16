"""M1 source formats must not weaken restricted-source exclusion."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from package_release import collect
from check_publication import inspect_context


class PublicationChecks(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        (self.root / 'assurance/standards').mkdir(parents=True)
        (self.root / 'assurance/standards/sources.json').write_text('{"standards": []}')

    def test_source_and_build_formats(self):
        names = ['test.cpp', 'test.hpp', 'app.js', 'worker.cjs', 'index.html', 'font.c', 'lv_conf.h', 'Gui.cmake', 'trajectory.jsonl', 'compose.yaml', 'CMakeLists.txt', 'Dockerfile', '.dockerignore']
        for name in names:
            (self.root / name).write_text('synthetic project-owned text\n')
        self.assertEqual(len(collect(self.root, {'files': names})), len(names))

    def test_reject_binary_source_and_restricted_format(self):
        for name, content in [('source.cpp', b'%PDF-synthetic'), ('source.hpp', b'PK\x03\x04fake'),
                              ('source.py', b'null\x00byte'), ('standard.pdf', b'plain text')]:
            with self.subTest(name=name):
                (self.root / name).write_bytes(content)
                with self.assertRaises(ValueError):
                    collect(self.root, {'files': [name]})

    def test_paths_symlinks_and_duplicates(self):
        (self.root / 'ok.cpp').write_text('int main() {}')
        (self.root / 'alias.cpp').symlink_to(self.root / 'ok.cpp')
        for paths in [['../escape.cpp'], ['/absolute.cpp'], ['ok.cpp', 'ok.cpp'], ['alias.cpp']]:
            with self.subTest(paths=paths), self.assertRaises(ValueError):
                collect(self.root, {'files': paths})

    def test_actual_context_is_explicit_reviewed_subset(self):
        manifest = json.loads((ROOT / 'publication_manifest.json').read_text())
        paths = inspect_context(ROOT, manifest)
        self.assertIn('src/plant.cpp', paths)
        self.assertNotIn('assurance/standards/sources.json', paths)
        self.assertFalse(any(p.startswith('.git/') for p in paths))

    def test_context_rejects_broad_inclusion(self):
        (self.root / '.dockerignore').write_text('**\n!src/**\n')
        with self.assertRaises(ValueError):
            inspect_context(self.root, {'files': []})


class OwnedCaptureChecks(unittest.TestCase):
    def test_only_registered_encoder_profile_with_matching_digest_is_allowed(self):
        from capture_png import encode
        import hashlib
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'assurance/standards').mkdir(parents=True)
            (root / 'assurance/standards/sources.json').write_text('{"standards": []}')
            image = root / 'capture.png'
            image.write_bytes(encode(2, 2, b'\0' * 12))
            manifest = {'files': ['capture.png']}
            with self.assertRaises(ValueError): collect(root, manifest)
            manifest['owned_assets'] = {'capture.png': {'origin': 'project-rendered-ui', 'command': 'real framebuffer capture', 'sha256': hashlib.sha256(image.read_bytes()).hexdigest()}}
            self.assertEqual(len(collect(root, manifest)), 1)
            image.write_bytes(image.read_bytes() + b'%PDF-private')
            manifest['owned_assets']['capture.png']['sha256'] = hashlib.sha256(image.read_bytes()).hexdigest()
            with self.assertRaises(ValueError): collect(root, manifest)


class OwnedDiagramChecks(unittest.TestCase):
    def setUp(self):
        import hashlib
        self.hash = lambda raw: hashlib.sha256(raw).hexdigest()

    def check(self, raw, **overrides):
        from package_release import validate_owned_svg
        asset = dict(origin='project-authored-diagram', command='python3 tools/render_hydraulic_diagrams.py', sha256=self.hash(raw))
        asset.update(overrides)
        validate_owned_svg(raw, asset)

    def test_passive_diagram_and_ownership(self):
        raw = b'<svg xmlns="http://www.w3.org/2000/svg"><path d="M0,0 H20"/><text x="0" y="10">Pump</text></svg>'
        self.check(raw)
        for override in ({'origin': 'unknown'}, {'sha256': '0' * 64}, {'command': ''}):
            with self.subTest(override=override), self.assertRaises(ValueError):
                self.check(raw, **override)

    def test_reject_active_external_or_unexpected_content(self):
        for content in ['<script>alert(1)</script>', '<image href="https://example.org/a.png"/>',
                        '<path onload="alert(1)"/>', '<path fill="url(https://example.org/a)"/>',
                        '<foreignObject/>', '<style>text{fill:red}</style>']:
            with self.subTest(content=content), self.assertRaises(ValueError):
                self.check(('<svg xmlns="http://www.w3.org/2000/svg">'+content+'</svg>').encode())
        for raw in [b'<!DOCTYPE svg><svg/>', b'<?xml-stylesheet href="external"?><svg/>', b'<svg>', b'<svg/>']:
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                self.check(raw)

    def test_registered_svg_is_packaged_and_restricted_hash_still_rejected(self):
        import hashlib
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'assurance/standards').mkdir(parents=True)
            sources = root / 'assurance/standards/sources.json'
            sources.write_text('{"standards": []}')
            raw = b'<svg xmlns="http://www.w3.org/2000/svg"><title>Original</title></svg>'
            (root / 'diagram.svg').write_bytes(raw)
            manifest = {'files': ['diagram.svg'], 'owned_assets': {'diagram.svg': dict(
                origin='project-authored-diagram', command='generate', sha256=hashlib.sha256(raw).hexdigest())}}
            self.assertEqual(collect(root, manifest), [('diagram.svg', raw)])
            sources.write_text(json.dumps({'standards': [{'supplied_sources': [{'sha256': hashlib.sha256(raw).hexdigest()}]}]}))
            with self.assertRaises(ValueError):
                collect(root, manifest)
