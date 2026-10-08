# Decisions and assumptions

| ID | Decision / reason | Limits and review trigger |
| --- | --- | --- |
| INT-001 | Start from clean `1999741`; use `feat/integrated-dialysis-roadmap`. Existing M1 corrections and evidence are retained. | Re-run affected tests as shared sources change. No M1 review rerun. |
| INT-002 | Preserve DL1 and `m1-hd-1`; extended model contracts are opt-in and explicitly versioned. | A compatibility regression blocks the dependent increment. |
| INT-003 | All new initial profiles and alarm thresholds are synthetic demonstration parameters. Use conservation laws and declared numerical approximations; do not invent commercial dialyzer specifications. | Physiological prediction requires independent calibration/validation datasets and review. |
| INT-004 | Keep standard-library numerical and service cores; select only pinned, policy-compatible GUI dependencies when required. | Record transitive libraries, fonts, notices, build/system packages and failure implications before adoption. |
| INT-005 | Preserve shared-kernel/plant/runner/protocol common-cause risks and existing release gaps. Automatic review is defect finding only. | Human risk acceptance, applicable standards, clinical/physical evidence cannot be supplied by software tests. |
| INT-006 | Use `assurance/STATUS.md` as the single progress/next-action checkpoint, this file for decisions, `MILESTONES.md` for the plan, and `assurance/REVIEWS.md` for reviews. | Re-read these checkpoints after context compaction. |
| M2-001 | Use a positive-compliance resistive graph and implicit Euler with bounded pivoted solves. It supports arbitrary branches and clamps without an external solver dependency. | First-order lumped model, no pulsatility/inertance/rheology. Analytic convergence tests define numerical evidence only. |
| M2-002 | Count patient draw minus return, including circuit storage; freeze storage on protective isolation. | Stopping pumps does not prove the circuit is empty or depressurized. Recovery semantics follow in M5. |
| M2-003 | Adopt project-authored mixed-cell transport and synthetic profiles, not a commercial countercurrent dialyzer specification. | M2 prescribes concentration boundaries; M3 must conserve compartment masses before dynamic physiology is claimed. |
| M2-004 | Review fixes require atomic committed snapshots, requested/executed evidence binding and explicit bounded drainage roundoff. | Three applicable P2 findings from the sole M2 review; regression evidence at `assurance/evidence/m2/`. |
| INT-007 | M2 migrates optional `historical_evidence` from a single object to an ordered list, retaining the original object plus superseded evidence. Active schema-1 evidence still must match the current baseline. | No historical record is relabeled as a current execution; release requirements and checker behavior are unchanged. |
| M3-001 | Solve body/circuit concentrations together with an implicit conservative transfer matrix; the C++ plant provides actual hydraulic transfers and membrane clearances. | Partition/refill coefficients are synthetic. No validated ATPase, oncotic, electrical or cardiovascular mechanism is claimed. |
| M3-002 | Keep the circuit prime outside the initial body volume; separately account for compliant storage, gross UF, external input/output and net body loss. | Weight change assumes water density 1 kg/L and fixed nonwater mass; it is not a measured patient weight. |
| M3-003 | Implement a clearly named fixed-pCO2 equilibrium indicator and conserve bicarbonate as a transported inventory. | Dynamic CO2, respiratory control and non-carbonic buffering remain model-validation/development gaps, not evidence inferred from pH curves. |

| M3-004 | Preserve computed concentration roundoff without clipping, reject oversized numeric inputs, and validate proposed patient replies before committing state. Evidence checks require finite inventories and compartment/summary consistency. | Five findings from the single M3 review; targeted real-service and tampered-evidence regressions. |

| M4-001 | Use a mixed preparation reservoir, two hydraulic/contaminant-surrogate barriers and explicit pre-circuit versus post-body delivery. Preserve separate actual gross/net ledgers. | No sterility, axial dialyzer, thermal blood model or exact net-prescription claim. |
| M4-002 | Quality protection blocks replacement, UF and dialysate exchange while blood circulation remains subject to independent pressure/validity protection. | Synthetic observed thresholds only; hidden contamination is deliberately not observable. |

| M5-001 | Keep effective lifecycle/constraints in plant arbitration; device clients see queued intent separately. Use a dedicated device volume rather than exposing control/plant.sock. | No UI fault/clock/patient/truth administration; native same-UID remains trusted. |
| M5-002 | Prime/clean through external source-to-waste circuit flows with explicit patient-side ledgers and isolation. | Flushed volume is a synthetic readiness criterion, not air removal or disinfection validation. |
| M5-004 | Low-flow/filter latches require a fresh run because the current circuit has no isolated functional recovery test; retained pressure is never erased. | Zero stopped-flow observations cannot prove a fault cleared; other resettable hazards require three safe recovery cycles. |
| M5-003 | Aggregate hazard masks, immediate differentiated actions, annotation-only ACK/silence, no protective overrides; reset requires safe measured recovery. | No silent pressure reset or automatic resumption after process restart. |

The WSL2 environment has an X11 socket (`/tmp/.X11-unix/X0`) but DISPLAY is
unset; desktop availability remains to be tested in M6. SDL development headers
are currently absent. No global environment, credential, certificate or permission
changes are authorized merely to bypass a block.

| M5-005 | Reconstruct body volume from body-boundary transfers, independently checking whole-system source/waste/storage balance. Verify protection evidence from authoritative masks as well as redundant latch fields. | Two P2 findings in the sole M5 review; do not widen physical limits or accept contradictory rehashed evidence. |

| M6-001 | Select pinned LVGL core/SDL2 software rendering with an original project font and disabled optional codecs/assets. | Exact versions/features/licenses/notices must be recorded before adoption; no implicit license exception. |
| M6-002 | Keep LVGL on the UI thread and bounded RPC work on a separate worker; display authoritative state and intent separately. | Invalid/stale/disconnected measurements never become invented zero outputs; UI is not a protective authority. |
| M6-003 | Add process-session-bound device requests to prevent old confirmation IDs from applying after restart. | Freshness token is not authentication; mount/role boundaries remain required. |
| M6-004 | Add optional wall pacing to the external runner only. | Virtual time remains integer/barrier driven, heartbeats continue during waits, and device UI exposes no experiment-clock control. |
| M7-001 | Freeze base `26211813a79d5f05720071de0b51df8089997476`; immutable scheduled configurations and fresh role processes make replay meaningful. | External emergency STOP stays effective and makes the run interrupted, never falsely replayable. |
| M7-002 | Use a bounded authenticated Unix broker and Dear ImGui/selected SDL2 console; native same-UID is trusted, Compose mounts separate administration. | No Docker socket, arbitrary execution/path export or hidden truth in control/protection; remaining shared resources stay in the threat model. |
| M7-003 | Per-role fixed-command supervisors allow repeated Compose runs without resetting a terminal plant in place. | Activation carries only generated run ID; new runs start isolated state and preserve old evidence. |

| M8-001 | Freeze base `4a1c366acd0050df4c744c2d1eb7d066890d5df4`; strengthen owned device endpoints and Linux parent-death cleanup before integrated deployment. | Compatibility aliases preserve DL1 device APIs; no process exit is treated as observed zero output. |
| M8-002 | Keep security/SBOM/static/advisory/CI results distinct from standards and human release decisions. | Exact selected dependencies, actual execution coverage and unresolved findings must remain visible; no implicit license exception. |
| M8-003 | CI artifact contract v2 preserves exact original bytes in bounded hashed envelopes; only validated outstanding release obligations are exempt from software failure. | Failed/malformed checkers and retention failures remain failures; schema-1 historical logs are not relabeled byte-exact. |
| M8-004 | Inspect application identities in each immutable container image and reject stale source/runtime inputs before generating its merged SBOM. | Build metadata is trusted but unsigned; platform advisory findings and layer/license gaps remain open. |
