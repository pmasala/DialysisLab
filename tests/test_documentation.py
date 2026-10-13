"""Current document identity and separation from historical execution evidence."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import documentation


class DocumentationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for name in ('assurance', 'docs/testing', 'tests'):
            (self.root / name).mkdir(parents=True, exist_ok=True)
        self.data = dict(requirements=[dict(id='REQ-001', statement='Keep authority separate.',
            acceptance='Denied calls change no patient state.', needs=['N1'], hazards=['H1'],
            designs=['D1'], tests=['T1'], implementation=[])], tests=[dict(id='T1',
            requirements=['REQ-001'], procedure='Attempt unauthorized access.', expected='Denied.',
            result='passed', evidence=dict(run_id='historical-result-must-not-be-current'))])
        self.save()
        (self.root / 'docs/document-set.json').write_text(json.dumps(dict(official_documents=['docs/manual.md'])))
        (self.root / 'docs/manual.md').write_text('[Valid target](target.md)\n')
        (self.root / 'docs/target.md').write_text('Target\n')
        self.generate()

    def save(self):
        (self.root / 'assurance/traceability.json').write_text(json.dumps(self.data))

    def generate(self):
        for name, value in documentation.render(self.root).items():
            (self.root / name).write_text(value)

    def test_historical_pass_does_not_become_current_acceptance(self):
        text = documentation.render(self.root)['docs/testing/CATALOG.md']
        self.assertNotIn('historical-result-must-not-be-current', text)
        self.assertNotIn('**Result:** passed', text)
        self.assertIn('not independently approved', text)
        self.assertIn('T1', text)

    def test_last_requirement_edit_invalidates_generated_candidate(self):
        self.assertEqual(documentation.check(self.root), [])
        self.data['requirements'][0]['acceptance'] = 'A changed acceptance obligation.'
        self.save()
        self.assertTrue(any('stale generated document' in e for e in documentation.check(self.root)))
        self.generate()
        self.assertEqual(documentation.check(self.root), [])

    def test_missing_and_outside_root_links_are_rejected(self):
        (self.root / 'docs/target.md').unlink()
        self.assertTrue(any('broken' in e for e in documentation.check(self.root)))
        (self.root / 'docs/manual.md').write_text('[Escape](../../outside.md)\n')
        self.assertTrue(any('outside-root' in e for e in documentation.check(self.root)))

    def test_unallocated_or_duplicate_requirements_cannot_disappear(self):
        self.data['requirements'][0]['id'] = 'UNKNOWN-001'
        self.save()
        with self.assertRaisesRegex(ValueError, 'exactly one'):
            documentation.render(self.root)
        self.data['requirements'][0]['id'] = 'REQ-001'
        self.data['requirements'].append(dict(self.data['requirements'][0]))
        self.save()
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            documentation.render(self.root)


if __name__ == '__main__':
    unittest.main()
