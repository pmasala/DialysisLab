# Current documentation audit and corrective-action record

Document ID AUD-DOC-01; revision 3; audit date 2026-10-12. Implementation assessed: the corrective candidate identified by source hashes in
[checks.json](checks.json), [convergence.json](convergence.json) and the native
resource report. It changes runtime code relative to main
`602e8dab8e65efdb0bc8db1051ce0006f0d3adfd`; earlier CI is not reused as a pass for
these changes. Git identifies the complete published candidate.

**Conclusion: the baseline is not ready for an independent conformity audit to close
without substantial findings.** This change supplies an auditable reading structure,
current design explanations and prospective test protocols. It does not supply the
missing safety decisions, measurements, human validation or independent approval.

This is an engineering gap assessment with source inspection and reproducible
structural checks. It is not a notified-body assessment. The author also prepared
the corrections; independence and formal auditor competence are not claimed.
Severity below is a project triage scheme, not an official notified-body grading.

## Scope, method and criteria

The review inventories all 60 requirements, 60 design records and 65 registered test
obligations; checks link/evidence structure; and samples source behavior for guided
phase guards, priming/return endpoints, protection arbitration, RPC failure handling,
preparation, distributed transport and UI visibility. It inspects current component
ownership and deployment boundaries. It does not execute a full product acceptance
campaign or a clause-by-clause review of licensed standards.

Criteria are: readable current-baseline narrative; testable obligations; explicit
units/assumptions; consistent component/interface/state definitions; trace from
requirement through design to procedure and applicable result; identified changes,
review authority and honest disposition of missing evidence. EU MDR Annex II is used
as a documentation-organization reference for future device adaptation, not as a
claim that the simulator already has a device conformity route.

Public-source checks on 2026-10-12:

- [EU MDR Annex II](https://eur-lex.europa.eu/eli/reg/2017/745/oj/eng): technical documentation needs a clear organization and evidence supporting applicable requirements. Legal applicability and the current consolidated baseline require responsible review.
- [IEC 62304 catalogue](https://webstore.iec.ch/en/publication/22794): identifies the software lifecycle reference; catalogue access is not full-text assessment.
- [ISO 14971 catalogue](https://www.iso.org/standard/72704.html): risk-management process reference; it does not provide project risk acceptance.
- [IEC 60601-2-16:2025](https://webstore.iec.ch/en/publication/68379): current international dialysis equipment edition; EU adoption/recognition is a separate decision.
- [Commission MDCG index](https://health.ec.europa.eu/medical-devices-sector/new-regulations/guidance-mdcg-endorsed-documents-and-other-guidance_en): lists MDCG 2019-16 rev.1 cybersecurity guidance. No licensed text is reproduced.

The existing standards register retains its open edition/applicability decisions.
Current completeness checks report 184 open checklist entries and 12 open gaps.
Trace structure has zero errors but 204 release-gap messages. These are distinct
counts from different checkers, not 400 independent nonconformities.

## Findings and dispositions

| ID / priority | Objective evidence and consequence | Action, owner role and closure criterion | Current disposition |
| --- | --- | --- | --- |
| DOC-01 / major | Requirements were mainly embedded in JSON and historical M documents. A reviewer had no single functional reading order. | Documentation owner: standalone SRS containing every stable ID and acceptance, grouped by function; deterministic generation check. | Corrected in this candidate; independent acceptance pending |
| DOC-02 / major | Old and current contracts appeared together without a current-baseline boundary; earlier outcomes could be mistaken for current verification. | Maintainer: separate Project Log; explicit official document register and current applicability decision, no inherited historical pass in catalogues. | Corrected in this candidate; historical bytes preserved |
| DOC-03 / major | Architecture overview omitted a systematic component/interface/data/deployment allocation and current detailed phase guards. | Architecture owner: SAD plus four detailed designs, source-linked state endpoints, numerical conventions and failure seams. | Current architecture and five detailed designs supplied, including protective behavior, failure sequences and common causes. Independent review pending |
| DOC-04 / major | REQ-003 uses “independently justified tolerances”; DYN-REQ-001 combines many behaviors; design records often contain only a sentence. Complete atomic coverage and justified operating limits are not approved. | Requirements/safety owners: decompose compound obligations, allocate measurable limits, map each to design and test without deleting parent obligations. | 99 detailed acceptance obligations now allocate all 60 parents to design and actual executable methods. Remaining coverage limitations are explicit. Scientific accuracy budgets and independent semantic approval remain open |
| DOC-05 / major | No requirement has a recorded independent reviewer. Formal safety classification, essential performance and quantitative risk acceptance are open in SAFETY_SECURITY and prerequisites. | Safety/quality owners: appoint competent reviewers, justify class/applicability, complete risk-control and residual-risk decisions. | Open; blocks approval claims |
| DOC-06 / major | Historical 50 passed / 9 blocked / 6 planned test records do not by themselves establish current requirement acceptance; current full software run is broader but not a reviewed coverage argument. | Verification owner: approve current case-to-obligation coverage and identified execution/reuse decisions; close each missing case. | Current allocation matrix covers all parent IDs and checks method existence. Actual case results are recorded separately in checks.json; unexecuted IPC/Compose cases and partial acceptance scopes remain explicit |
| DOC-07 / major | New guided/physical/distributed behavior lacks a complete approved boundary matrix, combined-fault rationale and global convergence/uncertainty envelope. Long legacy runs do not establish every maximum-size dynamic case. | Model/verification owners: execute prospective WF/MOD/FAIL gaps, predeclare error/resource criteria, review independence of oracles. | Executed state/action, endpoint, all-mask, actual coupled single/pair-mask and freshness campaigns; measured three-mode step refinement and a 100000-tick native run. Global accuracy remains unresolved, including nonmonotonic instantaneous feed/drain refinement. Separate current-model Compose job added; execution pending |
| DOC-08 / major | Public urea fit covers only selected clearance points; chamber/controller/rheology/electrolyte/refill parameters lack independent measurements. | Model owner: measurement protocol, identified data and rights, uncertainty/identifiability, independent validation envelope. | STP-CAL now specifies per-model measurements, provenance, uncertainty, holdout and predeclared acceptance worksheet. Actual measurements and approved accuracy budgets remain open |
| DOC-09 / major | Test and capture evidence is software-oriented; representative-user critical tasks, alarm performance and downstream physical/clinical evidence remain absent. | Usability/product owners: approved validation protocols and actual reviewed evidence for declared use. | Open; a simulator screen cannot close device obligations |
| DOC-10 / major | Shared host/protocol/plant are common causes; threat/dependency registers retain open dispositions. Separation is not independence. | Security/safety owners: current inventories, adversarial coverage and accepted residual/common-cause risks. | Current protective/security design records controls, event sequences, detector limits and seven trust/common-cause boundaries. Fresh native dependency inventory generated; local static/image scan blocked by absent tools. Formal risk and dependency acceptance remain external |
| DOC-11 / minor | Experiment preset discovery selects only machine_*.json; default guided UI is not discoverable through that list. | UI/experiment owner: expose/validate intended guided presets and test real selection/launch without bypassing scheduled-mode authority. | Corrected: scheduled physical HD/PRE/POST are discoverable and physical_hd is the default. Catalogue/load/configuration test passed; actual broker-to-service launch regression added for hosted execution |
| DOC-12 / major | Extended payloads are specified across parsers and prose; complete field-by-field current schema with units, constraints and version compatibility is not controlled in one specification. | Interface owner: generate/review a shared schema and compatibility tests against actual parsers. | 32 fixed forms / 394 fields controlled. Actual C++/Python numeric boundary and malformed-length witnesses now cover six current output families; actual plant rejects malformed fields in five configuration families. Remaining legacy/semantic combinations and independent review are not claimed complete |
| DOC-13 / major | C++ rejects dynamic arterial_level=1.5 while Python accepts it; other extended decoder bounds also differ. Outer DYNAMICS10 permits initial dialysate volume up to 2000 mL while patient INIT accepts only 1000. | Interface/model owners: reconcile accepted domains at configuration and observation boundaries; add negative/end-to-end tests and rerun affected suites before closing. | Corrected: shared observation/metadata domains reconciled, sequence ceiling enforced, and initial dynamic dialysate inventory restricted to 50..1000 mL in outer validator and plant. Actual parser and plant/patient initialization regressions passed |

Owner roles above are proposed assignments. The maintainer must allocate named
responsible people and due dates; this assessment cannot invent those commitments.

## End-to-end audit trails sampled

| Requirement | Design / source | Verification examined | Assessment |
| --- | --- | --- | --- |
| UI-REQ-002 | SDD-01; `Machine::guided_transition`, `advance_guided`; `guided_ui::progress` | Guided state/LVGL fixture and cycle test methods | Priming, connection, return, disconnection and progress are implemented; exhaustive guards and human comprehension remain separate obligations |
| M1-REQ-007 | SDD-03; runner STEP failure/HALT path | Lost STEP reply cases in machine tests | Failure after plant acceptance must block commit; evidence must preserve unknown stop states |
| REQ-003 / DYN-REQ-001 | SDD-02; distributed transport and patient transaction | Independent model verifier and physical/dynamic suites | Ledger coverage exists; it cannot establish accuracy of synthetic constitutive laws |
| M8-REQ-006 | Document control; CI and trace checker | Final hash checks and CI classification tests | Final candidate must be checked after every last edit; old verification before an edit is insufficient |

This is a sample-based technical audit. Uninspected paths are not implicitly accepted.
The full registered obligations remain visible in the official requirements and test
catalogues, with approval status separate from implementation.

## Corrective sequence and final gate

1. Complete this document reorganization and run generation/link/publication/trace
   checks against the final candidate. Preserve the report and exact file hashes.
2. Review the supplemental atomic requirements, wire/JSON specifications and allocations, then close the coverage gaps
   with predeclared tests. Assign named owners and justified acceptance criteria.
3. Collect model measurements and human-use evidence; approve risk and dependency
   dispositions and exact normative baseline with authorized full-text access.
4. Independently review the resulting evidence before any reference-release or
   downstream device conformity claim. No automatic “audit passed” badge is supplied.

All current official documents are listed in [document-set.json](../../docs/document-set.json).
Historical narrative belongs to [Project Log](../../project-log/README.md), which is
not part of that set. The current [verification status](../../docs/testing/STATUS.md)
contains explicit applicability, not a chronology of previous builds.

## Technical corrections and remaining closure work

The [atomic specification](../../docs/ATOMIC_REQUIREMENTS.md) and
[coverage matrix](../../docs/testing/COVERAGE.md) contain 99 detailed obligations
across all 60 stable parent IDs. An allocation is not automatically full semantic
coverage or a passed result. The matrix states each limitation and checks cited
methods against actual test source. Historical test records remain unchanged.

Runtime changes reconcile numeric decoders and initial dialysate-volume limits,
and expose complete scheduled guided presets in the experiment console. The
[protocol specification](../../docs/design/WIRE_PROTOCOL.md), field dictionary and
patient JSON document the resulting common domains. No clinical range is inferred
from a parser limit. The native core and GUI compile successfully.

Executed campaigns include 832 state/action/guard combinations, 45 endpoint cases,
seven self-test failures, 64 reset cases and all 8192 masks across 16 states. The
actual coupled plant/patient also receives 455 single/pair-mask challenges in five
active phases and ten role-specific freshness faults. Injecting a mask proves
arbitration, not that every physical hazard is observable by a real sensor.

Nine numerical runs compare HD/PRE/POST at 400/200/100 ms with aligned samples and
blood/substitution steps. Pressure, level and concentration differences generally
decrease; instantaneous feed/drain differences do not. This observed limitation
keeps global numerical-accuracy acceptance open. A 100000-tick actual-model native
run passes conservation and bounded-memory checks; Compose isolation, cgroup peak
memory and real service transport require the separate hosted campaign.

The [protective/security design](../../docs/design/SAFETY_SECURITY.md) supplies the
current engineering failure and trust-boundary analysis. [STP-CAL](../../docs/testing/MEASUREMENTS.md)
specifies measurement conditions, provenance, uncertainty, holdout and proposed
acceptance for ten model areas. [STP-CLOSE](../../docs/testing/CLOSURE.md) identifies
which procedures have executed and which still need environment or external input.

Remaining work has four distinct causes: unavailable local IPC/container/static
analysis capabilities; unresolved scientific accuracy and measurement evidence;
representative-user validation; and responsible/independent decisions. None is
closed by changing a status flag. The [current status](../../docs/testing/STATUS.md)
and exact check report identify the technical evidence actually delivered.
