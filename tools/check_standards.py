#!/usr/bin/env python3
"""Validate the draft register, not normative interpretation or conformity."""
import argparse
import json
from pathlib import Path
import sys
from render_checklist import render


def inspect(data, sources, gaps, trace):
    errors = []
    standard_ids = {s['id'] for s in sources['standards']}
    gap_ids = {g['id'] for g in gaps['gaps']}
    requirement_ids = {r['id'] for r in trace['requirements']}
    tests = {t['id']: set(t['requirements']) for t in trace['tests']}
    seen = set()
    for source in sources['standards']:
        if not set(source['edition_gap_ids']) <= gap_ids:
            errors.append(source['id'] + ': unknown gap reference')
        for item in source['supplied_sources']:
            if item['redistribute'] is not False:
                errors.append(source['id'] + ': restricted source must not be redistributable')
    if not data['items']:
        errors.append('empty checklist')
    for r in data['items']:
        rid = r['id']
        if rid in seen:
            errors.append(rid + ': duplicate ID')
        seen.add(rid)
        if r['standard_id'] not in standard_ids:
            errors.append(rid + ': unknown standard')
        for key in ('topic', 'project_action', 'evidence_required', 'clauses', 'owner_role', 'applicability_rationale'):
            if not r.get(key):
                errors.append(rid + ': empty ' + key)
        if r['scope'] not in {'reference', 'conditional', 'downstream'}:
            errors.append(rid + ': invalid scope')
        if not set(r['requirement_ids']) <= requirement_ids:
            errors.append(rid + ': unknown requirement')
        for tid in r['test_ids']:
            if tid not in tests:
                errors.append(rid + ': unknown test')
            elif not tests[tid].intersection(r['requirement_ids']):
                errors.append(rid + ': test does not cover a linked requirement')
        # Schema 1 is intentionally a draft-only schema. Future closure support
        # must add reviewed, configuration-bound evidence validation first.
        if r['completion_status'] != 'open' or r['applicability_status'] != 'proposed':
            errors.append(rid + ': schema 1 does not support closure/applicability approval')
        if r['reviewer'] is not None or r['review_date'] is not None or r['evidence']:
            errors.append(rid + ': review/evidence requires a supported reviewed-record schema')
    for gap in gaps['gaps']:
        if gap['status'] != 'open':
            errors.append(gap['id'] + ': gap closure requires reviewed-record schema')
    return dict(structural_errors=errors, open_checklist_entries=len(data['items']),
                open_gaps=len(gaps['gaps']),
                scope='Draft data integrity only. Not clause completeness, evidence adequacy or conformity.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--release', action='store_true')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    folder = root / 'assurance/standards'
    try:
        data, sources, gaps = [json.loads((folder / name).read_text()) for name in
                              ('checklist.json', 'sources.json', 'gaps.json')]
        trace = json.loads((root / 'assurance/traceability.json').read_text())
        report = inspect(data, sources, gaps, trace)
        if (folder / 'CHECKLIST.md').read_text() != render(data, sources, gaps):
            report['structural_errors'].append('CHECKLIST.md is stale; rerun render_checklist.py')
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({'input_error': str(exc)}))
        return 2
    print(json.dumps(report, indent=2))
    return int(bool(report['structural_errors'] or
                    (args.release and (report['open_checklist_entries'] or report['open_gaps']))))


if __name__ == '__main__':
    sys.exit(main())
