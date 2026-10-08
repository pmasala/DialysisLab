# Current status

## Integrated execution checkpoint — 2026-10-08

Branch `feat/integrated-dialysis-roadmap`. Technical phases M1–M5 COMPLETE;
M6 NEXT; M7–M9 PLANNED. The full project remains incomplete.

M5 implementation `443f73f` passes 108/108 native and 108/108 sanitizer tests,
22 native/22 Compose workflows with exact replay, 12 M2–M4 Compose compatibility
runs, four M1 runs and three isolation probes. Two native/two Compose 100000-tick
priming runs pass at the 100000 mL body-volume ceiling; no OOM, Docker runner RSS
22.20 MiB within 128 MiB, with reclaimable file cache reaching the total limit.
Independent water/species errors stay below 1e-6. Full results and commands:
[M5 evidence](evidence/m5/README.md).

The single M5 review found two P2 defects, fixed in `c54422c`; subsequent real
integration exposed finite-subnormal parsing, fixed in `443f73f`. Both failed-run
artifacts and all final results are retained. M1–M5 reviews are consumed: never
rerun them. M6 has not been reviewed.

Next executable step: freeze the M6 base at this verified evidence checkpoint,
record requirements/acceptance and implement the real LVGL device UI, including
session-aware requests, stale data/reconnection, input/confirmation flows and
actual native/Compose graphical/headless evidence. Continue automatically through
M7–M9. Feasibility (not UI implementation) and dependency inspections are retained
in `build/dependency-inspection/` and `build/m6-design-notes.md`. WSLg X11 software
windows and LVGL with an original font have actually rendered; no third-party GUI
dependency is adopted by M5.

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

Earlier evidence remains historical, with active regression links identifying the
current implementation. The full LVGL device UI, external experiment console,
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
