# Current status

Review update, 8 October 2026: the review found three defects in STEP failure
arbitration, trajectory memory and failed Compose evidence retention. Corrections
and 47 native tests now pass; real Docker revalidation is pending. Do not treat M1
as completed on the basis of the historical results below. This is a limited headless HD
reference slice, not a complete dialysis system, calibrated physiology, clinically
usable software, or a standards-conforming medical device.

## Implemented M1 behavior

- Reproducible CMake C++17 builds for separate control, protection and plant
  processes; separate Python patient and deterministic scenario runner.
- Five non-root, network-disabled Compose services with role-specific socket
  mounts. Control/protection receive modeled observations and cannot reach
  administration/patient endpoints in the container configuration.
- Fixed virtual ticks, a versioned DL1 interface, explicit sequences/validity and
  a separate wall-clock liveness lease. Pause heartbeats do not integrate fluid.
- Synthetic HD resistance, capped blood flow, measured circuit pressure and
  separate patient/effluent ledgers. Independent Decimal conservation checks.
- Occlusion and invalid/missing/stale/future/replayed observations; protection
  sends direct plant constraints. Conflicting control commands and subsequent
  permits cannot clear a latch. Process failures follow documented abort policies.

## Historical verification (before the review corrections)

Tested implementation revision: `b598a5c` (full source and executable hashes in
[evidence/m1/summary.json](evidence/m1/summary.json)). The subsequent evidence/status
commit does not change executable sources. Commands and raw records are indexed in
[evidence/m1/README.md](evidence/m1/README.md) and [the runbook](../docs/M1_RUNBOOK.md).

| Check | Observed result |
| --- | --- |
| Native Release build | GCC 13.3.0, CMake 3.28.3, Python 3.12.3; warnings treated as errors; succeeded. |
| Native suite | 32 tests passed, including all 12 original traceability tests. |
| AddressSanitizer + UBSan Debug suite | Same 32 tests passed; fatal sanitizer errors enabled; service logs checked. |
| Pinned container build | GCC 14.2.0, CMake 3.31.6, Python 3.12.14; succeeded. Exact package inventories retained. |
| Compose acceptance | Four 20-tick runs (nominal twice, occlusion twice), all completed; two actual role-boundary probes denied access. |
| Reproduction | Same-configuration repeats and native/container trajectories byte-identical; two separately configured native builds have identical executable SHA-256 values. No cross-toolchain binary identity claim. |
| Fluid conservation | Nominal 1/3 mL removal; occlusion 1/12 mL; zero/partial-flow and 100000-step patient ledger cases within 1e-8 mL. |
| Protection | Tick-5 occlusion observed at 600 mmHg against a synthetic 250 mmHg threshold; zero blood/UF and closed clamp by the end of that 100 ms interval. Also passes with control killed. |
| Failure/clock policy | Invalid sensor cases, killed services, killed scheduler heartbeat process and a 2.3 s virtual pause pass; wall timeout latches without advancing virtual time. |
| Assurance checks | Zero structural errors. All 184 standards entries and 12 edition/applicability gaps remain open. |
| Release gates | Trace release gate remains blocked (60 gaps); standards release gate remains blocked. No check was weakened. |

M1 requirements are **implemented**; affected execution records are being revalidated
and independent review remains pending. Six broader starter requirements remain draft and their six
protocols remain planned. All nine release prerequisites remain open. Test passes
are neither reviewer approval nor risk acceptance.

## Remaining roadmap and decisions

Full HD treatment workflows, pre/post HDF, online substitution preparation
(mixing, thermal behavior, filtration, hydraulics and delivery), configurable
circuits and multiple dialyzers, electrolyte/solute and acid-base models, LVGL
device UI and the separate experiment console all remain required. No feature
was removed to make M1 pass.

Open work includes independent model calibration/validation and authorized data;
approved clinical/essential-performance limits and hazard-specific recovery;
substantive safety/security/standards and EU-first applicability reviews; complete
risk analysis, SBOM/vulnerability triage, UI/usability and downstream physical-device
evidence; and validation on native Linux beyond this WSL2 host. The M1 model omits
compliance, realistic transients, refill, chemistry and clearance. Shared
kernel/runner/transport/plant remain common causes. Native same-user mode does not
provide container isolation. Patient failure after plant commit is explicitly
recorded as an incomplete tick in an aborted run, without distributed rollback.

The exact M1 dependency pins, original-source publication allowlist and Docker
context are documented; image redistribution and the full reference release have
not been approved. Licensed standards and derived private source material remain
outside the repository and Docker context.
