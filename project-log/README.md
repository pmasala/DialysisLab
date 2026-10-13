# Project Log — historical analysis only

This log is **outside the official current project documentation**. It helps explain
how the project evolved and investigate earlier failures. Reading it is not a
prerequisite for understanding or auditing the current design.

Start current work at [the official documentation](../docs/README.md). Only evidence
explicitly assessed against the current baseline belongs in its verification status.
A historical pass, a branch name or an old screenshot does not transfer approval.

## Historical archive locations

Historical files retain their paths and bytes to preserve existing evidence hashes,
source references and reproducibility. This index confines their navigation to the
Project Log; they are excluded from `docs/document-set.json`'s official reading set.
Moving signed/hashed evidence just to make a directory look tidy would break its
references. Future historical summaries belong here.

| Archive | Purpose |
| --- | --- |
| [Milestones](../docs/MILESTONES.md), [decisions](../docs/DECISIONS.md) | Development chronology and prior choices |
| [Past status](../assurance/STATUS.md), [reviews](../assurance/REVIEWS.md) | Dated execution/review summaries |
| [Evidence archive](../assurance/evidence) | Immutable earlier trajectories, screenshots, reports and logs; validate identity before reuse |
| [Compatibility trace register](../assurance/traceability.json) | Stable requirement/design/test IDs plus historical result records; current catalogues exclude those result fields |
| M1–M9 documents under `docs/` | Version-specific contracts and earlier predeclared acceptance; retained for legacy scenario investigation |

The current documentation audit sampled historical records to assess provenance;
that does not make the archive part of the official present-tense narrative or
accept all prior results against current code. Current verification must name a
baseline and an explicit reuse/re-execution decision.

## Prior corrective baseline fda5058

[Exact check report](audits/fda5058-checks.json) records the previous corrective
source selection and 86 passing local tests. Its hashes identify that source,
not the later signed dialysate-advection implementation. The current applicability
decision is in [verification status](../docs/testing/STATUS.md).
