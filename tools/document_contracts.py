"""Render supplemental obligations/contracts and reject dangling source allocations.

These checks establish identity and structural consistency, never acceptance or
exhaustive protocol coverage. Runtime witness tests cover selected serializers.
"""
import ast
import hashlib
import json
import math
from pathlib import Path


def test_inventory(root):
    entries = set()
    for path in (root / 'tests').glob('test_*.py'):
        for node in ast.parse(path.read_text()).body:
            if isinstance(node, ast.ClassDef):
                for method in node.body:
                    if isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef)) and method.name.startswith('test_'):
                        entries.add(path.stem + '.' + node.name + '.' + method.name)
    return entries


def cell(value):
    return str(value).replace('|', '\\|').replace('\n', ' ')


def render(root, parents):
    register = json.loads((root / 'docs/document-set.json').read_text())
    sources = register.get('contract_sources', [])
    if not sources:
        if 'docs/ATOMIC_REQUIREMENTS.md' in register.get('official_documents', []):
            raise ValueError('official contract documents require contract_sources')
        return {}
    expected = ['assurance/current-obligations.json', 'docs/wire-contract.json']
    if sources != expected:
        raise ValueError('contract_sources must identify both controlled contract inputs')
    obligations = json.loads((root / sources[0]).read_text())['obligations']
    inventory = test_inventory(root)
    seen = set()
    lines = ['# Atomic acceptance obligations', '',
        'Document ID SRS-02; proposed technical baseline, independent approval pending.', '',
        'Read [parent requirements](REQUIREMENTS.md) first. These obligations clarify registered parent requirements and their',
        'testable decisions without replacing or reducing any parent obligation. They are',
        'generated from [the controlled register](../assurance/current-obligations.json).',
        'Limits characterize the simulator implementation; they are not clinical thresholds.',
        'A test allocation is a coverage argument to review, not a recorded execution result.', '',
        'The [coverage matrix](testing/COVERAGE.md) makes incomplete cases visible.', '']
    matrix = ['# Current obligation–design–test allocation', '',
        'Document ID STM-01; generated from the atomic acceptance register.', '',
        'All rows are proposed and await independent acceptance. Method existence is checked',
        'against the actual Python test AST. The checker cannot decide semantic completeness.',
        'Read [current execution applicability](STATUS.md) separately. Additional cases and',
        'approval rules are in [closure protocols](CLOSURE.md).', '',
        '| Obligation / parent | Design | Existing executable entry point | Coverage limitation |',
        '| --- | --- | --- | --- |']
    for item in obligations:
        ident = item['id']
        if ident in seen:
            raise ValueError('duplicate atomic obligation: ' + ident)
        seen.add(ident)
        if item['parent'] not in parents:
            raise ValueError('unknown parent requirement: ' + item['parent'])
        if item['test'] not in inventory:
            raise ValueError('missing executable test: ' + item['test'])
        path = root / item['design']
        if not path.is_file() or not path.resolve().is_relative_to(root.resolve()):
            raise ValueError('missing/outside-root design: ' + item['design'])
        if item['approval'] != 'proposed; independent approval pending':
            raise ValueError('independent acceptance needs a reviewed result record, not a register flag')
        lines += ['## ' + ident + ' — ' + item['parent'], '', item['statement'], '',
                  '**Acceptance:** ' + item['acceptance'], '',
                  '**Coverage:** ' + item['coverage'], '',
                  '**Design:** [' + item['design'] + '](../' + item['design'] + ').', '',
                  '**Existing test:** `' + item['test'] + '`.', '']
        matrix.append('| ' + ' | '.join([ident + ' / ' + item['parent'],
            '[' + item['design'] + '](../../' + item['design'] + ')',
            '`' + item['test'] + '`', cell(item['coverage'])]) + ' |')
    allocated = {item['parent'] for item in obligations}
    matrix += ['', '## Parent obligations outside this supplemental decomposition', '',
        'These parents remain in the SRS and existing catalogue; they are not considered',
        'atomically covered merely because another requirement has a test allocation.', '',
        (', '.join(sorted(set(parents) - allocated)) + '.') if set(parents) - allocated else
        'None. All parents have at least one allocation. This structural completeness does not establish semantic completeness or full execution coverage.', '']
    spec = json.loads((root / sources[1]).read_text())
    if set(spec.get('source_sha256', {})) != set(spec['sources']):
        raise ValueError('wire source review hashes must cover all sources')
    for source in spec['sources']:
        if not (root / source).is_file():
            raise ValueError('missing wire implementation source: ' + source)
        if hashlib.sha256((root / source).read_bytes()).hexdigest() != spec['source_sha256'][source]:
            raise ValueError('wire implementation changed; review contract and refresh source hash: ' + source)
    fields = ['# Fixed-field DL1 dictionary', '',
        'Document ID ICD-02; generated from [wire-contract.json](../wire-contract.json).', '',
        'Read the [wire protocol](WIRE_PROTOCOL.md) for framing, authorization, ordering,',
        'composite payloads, patient JSON and experiment operations. Positions below start',
        'at 1 **after the tag**; neither DL1 nor the tag is counted. Bounds are inclusive',
        'parser limits, not clinical limits. A dash means a token or additional semantic rule.',
        'Real values must be finite. C++ is the bound reference unless a note says otherwise.',
        'This inventory does not claim every legacy protocol version is fully specified.', '']
    messages = set()
    for msg in spec['messages']:
        if msg['id'] in messages:
            raise ValueError('duplicate message ID: ' + msg['id'])
        messages.add(msg['id'])
        names = set()
        fields += ['## ' + msg['id'] + ' — ' + msg['tag'], '',
            '**Endpoint:** `' + msg['endpoint'] + '`; ' + msg['direction'] + '; ' + str(len(msg['fields'])) + ' fields.', '',
            '**Conditions:** ' + msg['condition'], '', '**Response / interpretation:** ' + msg['reply'], '',
            '| Position | Field | Type | Unit | Inclusive bounds |', '| --- | --- | --- | --- | --- |']
        for position, f in enumerate(msg['fields'], 1):
            if f['name'] in names or f['type'] not in ('real', 'integer', 'atom') or not f['unit']:
                raise ValueError('invalid/duplicate wire field: ' + msg['id'] + '/' + f['name'])
            names.add(f['name'])
            bounds = f['bounds']
            if bounds is not None and (len(bounds) != 2 or
                    any(type(x) not in (int, float) or not math.isfinite(x) for x in bounds) or bounds[0] > bounds[1]):
                raise ValueError('invalid wire bounds: ' + msg['id'] + '/' + f['name'])
            fields.append('| ' + ' | '.join(map(cell, [position, '`' + f['name'] + '`', f['type'], f['unit'],
                          '—' if bounds is None else str(bounds[0]) + ' … ' + str(bounds[1])])) + ' |')
        fields.append('')
    return {'docs/ATOMIC_REQUIREMENTS.md': '\n'.join(lines),
            'docs/testing/COVERAGE.md': '\n'.join(matrix),
            'docs/design/WIRE_FIELDS.md': '\n'.join(fields)}
