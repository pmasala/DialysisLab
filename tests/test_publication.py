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
        names = ['test.cpp', 'test.hpp', 'font.c', 'lv_conf.h', 'Gui.cmake', 'trajectory.jsonl', 'compose.yaml', 'CMakeLists.txt', 'Dockerfile', '.dockerignore']
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
