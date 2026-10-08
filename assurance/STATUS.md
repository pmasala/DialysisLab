# Current status

## Integrated execution checkpoint — 2026-10-08

Branch `feat/integrated-dialysis-roadmap`, published through verified M4 checkpoint. M1–M4 technical scope COMPLETE;
M5 IN PROGRESS; M6–M9 PLANNED. The full project remains incomplete.

M4 implementation `cca9ce6` passes 87/87 native and 87/87 sanitizer tests, 24 native/
24 Compose treatment scenarios, 14 M2/M3 and four M1 Compose regressions plus two
isolation probes. Two native/two Compose 100000-tick runs pass with identical
hashes, gross UF 166665 mL, positive body water, confirmed native HALT and no OOM.
Runner Docker RSS peaks at 22.31 MiB; cgroup file cache reaches the 128 MiB budget.
See [M4 evidence and measurement limits](evidence/m4/README.md). Its single review
found one P1/five P2 defects, all fixed and verified. No M1–M4 review may be rerun.

M5 candidate `a490984` passed 105/105 native and sanitizer tests, 22 native/22
Compose workflows with identical hashes, 12 M2–M4 Compose compatibility runs,
four M1 runs and three isolation probes. Its single review completed (exit 0)
with two applicable P2 findings: isolated flush/body roundoff and incomplete
alarm-mask evidence checks. Both fixes are implemented; targeted regressions
passed (20/20), committed as `c54422c`. The first real long runs both exposed
a finite-subnormal parser rejection at tick 4662; failed artifacts are retained.
That integration defect is now fixed and its actual transport regression passes.
Next executable step: commit this follow-up, reconfigure a clean build, repeat
final regressions and the 100000-tick priming case in native/Compose,
record evidence, then proceed to M6. M5 review is consumed; never rerun it.
Exact review metadata/output: `build/reviews/m5.json`, `build/reviews/m5-output.txt`.
GUI feasibility and design notes remain in `build/dependency-inspection/` and
`build/m6-design-notes.md`; no new third-party dependency is adopted by M5.

Persistent checkpoints: [plan](../docs/MILESTONES.md),
[decisions](../docs/DECISIONS.md), [reviews](REVIEWS.md). The synthetic hydraulic, patient and treatment models are numerically tested but
uncalibrated. Lifecycle/alarm workflows, UI/console, hardening/CI and final
integration remain to be implemented. All
independent assurance and regulatory release obligations remain open.

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
