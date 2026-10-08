# Current status

## Integrated execution checkpoint — 2026-10-08

Branch `feat/integrated-dialysis-roadmap`. Technical phases M1–M8 COMPLETE;
M9 corrections and final verification IN PROGRESS. Formal release remains blocked.

M9 candidate `4719ebc` received its sole review: P1 long-run fixture capacity,
P2 extracted-source Git assumption, P2 generated Compose fixture permissions.
All three are implemented with six targeted integration regressions passing.
The actual Linux process-death regression and ESRCH/ENOENT/access-error tests pass;
this addresses the failed candidate hosted CI37733002033 without suppressing
permission failures or extending its timeout. Review count remains one per phase.

Corrected fixtures use replacement70mL/min for sustained HDF and R0.9/KUF1 for
the large integrated dialyzer. Actual1500-tick runs deliver net5mL/min without
alarms. Thresholds and acceptance bounds are unchanged. Full100000-tick repeats,
corrected deployment matrix and final source-package verification remain pending;
the initial failed long runs and their original manifests are retained.

M8 corrected hosted CI37730439086 passed; all41 artifacts recover byte for byte.
150 native/sanitizer tests, actual UI/console deployments, three Docker failure
cases and two100000-tick M1 runs passed (RSS max19.47MiB at128MiB). Five actual
SBOMs validate; stale images are rejected. The scan retains73 open advisory IDs,
without risk acceptance or a clean-image claim. See `evidence/m8/`.

There is no process, Docker or WSLg access block. Owned large trajectories and
raw captures may be archived only after byte-exact independent round-trip checks;
original failures remain failures, with recovery metadata. Preserve unknown user
data. Next: commit review corrections, rebuild, run final native/Compose/long/
package verification, recover corrected hosted CI and publish supported evidence.

Persistent checkpoints: [milestone plan](../docs/MILESTONES.md),
[decisions](../docs/DECISIONS.md), [reviews](REVIEWS.md).

## Implemented increments and evidence

| Phase | Implemented and verified scope | Evidence |
| --- | --- | --- |
| M1 | Deterministic separate processes, direct protection, aborted STEP handling, streaming JSONL, retained failed Compose results, actual 100000-tick memory tests. | [Review corrections](evidence/m1-review/README.md) |
| M2 | Configurable compliant hydraulic graph, synthetic dialyzers, diffusion/convection/UF and independent numerical balances. | [M2](evidence/m2/README.md) |
| M3 | Conservative Python body/circuit water and six species, external transfers, water-only weight and limited fixed-pCO2 indicator. | [M3](evidence/m3/README.md) |
| M4 | HD/pre/post HDF, mixed preparation/temperature/filter hydraulics, replacement accounting and directly enforced fluid-quality protection. | [M4](evidence/m4/README.md) |
| M5 | Guarded machine lifecycle, external priming/cleaning ledgers, aggregate hazard-specific constraints, ACK/silence/reset/restart policies and device-only endpoints. | [M5](evidence/m5/README.md) |
| M6 | Actual LVGL/SDL device UI, session-bound requests, precision/confirmation, sensor age/trends, alarms and native/Compose graphical verification. | [M6](evidence/m6/README.md) |
| M7 | Separate real ImGui console and authenticated broker, immutable configuration/fault schedules, virtual pause, fresh native/Compose replay, comparison and retained exports/failures. | [M7](evidence/m7/README.md) |

| M8 | Process/input/device-boundary hardening, actual-image SBOMs, scans, exact hosted CI artifact recovery and retained open dependency findings. | [M8](evidence/m8/README.md) |

Earlier evidence remains historical, with active regression links identifying the
current implementation. The final integrated package remains required. No roadmap feature
has been removed to make a phase or release gate pass.

## Open gates and limits

All 184 standards checklist entries, 12 edition/applicability gaps and nine release
prerequisites remain open. Independent design/evidence review, clinical/physical
performance, calibration/validation, human risk acceptance and standards conformity
are not supplied by these software tests or AI reviews. Normal structural/publication
checks must pass; release gates remain blocked.

Models and thresholds are synthetic and uncalibrated. Conductivity does not identify
individual species; contamination/breaches and stuck detectors can remain latent.
No microbial quality, sterility, validated cleaning/air clearance, respiratory
regulation or hardware independence is claimed. No pump/filter functional reset is
implemented; those latches require a fresh run. Common plant/runner/transport/
configuration/kernel resources remain causes shared by control and protection.

HALT request/acknowledgment is distinct from observed outputs; lost delivery can
remain unconfirmed. Patient failure after plant commit aborts without distributed
rollback. JSONL recovery covers process interruption, not power-loss durability.
Memory measurements apply to the recorded configurations; RSS headroom is not
reserved cgroup headroom. Native same-UID mode is trusted development, and native
Linux outside the WSL2 host is not newly validated. Device-volume producer ownership
and availability/security controls are implemented and verified in M8; residual trusted-host/common-cause risks remain.

Publication and Docker inputs remain explicit allowlists. Licensed standards,
extracts/images and private material remain excluded. Source-package checks are
not approval to redistribute an unassessed complete image or medical product.
