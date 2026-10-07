#!/usr/bin/env python3
"""Render the original project checklist; never reads licensed source files."""
import json
from pathlib import Path


def render(data, sources, gaps):
    standards = {s['id']: s for s in sources['standards']}
    lines = ['# Explained project checklist', '',
             'Generated from `checklist.json`. Edit the JSON and rerun `python3 tools/render_checklist.py`.', '',
             '**Draft for substantive review. All entries are open; no compliance or test pass is claimed.**', '',
             'Read [coverage and use instructions](README.md) and [edition gaps](EDITION_GAPS.md) first. '
             'Owner roles are not assigned people. Source references are edition-specific; grouped references require detailed review.', '']
    previous = None
    for r in data['items']:
        if r['standard_id'] != previous:
            previous = r['standard_id']
            s = standards[previous]
            lines.extend(['## ' + s['reference'], '', s['review_note'], ''])
            if s['edition_gap_ids']:
                lines.extend(['Open edition/coverage gaps: ' + ', '.join(s['edition_gap_ids']) + '.', ''])
        lines.extend(['### ' + r['id'] + ' — ' + r['topic'], '',
                      '**References:** ' + '; '.join(r['clauses']) + '. **Basis:** ' + r['basis'] + '.', '',
                      r['project_action'], '', '**Evidence needed:** ' + '; '.join(r['evidence_required']) + '.', '',
                      '**Scope:** ' + r['scope'] + '. ' + r['applicability_rationale'], '',
                      '**Owner role:** ' + r['owner_role'] + '. **Applicability:** ' + r['applicability_status']
                      + '. **Completion:** ' + r['completion_status'] + '. **Reviewer/date:** unassigned.', ''])
        if r['requirement_ids']:
            lines.extend(['Starter trace links: ' + ', '.join(r['requirement_ids'] + r['test_ids'])
                          + ' (draft/planned; not complete coverage).', ''])
    lines.extend(['## Open gaps', ''])
    for gap in gaps['gaps']:
        lines.append('- ' + gap['id'] + ': ' + gap['title'] + ' — ' + gap['status'] + '.')
    return '\n'.join(lines) + '\n'


if __name__ == '__main__':
    folder = Path(__file__).resolve().parents[1] / 'assurance/standards'
    args = [json.loads((folder / name).read_text()) for name in ('checklist.json', 'sources.json', 'gaps.json')]
    (folder / 'CHECKLIST.md').write_text(render(*args))
    print(f'Rendered {len(args[0]["items"])} checklist entries.')
