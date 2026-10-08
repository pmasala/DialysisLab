"""Integrity of the selected GUI cache; no downloads or fixed UI responses."""
import hashlib
import io
import json
from pathlib import Path
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import fetch_gui


class GuiDependencyTests(unittest.TestCase):
    def fixture(self, root, member='library/source.c', link=False):
        cache = root / 'cache'; cache.mkdir()
        archive = cache / 'library.tar.gz'
        with tarfile.open(archive, 'w:gz') as out:
            entry = tarfile.TarInfo(member)
            if link:
                entry.type = tarfile.SYMTYPE; entry.linkname = '/tmp/outside'; out.addfile(entry)
            else:
                data = b'/* own synthetic test input */\n'; entry.size = len(data); out.addfile(entry, io.BytesIO(data))
        lock = dict(components=[dict(name='test', version='1', url='https://invalid.example/no-download',
                                    archive=archive.name, directory='library', sha256=hashlib.sha256(archive.read_bytes()).hexdigest())])
        (root / 'gui_dependencies.json').write_text(json.dumps(lock))
        return cache

    def test_verified_archive_does_not_authorize_modified_extracted_sources(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); cache = self.fixture(root)
            with patch.object(fetch_gui, 'ROOT', root):
                fetch_gui.fetch(cache, offline=True); fetch_gui.fetch(cache, offline=True)
                (cache / 'library/source.c').write_text('tampered')
                with self.assertRaisesRegex(ValueError, 'modified extracted'): fetch_gui.fetch(cache, offline=True)
                (cache / 'library.tar.gz').write_bytes(b'tampered')
                with self.assertRaisesRegex(ValueError, 'archive digest'): fetch_gui.fetch(cache, offline=True)

    def test_unknown_links_and_traversal_are_not_extracted(self):
        for name, link in [('library/../../outside', False), ('library/symlink', True)]:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                root = Path(directory); cache = self.fixture(root, name, link)
                with patch.object(fetch_gui, 'ROOT', root), self.assertRaises(ValueError): fetch_gui.fetch(cache, offline=True)
                self.assertFalse((root / 'outside').exists())
