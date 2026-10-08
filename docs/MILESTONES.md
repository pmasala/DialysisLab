# Integrated simulator execution plan

Execution started 2026-10-08 from `1999741` on
`feat/integrated-dialysis-roadmap`. Preserve the M1 implementation and evidence.
This is simulation software and a development template, not a medical device,
clinical validation, standards approval, or hardware independence demonstration.

## Procedure and checkpoints

For each phase: freeze its base commit, requirements, hazards and acceptance;
implement and test; commit a candidate; run **one** read-only automatic review
against that base; record and resolve findings; run regressions; commit evidence
and proceed. M1's supplied review has already consumed its review opportunity.
An unavailable review is REVIEW_BLOCKED, never an approval. See
[review register](../assurance/REVIEWS.md), [decisions](DECISIONS.md), and the
authoritative [progress checkpoint](../assurance/STATUS.md).

## Phase requirements and acceptance

| Phase / initial commit | Required behavior | Acceptance and pertinent risks |
| --- | --- | --- |
| M1 / `a604f07` (fixes `57b27e2`) | Preserve deterministic separated processes, terminal abort, streaming records, failure collection. | Existing real process and Compose regressions, 100000-tick RSS; HAZ-001–004. Evidence at `evidence/m1-review/`. |
| M2 / `1999741` | Configurable hydraulic network, compliance/transients, pumps, tubes, clamps, sensors, multiple synthetic dialyzers; diffusion, convection and UF. | Independent water/solute conservation, analytic limits, numerical convergence, component/fault changes, actual process integration; HAZ-002–004. |
| M3 / `40533e4` | Python fluid/solute compartments, water/urea/Na/K and explicitly bounded further electrolyte/acid-base models. | Positive conservative ledgers, independent calculations, zero/equilibrium/external-flux cases, synthetic overload/imbalance scenarios; HAZ-003–004. |
| M4 / `47ffc5e` | HD, pre/post HDF, online mixing/heating/filtration/routing and replacement. | Gross/net/circuit balances, composition/thermal/route/integrity faults, observable versus hidden contamination; HAZ-003,006. |
| M5 / `e1c8ae2` | Machine states, hazard-specific actions, alarms, latches/reset/recovery/restart and communication policies. | All state transitions, timing, continuing hazards despite acknowledgment, conflicting commands and process failures; HAZ-002,004,005,006. |
| M6 / `445c667` | C++ LVGL device UI connected to authoritative services, prescription/telemetry/trends/alarms. | Real workflow, input/confirmation/disconnection tests, graphical evidence where available, no simulation administration; HAZ-001,004,005. |
| M7 / after M6 | Separate experiment console with configuration, scheduling, truth, replay/comparison/export and batch access. | Actual service runs, pause/resume, reproducibility, administration isolation; HAZ-001,003. |
| M8 / after M7 | Threat mitigations, bounded inputs, resource/isolation controls, dependency inventory/SBOM and CI. | Abuse/failure tests, available scans, reviewed licenses/pins/notices, unchanged release obligations and deny-by-default publication; HAZ-001–006. |
| M9 / after M8 | Integrated matrix, reproducible package, Linux/WSL2 quickstart and complete supported lifecycle evidence. | Modes/patients/dialyzers/faults/long runs/recovery/UI/console/headless/deployments; regressions and one review of new integration/package changes. |

Each phase expands these targets in its model/interface document and traceability
records **before** implementation. Tolerances and synthetic limits are declared
there, not inferred from passing output. Results identify actual source/build,
configuration, dependencies, commands, expected criteria and artifacts. Calibration,
independent risk acceptance, unavailable standards and physical product obligations
remain separate open gates. No phase may discard a later phase from this roadmap.

## Implementation order

1. Preserve the DL1 M1 compatibility path; introduce explicitly versioned extended
   configurations and observations for the new circuit model.
2. Couple conservative plant transport to Python patient compartments, then add
   substitution and preparation with distinct gross/net ledgers.
3. Add stateful control/protection APIs before implementing their actual UI client.
4. Add external administration/experiment workflows, security checks and inventories.
5. Run the full matrix and package only explicitly approved project files/assets.

Environmental blocks do not prevent independent implementation/testing. Record
the exact failing command and prerequisites, continue executable work, and never
translate BLOCKED into PASS. Push this branch without rewriting origin history
when access is available.
