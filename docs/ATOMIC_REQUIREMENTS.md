# Atomic acceptance obligations

Document ID SRS-02; proposed technical baseline, independent approval pending.

Read [parent requirements](REQUIREMENTS.md) first. These obligations clarify selected
compound requirements without replacing or reducing any parent obligation. They are
generated from [the controlled register](../assurance/current-obligations.json).
Limits characterize the simulator implementation; they are not clinical thresholds.
A test allocation is a coverage argument to review, not a recorded execution result.

The [coverage matrix](testing/COVERAGE.md) makes incomplete cases visible.

## SWF-01 — UI-REQ-002

The guided machine shall complete initial checks before entering preparation.

**Acceptance:** All seven test bits, three safe samples, no alarm and configured test duration are required. Missing integrity retains self_test.

**Coverage:** Integrity negative case and nominal completion exist; six other individual check failures need explicit cases.

**Design:** [docs/design/TREATMENT.md](../docs/design/TREATMENT.md).

**Existing test:** `test_guided.GuidedUnitTests.test_guided_machine_protocol_and_actual_lvgl_view`.

## SWF-02 — UI-REQ-002

Priming shall end on delivered flush volume.

**Acceptance:** Below prime_mL retain priming; at or above target with safe guard enter configuration and set primed. The crossing-tick transfer bounds overshoot.

**Coverage:** direct assertion or named fixture; current result acceptance pending

**Design:** [docs/design/TREATMENT.md](../docs/design/TREATMENT.md).

**Existing test:** `test_guided.GuidedUnitTests.test_guided_machine_protocol_and_actual_lvgl_view`.

## SWF-03 — M5-REQ-002

Isolated priming and cleaning shall not remove or return patient water.

**Acceptance:** Patient draw/return are zero during isolated flush; body and source/waste balances independently remain within 1e-6 mL/mmol.

**Coverage:** direct assertion or named fixture; current result acceptance pending

**Design:** [docs/design/TREATMENT.md](../docs/design/TREATMENT.md).

**Existing test:** `test_guided.GuidedUnitTests.test_in_process_hydraulics_complete_cycle_and_patient_transactions`.

## SWF-04 — UI-REQ-002

Starting treatment shall require priming and an explicit patient connection.

**Acceptance:** Reject START before CONNECT. CONNECT is accepted only from primed configuration; connected alone does not start flow.

**Coverage:** direct assertion or named fixture; current result acceptance pending

**Design:** [docs/design/TREATMENT.md](../docs/design/TREATMENT.md).

**Existing test:** `test_guided.GuidedUnitTests.test_guided_machine_protocol_and_actual_lvgl_view`.

## SWF-05 — UI-REQ-002

Treatment duration shall count delivered treatment time.

**Acceptance:** A pause does not consume treatment duration; automatic finished occurs at the configured endpoint and preserves accumulated time across resume.

**Coverage:** direct assertion or named fixture; current result acceptance pending

**Design:** [docs/design/TREATMENT.md](../docs/design/TREATMENT.md).

**Existing test:** `test_guided.GuidedUnitTests.test_guided_machine_protocol_and_actual_lvgl_view`.

## SWF-06 — UI-REQ-002

Blood return shall start only by confirmed request after treatment.

**Acceptance:** RETURN requires finished and patient_connected; completion on returned_mL >= return_target_mL enters disconnecting. UF/substitution are off during return.

**Coverage:** direct assertion or named fixture; current result acceptance pending

**Design:** [docs/design/TREATMENT.md](../docs/design/TREATMENT.md).

**Existing test:** `test_guided.GuidedProcessTests.test_full_guided_cycle_preserves_water_solutes_and_stage_evidence`.

## SWF-07 — UI-REQ-002

Disinfection shall require explicit disconnection and both endpoint conditions.

**Acceptance:** CLEAN is rejected until disconnected. Complete only when configured duration and flush target have both been reached.

**Coverage:** direct assertion or named fixture; current result acceptance pending

**Design:** [docs/design/TREATMENT.md](../docs/design/TREATMENT.md).

**Existing test:** `test_guided.GuidedUnitTests.test_guided_machine_protocol_and_actual_lvgl_view`.

## SWF-08 — M5-REQ-004

Alarm handling shall not restart circulation.

**Acceptance:** ACK/silence do not clear restrictions. Reset requires recovery with three safe observations; guided restart requires separate RESUME. Terminal stop cannot resume.

**Coverage:** Legacy reset test plus guided fixture; complete alarm-by-guided-phase matrix is a planned test obligation.

**Design:** [docs/design/TREATMENT.md](../docs/design/TREATMENT.md).

**Existing test:** `test_machine.MachineTests.test_reset_needs_three_safe_cycles_and_never_resumes_automatically`.

## SUI-01 — UI-REQ-002

The guided view shall display authoritative phase progress.

**Acceptance:** Priming/return use volume fractions, therapy delivered time, cleaning the lesser time/volume fraction. Manual/stale/blocked/zero-flow estimates do not display a running ETA.

**Coverage:** direct assertion or named fixture; current result acceptance pending

**Design:** [docs/design/INTERACTION.md](../docs/design/INTERACTION.md).

**Existing test:** `test_guided.GuidedUnitTests.test_guided_machine_protocol_and_actual_lvgl_view`.

## SUI-02 — UI-REQ-002

Only permitted treatment operations shall be presented.

**Acceptance:** CONNECT visible only in eligible connection state; blocked/stale views suppress mutations; STOP remains available across tabs. Server guards also reject forbidden requests.

**Coverage:** direct assertion or named fixture; current result acceptance pending

**Design:** [docs/design/INTERACTION.md](../docs/design/INTERACTION.md).

**Existing test:** `test_guided.GuidedUnitTests.test_guided_machine_protocol_and_actual_lvgl_view`.

## SUI-03 — UI-REQ-002

Blood and active substitution rates shall be editable during safe therapy.

**Acceptance:** Accept confirmed blood 0..500 and HDF substitution 2..120 mL/min with sum <=500. HD requires substitution zero. Reject mode/net-UF changes during therapy. Preserve treatment time.

**Coverage:** direct assertion or named fixture; current result acceptance pending

**Design:** [docs/design/INTERACTION.md](../docs/design/INTERACTION.md).

**Existing test:** `test_guided.GuidedUnitTests.test_guided_machine_protocol_and_actual_lvgl_view`.

## SUI-04 — M6-REQ-005

A confirmation shall not apply to a different process session.

**Acceptance:** Reject stale epoch and clear pending client state after session replacement; do not retry ambiguous critical requests automatically.

**Coverage:** Direct old-confirmation rejection after session replacement; independent acceptance pending.

**Design:** [docs/design/INTERACTION.md](../docs/design/INTERACTION.md).

**Existing test:** `test_device_sessions.DeviceSessionTests.test_restart_reusing_intent_number_cannot_accept_old_confirmation`.

## SIF-01 — M1-REQ-007

Any failed decision STEP shall prevent committing that tick.

**Acceptance:** Attempt both services; if either RPC fails, send no COMMIT/ADVANCE, request HALT, query stop separately and abort. Exercise lost replies after command acceptance.

**Coverage:** direct assertion or named fixture; current result acceptance pending

**Design:** [docs/design/INTERFACES.md](../docs/design/INTERFACES.md).

**Existing test:** `test_machine.MachineTests.test_lost_step_each_role_stops_and_invalidates_pending_m5_decisions`.

## SIF-02 — REQ-002

Plant arbitration shall enforce the union of active restrictions.

**Acceptance:** A conflicting positive demand cannot remove an active mask; simultaneous hazards restrict all affected outputs before the next integration.

**Coverage:** direct assertion or named fixture; current result acceptance pending

**Design:** [docs/design/INTERFACES.md](../docs/design/INTERFACES.md).

**Existing test:** `test_machine.MachineTests.test_simultaneous_hazards_apply_before_commit_and_defeat_hostile_control`.

## SIF-03 — REQ-004

Invalid protection observations shall constrain outputs before integration.

**Acceptance:** Sequence/time/validity must match the current frozen sample; invalid, missing, stale, future or replayed samples are unusable. No tick commits unrestricted outputs on an unusable protection sample.

**Coverage:** Detector fixture exists; explicit five-corruption channel matrix is allocated in the parent protocol.

**Design:** [docs/design/INTERFACES.md](../docs/design/INTERFACES.md).

**Existing test:** `test_machine.MachineTests.test_each_detector_observation_bound_and_specific_actuator_action`.

## SIF-04 — M1-REQ-007

Wall-clock liveness shall remain distinct from virtual pause.

**Acceptance:** Nominal lease 2000 ms; tested wall acceptance <=3 s. PING while paused does not increment virtual sequence or physiology.

**Coverage:** direct assertion or named fixture; current result acceptance pending

**Design:** [docs/design/INTERFACES.md](../docs/design/INTERFACES.md).

**Existing test:** `test_machine.MachineTests.test_m5_wall_watchdog_terminal_state_and_observation_remain_separate`.

## SIF-05 — M1-REQ-009

Failed-run evidence shall survive unsuccessful collection.

**Acceptance:** Keep original error identity, available diagnostics and partial records. If extraction fails, retain volumes and usable recovery instructions before any cleanup.

**Coverage:** Direct extraction failure/retention case; other collection phases covered by adjacent suite methods.

**Design:** [docs/design/INTERFACES.md](../docs/design/INTERFACES.md).

**Existing test:** `test_compose_collection.ComposeCollectionTests.test_failed_extraction_keeps_volume_and_recovery_commands`.

## SMOD-01 — REQ-003

Water accounting shall separate patient, circuit, gross UF and substitution.

**Acceptance:** For current physical HD/PRE/POST complete cycles, independent cumulative water residual <=1e-6 mL. Net meter is gross UF minus substitution, not patient weight.

**Coverage:** direct assertion or named fixture; current result acceptance pending

**Design:** [docs/design/MODELS.md](../docs/design/MODELS.md).

**Existing test:** `test_physical.PhysicalProcessTests.test_real_services_and_retained_evidence`.

## SMOD-02 — DYN-REQ-001

Distributed transport shall conserve every tracked solute.

**Acceptance:** Six-species whole-system and dialysate-ledger residuals <=1e-6 mmol; local compartment sums agree with aggregate inventories.

**Coverage:** direct assertion or named fixture; current result acceptance pending

**Design:** [docs/design/MODELS.md](../docs/design/MODELS.md).

**Existing test:** `test_dynamics.DynamicsTests.test_distributed_transit_delay_conservation_and_atomic_rejection`.

## SMOD-03 — PHY-REQ-001

Red cells and proteins shall remain explicitly accounted for.

**Acceptance:** Vascular + circuit + lost red cells/protein equal initial inventory to 1e-6 mL/g; local Hct and Cp must agree with inventories and volumes.

**Coverage:** direct assertion or named fixture; current result acceptance pending

**Design:** [docs/design/MODELS.md](../docs/design/MODELS.md).

**Existing test:** `test_physical.PhysicalTests.test_uf_hemoconcentration_refill_and_rbc_conservation`.

## SMOD-04 — PHY-REQ-001

Needle geometry shall affect hydraulic resistance.

**Acceptance:** With viscosity and length fixed, resistance is proportional to diameter^-4; use internal diameter in mm and explicit SI conversions.

**Coverage:** direct assertion or named fixture; current result acceptance pending

**Design:** [docs/design/MODELS.md](../docs/design/MODELS.md).

**Existing test:** `test_physical.PhysicalTests.test_equations_and_limits`.

## SMOD-05 — DYN-REQ-001

Chamber level changes shall arise from retained liquid/gas inventories.

**Acceptance:** Implicit liquid continuity and (760+P)*Vgas=gas_inventory hold; bounded gas actuation cannot directly reset liquid volume. Isolation freezes storage.

**Coverage:** direct assertion or named fixture; current result acceptance pending

**Design:** [docs/design/MODELS.md](../docs/design/MODELS.md).

**Existing test:** `test_dynamics.DynamicsTests.test_gas_pumps_balancing_and_independent_level_protection`.

## SMOD-06 — DYN-REQ-001

Pump flow, access draw and patient return shall remain distinguishable.

**Acceptance:** Differences equal circuit storage change and membrane/substitution transfers, rather than being forced equal during transients.

**Coverage:** direct assertion or named fixture; current result acceptance pending

**Design:** [docs/design/MODELS.md](../docs/design/MODELS.md).

**Existing test:** `test_physical.PhysicalTests.test_in_process_physical_treatments`.

## SMOD-07 — DYN-REQ-001

Dialysate balance shall include compliant storage and extra UF removal.

**Acceptance:** Storage change equals feed + membrane filtration - drain; independent recorded residual <=1e-5 mL. Valve changeover holds 30 ms, including smaller time steps.

**Coverage:** direct assertion or named fixture; current result acceptance pending

**Design:** [docs/design/MODELS.md](../docs/design/MODELS.md).

**Existing test:** `test_dynamics.DynamicsTests.test_gas_pumps_balancing_and_independent_level_protection`.

## SMOD-08 — DYN-REQ-001

Nonconverged hydraulic steps shall not report nominal flow.

**Acceptance:** Forced solver-iteration exhaustion results in zero outputs and explicit hydraulic_solver limitation, not a successful nominal target.

**Coverage:** direct assertion or named fixture; current result acceptance pending

**Design:** [docs/design/MODELS.md](../docs/design/MODELS.md).

**Existing test:** `test_dynamics.DynamicsTests.test_gas_pumps_balancing_and_independent_level_protection`.

## SMOD-09 — DYN-REQ-001

PRE and POST shall enter different retained blood compartments.

**Acceptance:** PRE enters filter segment 1; POST enters venous chamber. Concentration changes propagate through downstream cells rather than instantaneous whole-circuit mixing.

**Coverage:** Transit/atomic-rejection fixture exists; route allocation also relies on physical three-mode cycles.

**Design:** [docs/design/MODELS.md](../docs/design/MODELS.md).

**Existing test:** `test_dynamics.DynamicsTests.test_distributed_transit_delay_conservation_and_atomic_rejection`.

## SMOD-10 — PHY-REQ-001

Prepared-fluid heating and supply shall respect finite resources.

**Acceptance:** Acid and bicarbonate decrement independently; bicarbonate dissolves at bounded rate; heater power remains 0..configured maximum and thermal balance includes storage and flow.

**Coverage:** direct assertion or named fixture; current result acceptance pending

**Design:** [docs/design/MODELS.md](../docs/design/MODELS.md).

**Existing test:** `test_physical.PhysicalTests.test_equations_and_limits`.

## SMOD-11 — REQ-006

Observable preparation faults shall inhibit unsafe modeled fluid delivery.

**Acceptance:** Observed temperature outside 35..39 C, conductivity outside 12..16 mS/cm, integrity failure or other declared quality hazards constrain delivery before commit. Hidden contamination alone is not an invented observable.

**Coverage:** direct assertion or named fixture; current result acceptance pending

**Design:** [docs/design/MODELS.md](../docs/design/MODELS.md).

**Existing test:** `test_machine.MachineTests.test_quality_detectors_trip_in_their_first_unsafe_observation_cycle`.

## SMOD-12 — DYN-REQ-001

Reference fitting shall keep a separate comparison point.

**Acceptance:** Fit only the 300 mL/min urea point, compare 400 mL/min at stated conditions; 5% relative holdout criterion is an engineering comparison. Report other coefficients as uncalibrated.

**Coverage:** direct assertion or named fixture; current result acceptance pending

**Design:** [docs/design/MODELS.md](../docs/design/MODELS.md).

**Existing test:** `test_dynamics.DynamicsTests.test_reference_holdout_and_discretization_are_reported`.

## SMOD-13 — M3-REQ-001

Rejected patient transactions shall preserve the previous state.

**Acceptance:** Invalid or nonfinite prospective inventory, shape or ordering leaves the accepted patient snapshot unchanged.

**Coverage:** direct assertion or named fixture; current result acceptance pending

**Design:** [docs/design/MODELS.md](../docs/design/MODELS.md).

**Existing test:** `test_dynamics.DynamicsTests.test_distributed_transit_delay_conservation_and_atomic_rejection`.

## SEXP-01 — M7-REQ-003

Experiment pause shall maintain liveness without advancing virtual time.

**Acceptance:** Pause for more than 2 wall seconds leaves sequence/time unchanged; external device STOP aborts without requiring resume or another tick.

**Coverage:** direct assertion or named fixture; current result acceptance pending

**Design:** [docs/design/INTERACTION.md](../docs/design/INTERACTION.md).

**Existing test:** `test_experiments.ExperimentTests.test_external_stop_while_paused_aborts_without_resume_or_another_tick`.

## SEXP-02 — M7-REQ-004

Replay and export shall reject contradictory artifact identity.

**Acceptance:** Reject mismatched run/configuration/build/trajectory identity rather than comparing unrelated records; stream export and retain original failure.

**Coverage:** direct assertion or named fixture; current result acceptance pending

**Design:** [docs/design/INTERACTION.md](../docs/design/INTERACTION.md).

**Existing test:** `test_experiments.ExperimentReviewTests.test_comparison_and_export_reject_every_contradictory_identity`.

## SQA-01 — M8-REQ-006

Current documentation shall remain synchronized with controlled requirements.

**Acceptance:** A final requirement edit makes generated documentation checks fail until regeneration. Missing or duplicate IDs and broken local links fail the gate.

**Coverage:** direct assertion or named fixture; current result acceptance pending

**Design:** [docs/design/INTERFACES.md](../docs/design/INTERFACES.md).

**Existing test:** `test_documentation.DocumentationTests.test_last_requirement_edit_invalidates_generated_candidate`.

## SQA-02 — M8-REQ-006

Current acceptance shall not inherit a historical pass.

**Acceptance:** Generated current test catalogues omit historical evidence outcomes and require explicit applicability/approval records.

**Coverage:** direct assertion or named fixture; current result acceptance pending

**Design:** [docs/design/INTERFACES.md](../docs/design/INTERFACES.md).

**Existing test:** `test_documentation.DocumentationTests.test_historical_pass_does_not_become_current_acceptance`.
