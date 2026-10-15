#!/usr/bin/env python3
"""Render current requirements/test inventory; check drift and local document links.

Historical execution results are deliberately excluded from the official catalogues.
This is a structural tool, not a scientific or regulatory approval tool.
"""
import argparse
import ast
import json
from pathlib import Path
import re
import sys
import document_contracts
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
GROUPS = [
    ('System boundaries and protective principles', ['REQ-']),
    ('Execution, failure handling and records', ['M1-REQ-']),
    ('Hydraulics, patient and prepared fluids', ['M2-REQ-', 'M3-REQ-', 'M4-REQ-', 'PHY-REQ-', 'DYN-REQ-', 'MIX-REQ-']),
    ('Treatment lifecycle and operator interface', ['M5-REQ-', 'M6-REQ-', 'UI-REQ-', 'SYN-REQ-']),
    ('Experiments and inspection', ['M7-REQ-']),
    ('Security, dependencies and integration', ['M8-REQ-', 'M9-REQ-']),
]


def link(path, prefix):
    return '[' + path + '](' + prefix + path + ')'


def render(root):
    data = json.loads((root / 'assurance/traceability.json').read_text())
    requirements = data['requirements']
    ids = [r['id'] for r in requirements]
    if len(ids) != len(set(ids)):
        raise ValueError('duplicate requirement ID')
    lines = ['# Software requirements specification', '',
        'Document ID SRS-01; revision controlled by Git. Status: review candidate; no independent approval recorded.', '',
        'Read next: [Architecture](ARCHITECTURE.md). Definitions: [Glossary](GLOSSARY.md).', '',
        '## Intended use and users', '',
        'DialysisLab is an open-source simulation and software-development reference for engineers,',
        'researchers and educators. It operates only simulated equipment and patients. It supports',
        'intermittent HD and HDF PRE/POST, including modeled online substitution preparation.',
        'It is not intended to prescribe or deliver treatment to people. EU is the first target',
        'for future lifecycle adaptation; this is not a medical-device classification decision.', '',
        'The device operator controls treatment; the experiment user configures patient, equipment,',
        'faults and time. Patient configuration remains outside the device UI. C++17 implements',
        'equipment/control/protection and graphical clients; Python 3.9+ implements the patient',
        'and experiment runtime. Linux and WSL2 are supported development targets. Application',
        'dependencies prefer MIT, BSD, Apache-2.0 or zlib; exceptions need explicit review.', '',
        '## Reading and acceptance rules', '',
        'Requirements are grouped by function. Existing IDs remain stable for traceability; an M',
        'prefix is not the reading order. Statements and acceptance text below are generated',
        'from the maintained register without silently rewriting obligations. The supplemental',
        '[atomic requirements](ATOMIC_REQUIREMENTS.md) and [coverage matrix](testing/COVERAGE.md)',
        'allocate implemented parent requirements to detailed obligations and executable test methods; deferred work is explicit. Some obligations',
        'remain too broad or need justified numerical criteria; the current audit identifies them.', '',
        '**Current verification decision:** implementation is recorded for these requirements,',
        'but requirement-level independent acceptance is not recorded. Historical test passes',
        'are intentionally not carried forward here. Use the current verification record to',
        'assess baseline applicability; consult the separate Project Log only for history.', '',
        'Simulation bounds and synthetic alarm thresholds are not clinical limits. Supported',
        'legacy scenarios are compatibility requirements, not the current interactive default.',
        'The default is the guided dynamic scenario documented in the design chapters.', '',
        '## Operational reference', '',
        'The guided sequence is tests → preparation → priming → connection → therapy → return',
        '→ disconnection → disinfection. Priming and return terminate on measured volume;',
        'therapy on delivered treatment time; disinfection needs both time and volume. Manual',
        'phases wait for confirmation. The detailed guards and progress criteria are in',
        '[Treatment design](design/TREATMENT.md) and [workflow protocol](testing/WORKFLOW.md).', '',
        'Safety-class assignment, quantitative risk acceptability, independent approval and',
        'validated model operating envelopes remain required decisions, not assumptions.', '']
    assigned = []
    for title, prefixes in GROUPS:
        lines += ['## ' + title, '']
        for r in requirements:
            if not any(r['id'].startswith(prefix) for prefix in prefixes):
                continue
            assigned.append(r['id'])
            lines += ['### ' + r['id'], '', r['statement'], '',
                '**Acceptance:** ' + r['acceptance'], '',
                '**Trace:** needs ' + ', '.join(r['needs']) + '; risks ' + ', '.join(r['hazards']) +
                '; design ' + ', '.join(r['designs']) + '; verification ' + ', '.join(r['tests']) + '.', '',
                '**Implementation locations:** ' + ', '.join(link(a['path'], '../') for a in r['implementation'] if not re.match(r'(docs/M[1-9]|assurance/evidence/)', a['path'])) + '.', '']
    if sorted(assigned) != sorted(ids):
        raise ValueError('requirements must have exactly one functional group')
    lines += ['## Change control', '',
        'Edit the register, review requirement changes, then run `python3 tools/documentation.py --write`.',
        'Historical result fields in the compatibility register are not evidence of current approval.',
        'See [Document control](DOCUMENT_CONTROL.md) and [current verification status](testing/STATUS.md).', '']
    requirements_text = '\n'.join(lines)
    lines = ['# Current verification catalogue', '',
        'Document ID STC-01; revision controlled by Git. Generated inventory, not a test report.', '',
        'Read [Master plan](PLAN.md) first. [Current status](STATUS.md) identifies baseline applicability.',
        'Historical outcomes and milestone reports belong to the separate Project Log and are not',
        'rendered here. A method name proves that a test exists, not that it ran or fully covers a requirement.', '',
        '## Registered verification obligations', '']
    for title, prefixes in GROUPS:
        relevant = {r['id'] for r in requirements if any(r['id'].startswith(p) for p in prefixes)}
        lines += ['### ' + title, '']
        for t in data['tests']:
            if not relevant.intersection(t['requirements']):
                continue
            lines += ['#### ' + t['id'], '', '**Requirements:** ' + ', '.join(t['requirements']) + '.', '',
                '**Procedure:** ' + t['procedure'], '', '**Expected:** ' + t['expected'], '',
                '**Current acceptance:** not independently approved; no historical result inherited.', '']
    lines += ['## Concrete Python test entry points', '',
        'Run from repository root after building the required profile. `PYTHONPATH=python:tools:tests`',
        'makes the listed module/class/method selectable with `python3 -m unittest -v`.',
        'Inspect each fixture for process, display and Docker prerequisites; report skipped cases.', '']
    for path in sorted((root / 'tests').glob('test_*.py')):
        tree = ast.parse(path.read_text())
        entries = []
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                for method in node.body:
                    if isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef)) and method.name.startswith('test_'):
                        entries.append(path.stem + '.' + node.name + '.' + method.name)
        if entries:
            lines += ['### ' + link(str(path.relative_to(root)), '../../'), '']
            lines += ['- `' + entry + '`' for entry in entries]
            lines.append('')
    result = {'docs/REQUIREMENTS.md': requirements_text, 'docs/testing/CATALOG.md': '\n'.join(lines)}
    result.update(document_contracts.render(root, ids))
    return result


def check(root):
    errors = []
    for name, expected in render(root).items():
        path = root / name
        if not path.exists() or path.read_text() != expected:
            errors.append('stale generated document: ' + name)
    register = json.loads((root / 'docs/document-set.json').read_text())
    for name in register['official_documents']:
        path = root / name
        if not path.is_file():
            errors.append('missing official document: ' + name)
            continue
        for target in re.findall(r'\]\(([^\s)]+)(?:\s+[^)]*)?\)', path.read_text()):
            if '://' in target or target.startswith(('#', 'mailto:')):
                continue
            target = unquote(target.split('#')[0])
            resolved = (path.parent / target).resolve()
            if not resolved.is_relative_to(root.resolve()) or not resolved.exists():
                errors.append(name + ': broken or outside-root local link: ' + target)
    preparation = root / register.get('current_preparation_evidence', 'assurance/evidence/preparation/report.json')
    if not preparation.resolve().is_relative_to(root.resolve()):
        errors.append('preparation evidence outside project root')
    elif 'current_preparation_evidence' in register and not preparation.is_file():
        errors.append('missing current preparation evidence')
    elif preparation.exists():
        from verify_preparation import applicable
        if not applicable(json.loads(preparation.read_text()), root):
            errors.append('preparation execution is not applicable to current verification inputs; rerun verify_preparation.py')
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--write', action='store_true')
    group.add_argument('--check', action='store_true')
    args = parser.parse_args()
    if args.write:
        for name, value in render(ROOT).items():
            (ROOT / name).write_text(value)
    errors = check(ROOT)
    print(json.dumps(dict(structural_errors=errors,
        scope='Document drift, local links and contract/test allocation structure; no scientific or regulatory approval.'), indent=2))
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main())
