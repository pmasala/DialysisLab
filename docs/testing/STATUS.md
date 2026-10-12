# Current baseline: verification and acceptance

Document ID SVR-01; revision 1; prepared 2026-10-12; approval pending.
This is the current evidence decision, not a history of development runs.

## Assessed implementation

- Source baseline: `602e8dab8e65efdb0bc8db1051ce0006f0d3adfd` (main integration).
- Source tree: `646c4bc3578d26a78203b42025cd93166b9ae93a`.
- Scope: simulation-only HD/HDF PRE/POST, guided UI and dynamic physical model.
- Documentation revision: the Git commit containing this document; documentation
  checks for this candidate are recorded in the current audit report.

## Evidence applicability decision

Hosted software verification run
[38269172854](https://github.com/pmasala/DialysisLab/actions/runs/38269172854)
completed successfully on a tree identical to the integrated implementation above.
The tree identity was checked during integration. Its software execution evidence
is applicable to that unchanged implementation; this is an explicit reuse decision,
not an automatic inheritance from an older milestone. Requirement-level completeness,
independent risk approval and scientific validation are not established by that run.
No claim is made here that this documentation candidate has already passed hosted CI.

| Decision area | Current status | Required closure |
| --- | --- | --- |
| Existing software regression pipeline | Applicable successful execution for identified implementation tree | Assess impact and rerun on subsequent changes |
| Current documentation structure | Candidate under the checks recorded in the audit | Maintainer and independent technical review |
| Requirement acceptance | Not independently approved for any of the 60 registered requirements | Review each acceptance obligation, coverage and result |
| Model calibration/validation | Partial conditional urea fit only | Independent measurements, uncertainty and approved operating envelope |
| Human usability and alarm performance | Not approved | Representative-user tasks and applicable alarm assessment |
| Security/dependency residual risks | Open dispositions | Current inventory/advisory assessment and responsible acceptance |
| Normative/reference release | Blocked | Full-text applicability, safety classification, risk decisions and named approvals |

A reviewer must identify each required case, executed artifact and result before
changing a requirement's current acceptance. Historical records remain available in
the [Project Log](../../project-log/README.md), outside this official result summary.
A passing structural checklist cannot close any of the scientific or human decisions.
