# Current status

## Integrated execution checkpoint — 2026-10-08

Branch `feat/integrated-dialysis-roadmap`, starting commit `1999741`. M1 technical
scope COMPLETE with its supplied review resolved; M2 IN PROGRESS (candidate implemented and tested; single review next); M3–M9 PLANNED. Full project remains incomplete. The next executable
step is to commit the tested M2 candidate and invoke its single read-only review
against `1999741`; then address findings and retain final evidence. See
[the persistent plan](../docs/MILESTONES.md), [decisions](../docs/DECISIONS.md) and
[review register](REVIEWS.md). Baseline structural checks were repeated: zero
errors; 66 trace release gaps, 184 open standards entries and 12 gaps remain.


Review update, 8 October 2026: the three M1 review defects are corrected and have
passed real process and Docker regression checks. The tested implementation is
`da5ccc2`; [current evidence](evidence/m1-review/README.md) records exact commands,
source/configuration/binary hashes and results. The original `b598a5c` evidence is
retained in `evidence/m1/` as historical evidence, not verification of these fixes.

## Review corrections and actual verification

| Area | Implemented behavior and observed result |
| --- | --- |
| Failed STEP RPC | Control and protection replies were separately discarded over real sockets after plant acceptance. The runner attempts both decisions, sends no COMMIT/ADVANCE for the aborted tick, requests HALT and records the cause and stop state. |
| Pending decisions | HALT, protocol shutdown and the independent wall watchdog discard prepared ticks and permanently prevent further commits. Tests challenge late COMMIT, PREPARE, DEMAND and PERMIT against the real plant. |
| Stop uncertainty | HALT acknowledgment is separate from observed STATUS. Failed delivery can report still-running outputs; failed observation remains null. Tests verify the later watchdog without retroactively claiming an earlier confirmed stop. |
| Streaming trajectory | Manifest schema 2 and JSONL v1 replace new-run JSON arrays. One record is written at a time; SHA-256 tracks exactly written bytes. Readers validate sequence and recover complete records after actual runner SIGKILL. |
| 100000-tick memory | Two full Compose runs completed under 128 MiB. Peak RSS 22.50 MiB (acceptance <=64 MiB), RSS headroom 105.50 MiB; cgroup peak including cache 71.14 MiB. No OOM kill. Both 100000-record hashes matched independent scans and each other. |
| Failed Compose evidence | Aborted runner exit 7, pre-start exit 1, and extraction failure with original exit 7 were preserved. All available logs/artifacts were collected before cleanup. Failed extraction retained the volume; real recovery verified files before test-owned removal. |
| Native and sanitizer regression | 47/47 tests passed natively and 47/47 with AddressSanitizer/UBSan, including all 12 original traceability tests. |
| Existing deployment/reproduction | Four original Compose runs and two isolation probes passed. Native/container JSONL bytes and separate native executable hashes match. |
| Assurance | Structural checks pass. Trace release gate remains blocked with 66 gaps; all 184 standards entries, 12 edition/applicability gaps and nine release prerequisites remain open. No check was weakened. |

Nine M1 requirements are implemented with passing execution evidence, while
independent design/evidence review and residual-risk acceptance remain pending.
Six broad roadmap requirements remain draft and their six protocols remain planned.
Passing these regressions does not complete the full reference project or establish
standards conformity. See [the interface contract](../docs/M1_INTERFACES.md),
[review acceptance plan](../docs/M1_REVIEW_FIXES.md) and [runbook](../docs/M1_RUNBOOK.md).

## Preserved scope and remaining limitations

M1 remains a deliberately limited deterministic HD demonstration: separate C++
control/protection/plant, separate Python patient/runner, synthetic resistance,
measured pressure, fluid-volume accounting and direct protective arbitration.
The model and demonstration thresholds have not been expanded or recalibrated.

Full HD treatment workflows, pre/post HDF, online substitution preparation
(mixing, thermal behavior, filtration, hydraulics and delivery), configurable
circuits and multiple dialyzers, electrolyte/solute and acid-base models, LVGL
device UI and the separate experiment console remain required.

Remaining decisions include independent calibration/validation and authorized data,
clinical/essential-performance limits, hazard-specific recovery and residual-risk
acceptance, security/SBOM/vulnerability review, EU-first standards applicability,
usability and downstream physical-device evidence. Native Linux outside this WSL2
host is not newly validated. Shared kernel/runner/transport/plant remain common
causes; native same-user mode does not provide container mount isolation.

A lost stop request leaves actual state unconfirmed until observed; watchdog timing
is a tested development policy, not hard real-time assurance. Patient failure after
plant commit still produces an aborted, incomplete tick without distributed rollback.
JSONL recovery covers process interruption, not storage-device or power-loss
survival; full long-run streams are retained in ignored `build/`, with hashes and
measurements committed as evidence. Measured memory margins apply to the recorded
configuration/image. Clinical safety and calibrated physiology are not claimed.

Pinned dependencies and source-only publication rules remain unchanged apart from
explicitly admitting project-owned JSONL evidence and named build inputs. Licensed
standards and private extracts/images remain outside Git, Docker contexts and
public artifacts. Image redistribution and a complete reference release are not
approved by these checks.
