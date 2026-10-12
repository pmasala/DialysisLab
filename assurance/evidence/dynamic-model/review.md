# Dynamic circuit implementation review

Scope: dynamic chamber/UF control, distributed transport, RPC framing, device
telemetry, numerical failure handling and reference-data claims. Performed by the
implementing Codex session; this is not an independent safety or clinical review.

The review identified and corrected these integration defects:

- The Python device-view parser still counted the older observation fields. It now
  reads `OBS10` consistently with the C++ control/protection/UI readers. The
  in-process cycle checks the actual plant observation with the service intent trailer.
- Distributed patient replies and complete records can exceed old message budgets.
  Patient responses have an explicit 32 KiB budget; other RPC frames remain 4 KiB.
  JSONL records have a 32 KiB bound and remain streamed. Oversize rejection is tested.
  Console history supports 1024 metrics and 300 samples rather than doubling the
  previous total sample-times-metric budget.
- A valve hold could otherwise freeze when a simulation tick was shorter than the
  switching delay. Requested circulation and the interval's delivered feed are now
  distinct, and valve time advances during zero-delivery changeover intervals.
- A fixed iteration count did not establish segment-flux convergence at extreme
  settings. Adaptive relaxation and an explicit convergence result were added.
  Nonconvergence produces zero outputs with `hydraulic_solver`; a forced short
  iteration budget exercises this path.
- A single mixed-pool verifier would incorrectly reconstruct effluent solute mass.
  Verification now uses the actual outlet compartment and countercurrent segment
  concentrations, including dialysate storage. Local RBC/protein inventories and
  their one-tick hydraulic coupling are checked independently.

Regressions after correction include HD/PRE/POST full in-process cycles, finite
actuator/level response, a separate reference holdout, actual LVGL rendering and
bounded message/history checks. Exact commands and source hashes accompany the
execution report. Socket and container execution are separate CI checks.

Remaining evidence gaps are stated rather than silently accepted: manufacturer
clearance test-fluid composition and measurement uncertainty are incomplete in the
selected public table; no measured chamber/controller/rheology/patient dataset was
supplied. The exported profile is a partial transport fit, not a calibrated device.
