# Current status

## Integrated execution checkpoint — 2026-10-08

Branch `feat/integrated-dialysis-roadmap`. Technical phases M1–M6 COMPLETE;
M7 IN PROGRESS; M8–M9 PLANNED. The full project remains incomplete.

M6 implementation `2ee31ad` passes 114/114 native and sanitizer regressions,
10/10 actual UI/demo tests in headless, WSLg and instrumented builds, two real
widget-driven Compose deployments, twelve native/twelve Compose exact-replay
scenarios, four M1 runs and three isolation probes. The UI supports guarded
HD/pre/post prescriptions, lifecycle requests, measured telemetry/trends,
alarms and session/stale/disconnect handling. Actual 1100x890 captures and widget
input/output logs are retained. UI peak RSS is 9.11 MiB headless and 19.55 MiB
X11 within 128 MiB; no OOM. [M6 evidence](evidence/m6/README.md) records exact
commands, identities, dependencies, results and limits.

The sole M6 review (`00baa58` against `445c667`) found six P2 defects fixed in
`5552622`; final visual inspection found dialog contrast M6-V1, fixed in
`2ee31ad` with rendered-pixel verification. All applicable findings pass targeted
regression. M1–M6 reviews are consumed: never rerun them. M7 has not been reviewed.
Earlier long-run/failure evidence remains preserved; no new 100000-tick graphical
endurance claim is made. Release and independent-assurance gates remain blocked.

Next executable step: finish M7 review corrections and targeted regressions, commit
the corrections and run clean-build native/sanitizer/GUI/Compose integration evidence.
The sole M7 review examined candidate `1cf008c` against `2621181` and returned one
P1 plus ten P2 findings; it is consumed and must not run again. The journal/STOP,
shutdown ownership, restart/revision, storage-bound, evidence identity, GUI reply,
pacing and inventory fixes are implemented and under regression. Also fix M7-V1,
the unauthenticated metadata header. Review commands, output and disposition are in
`assurance/REVIEWS.md` and `build/reviews/m7*`. Continue M8/M9 after final M7 evidence.

M7 constraints: immutable scheduled configuration, separate authenticated admin
channel, fixed-role Compose supervisors, actual STOP evidence and streaming exports.
Native hard-kill orphan cleanup and shared device-producer ownership are explicit
M8 hardening work, not hidden assumptions of physical isolation.

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

Earlier evidence remains historical, with active regression links identifying the
current implementation. The external experiment console,
security/SBOM/CI and final integrated package remain required. No roadmap feature
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
and additional availability/security controls are tracked for M8.

Publication and Docker inputs remain explicit allowlists. Licensed standards,
extracts/images and private material remain excluded. Source-package checks are
not approval to redistribute an unassessed complete image or medical product.
