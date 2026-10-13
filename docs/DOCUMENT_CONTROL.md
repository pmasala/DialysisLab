# Document control and change assessment

Document ID DOC-CTRL; revision 1; prepared 2026-10-12. Status: proposed for review.
Owner role: project maintainer. Independent approval: not recorded.

## Identify exactly what is being read

The Git commit identifies a document revision and its associated implementation.
Use `git rev-parse HEAD` and record the tree, scenario hash, compiler and image
identities with an execution. A branch name alone is mutable and is not a baseline.
The audit assesses this corrective candidate against main
`602e8dab8e65efdb0bc8db1051ce0006f0d3adfd` as the change base. Its current runtime,
document and test hashes are recorded in the audit reports. No earlier CI pass is
assigned to changed code. No signature or human approval is implied.

All future pull requests target **main**. Development branches are temporary work
areas. A merged branch is not an approved product release.

## Sources and precedence

| Information | Maintained source | Human-readable view |
| --- | --- | --- |
| Requirement IDs, statements, acceptance, risk/design/test links and recorded status | `assurance/traceability.json` | [Requirements](REQUIREMENTS.md) |
| Current component responsibilities and implementation decisions | Architecture and `docs/design/` | Same documents, backed by linked source |
| Current test obligations and execution applicability | Current plan, catalogue and baseline assessment | [Catalogue](testing/CATALOG.md), [Status](testing/STATUS.md) |
| Execution procedures and new acceptance proposals | `docs/testing/` | Master plan and topic protocols |
| Standards applicability and edition decisions | `assurance/standards/*.json` | Generated checklist and edition-gap record |
| Documentation findings, owners and closure evidence | [Audit](../assurance/audits/DOCUMENTATION_AUDIT.md) | Same record |

Historical result records are archived through [Project Log](../project-log/README.md),
outside the official set. The catalogue does not render them. Reuse requires an
explicit current-baseline assessment; otherwise the result is pending.

A conflict between a requirement and code is a defect to disposition, not a rule
that code automatically wins. Historical milestone text remains authoritative only
for its named version. The new current-design chapters identify which extensions
supersede older assumptions. New protocols are prospective; they cannot be used to
retroactively declare an older run successful.

Generate the requirements, catalogue, atomic allocations and wire dictionary with:

```bash
python3 tools/documentation.py --write
python3 tools/documentation.py --check
```

The checker detects stale generated catalogues and broken local file links in the
current reading set. It does not assess scientific truth, normative completeness,
external website availability or reviewer competence. The requirements retain
existing broad statements verbatim so that editorial changes cannot silently
change obligations. The detailed allocation covers every parent ID; semantic completeness and risk
approval remain review decisions.

## Review and publication sequence

1. Identify the affected requirement, risk control, interface, model assumption
   and test. Review changes against the declared simulator scope.
2. Update the design and protocol before execution where new acceptance is needed.
   Record changed tolerances explicitly; do not relax a tolerance to hide failure.
3. Implement and execute the affected tests. Preserve failures and partial output.
4. Review the candidate once; correct findings and repeat affected verification.
5. After the last edit, regenerate documents, refresh **implementation** hashes,
   check traceability, standards, publication and the final staged diff. Never
   replace a historical evidence hash with a current source hash.
6. Open the PR against main. Record local limitations and the exact hosted results.
   The maintainer authorizes merge; the safety/regulatory owner separately authorizes
   any reference-release or downstream product claim.

The maintainer allocates named requirement, design, verification and safety owners.
Role labels in these documents are proposed responsibilities, not evidence that
those people have been appointed. Independent review remains open until a named,
competent reviewer records date, scope, findings and acceptance.

## Rights and language

Project-authored prose, equations describing this code, and test procedures may be
published under the repository licence. Do not copy licensed standards, their
checklists or manufacturer artwork. Link public sources, record edition and access
limitations, and retain licensed review material privately. Public metadata is not
a substitute for the full normative text. English is the maintained repository
language; a translation must identify its corresponding commit.

## Supplemental contracts and allocations

`assurance/current-obligations.json` controls selected atomic clarifications and
concrete test allocations; it does not replace the 60 parent requirements.
`docs/wire-contract.json` controls fixed-field wire order, units and bounds.
Run `python3 tools/documentation.py --write` after editing either. The check rejects
unknown parents, missing executable methods, duplicate fields, invalid bounds and
stale generated documents. Wire source hashes must be refreshed only after reviewing
the affected producer/consumer contract. They detect change; they do not prove
semantic equivalence. Patient JSON and composite protocol prose remain reviewed
manual specifications, so impact review must include them explicitly.

The coverage matrix records existing tests and partial coverage. A passing witness
for a known parser discrepancy confirms the finding; it does not close it. An
independent acceptance decision needs an identified result and reviewer record under
[closure protocol](testing/CLOSURE.md), never just a changed status flag.
