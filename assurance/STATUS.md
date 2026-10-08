# Current status

## Integrated execution checkpoint — 2026-10-08

Branch `feat/integrated-dialysis-roadmap`. Technical phases M1–M7 COMPLETE;
M8 IN PROGRESS; M9 PLANNED. The full project remains incomplete.

M7 implementation `bbecf59` passes 134/134 native and sanitizer tests each,
20 broker/service regressions, 5/5 actual ImGui console tests in headless/WSLg/
instrumented modes, ten device-UI regressions, ten native/ten Compose model runs,
two actual console deployments (each original/replay/aborted run), and four M1
runs plus three isolation probes. Scheduled replay hashes match exactly within
and across the identified native/container builds. The console uses a separate
authenticated administrative channel; patient/circuit/dialyzer/fault calendars
are immutable per run. Pause retains liveness, external STOP aborts, and export
streams verified or explicitly recovered partial artifacts.

The sole M7 review examined `1cf008c` against `2621181`; one P1 and ten P2 findings
are fixed in `bbecf59`, as is unauthenticated-header integration finding M7-V1.
No second review ran. Console peak RSS is 16.55 MiB headless and 18.97 MiB X11,
within the 128 MiB Compose limit with no OOM. Full commands, source identities,
configurations, actual results and rendered artifacts: [M7 evidence](evidence/m7/README.md).
Earlier M1–M6 evidence and failed diagnostic attempts remain preserved.

M7-V2 publication correction passes all normal checks and preserves blocked release
gates; exact log bytes are retained in hashed JSON wrappers.

M8 implementation is in progress at frozen base
`4a1c366acd0050df4c744c2d1eb7d066890d5df4`. Device producers have distinct volumes;
parent-death cleanup and bounded strict JSON are implemented. Six new security
regressions plus four dependency/scanner tests pass; 38 affected process tests pass.
Actual M1 Compose passes four runs/three strengthened isolation probes. The first
supervised experiment aborted because the guard rejected valid container parent
PID 1; the correction passes the second actual experiment deployment. Failures
and artifacts remain in `build/m8-*-first*`. Cppcheck's conservative role warning
is addressed by explicit bounds/roles; the third standalone scan has zero findings.

Initial OSV analysis queried 96 identities with 25 matching queries, never a clean
scan. Updated runtime selection is official pinned CPython 3.12.15/trixie-slim,
signed snapshot 20261007; build and fresh scan/triage remain in progress. CI avoids
both inspected actions: checkout retains vulnerable undici, uploader has an
unresolved transitive license. The public repository is fetched with system Git
and verified against the exact event SHA; hosted Actions is available, not yet run.
SBOMs validate against official CycloneDX 1.6 with installed jsonschema 4.10.3;
final inventories must identify the corrected image/build.

Next executable step: complete M9 integrated matrix, simultaneous actual LVGL
and ImGui workflows, sustained-treatment long runs and reproducible package.
M9 base is `eb290dee95ac078ca3485fe1088161558dccbe59`; acceptance is frozen in
`docs/M9_INTEGRATION.md`. Its single review has NOT run. Preliminary verification passes152 native
tests,36 native/36 Compose matrix runs,30 native/30 Compose fault runs and
simultaneous headless/WSLg device+console flows. The extracted-source package
build and152 tests pass; widget/package closure and two native/two Compose
sustained100000-tick runs are still running. Preserve these pending outcomes.
M9-V1 paused device
STOP and M9-V2 rejected synthetic fixture are recorded in `REVIEWS.md`; fixes
retain existing output/conservation/input bounds.

M8 is technically COMPLETE: 150/150 native/sanitizer tests, 10 device/5 console
tests, ten native/ten Compose model runs, actual deployments and boundary probes.
All four review findings are fixed in `e8c497c`. Corrected hosted CI37730439086
passed; 41 artifacts recover byte for byte. Five actual SBOMs validate; stale
images are rejected. Three real Docker failure cases and two100000-tick M1 runs
pass, RSS max19.47MiB at128MiB. See `evidence/m8/`. The scan retains73 open
advisory IDs; no risk acceptance or clean-image claim. M1–M8 reviews consumed.

No process, Docker or WSLg block. Owned raw PPM captures were compressed only
after independent lossless hash verification; `evidence/m8/capture-storage.json`
records originals/archives/recovery. Do not prune unknown user data or old history.

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
