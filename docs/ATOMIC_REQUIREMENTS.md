# Atomic acceptance obligations

Document ID SRS-02; proposed technical baseline, independent approval pending.

Read [parent requirements](REQUIREMENTS.md) first. These obligations clarify registered parent requirements and their
testable decisions without replacing or reducing any parent obligation. They are
generated from [the controlled register](../assurance/current-obligations.json).
Limits characterize the simulator implementation; they are not clinical thresholds.
A test allocation is a coverage argument to review, not a recorded execution result.

The [coverage matrix](testing/COVERAGE.md) makes incomplete cases visible.

## SWF-01 — UI-REQ-002

The guided machine shall complete initial checks before entering preparation.

**Acceptance:** All seven test bits, three safe samples, no alarm and configured test duration are required. Missing integrity retains self_test.

**Coverage:** Complete guided phase/action/guard, endpoint and reset unit matrices now executable; independent approval remains pending.

**Design:** [docs/design/TREATMENT.md](../docs/design/TREATMENT.md).

**Existing test:** `test_audit_closure.AuditClosureTests.test_complete_guided_state_guard_endpoint_and_hazard_mask_matrices`.

## SWF-02 — UI-REQ-002

Priming shall end on delivered flush volume.

**Acceptance:** Below prime_mL retain priming; at or above target with safe guard enter configuration and set primed. The crossing-tick transfer bounds overshoot.

**Coverage:** Complete guided phase/action/guard, endpoint and reset unit matrices now executable; independent approval remains pending.

**Design:** [docs/design/TREATMENT.md](../docs/design/TREATMENT.md).

**Existing test:** `test_audit_closure.AuditClosureTests.test_complete_guided_state_guard_endpoint_and_hazard_mask_matrices`.

## SWF-03 — M5-REQ-002

Isolated priming and cleaning shall not remove or return patient water.

**Acceptance:** Patient draw/return are zero during isolated flush; body and source/waste balances independently remain within 1e-6 mL/mmol.

**Coverage:** direct assertion or named fixture; current result acceptance pending

**Design:** [docs/design/TREATMENT.md](../docs/design/TREATMENT.md).

**Existing test:** `test_guided.GuidedUnitTests.test_in_process_hydraulics_complete_cycle_and_patient_transactions`.

## SWF-04 — UI-REQ-002

Starting treatment shall require priming and an explicit patient connection.

**Acceptance:** Reject START before CONNECT. CONNECT is accepted only from primed configuration; connected alone does not start flow.

**Coverage:** Complete guided phase/action/guard, endpoint and reset unit matrices now executable; independent approval remains pending.

**Design:** [docs/design/TREATMENT.md](../docs/design/TREATMENT.md).

**Existing test:** `test_audit_closure.AuditClosureTests.test_complete_guided_state_guard_endpoint_and_hazard_mask_matrices`.

## SWF-05 — UI-REQ-002

Treatment duration shall count delivered treatment time.

**Acceptance:** A pause does not consume treatment duration; automatic finished occurs at the configured endpoint and preserves accumulated time across resume.

**Coverage:** Complete guided phase/action/guard, endpoint and reset unit matrices now executable; independent approval remains pending.

**Design:** [docs/design/TREATMENT.md](../docs/design/TREATMENT.md).

**Existing test:** `test_audit_closure.AuditClosureTests.test_complete_guided_state_guard_endpoint_and_hazard_mask_matrices`.

## SWF-06 — UI-REQ-002

Blood return shall start only by confirmed request after treatment.

**Acceptance:** RETURN requires finished and patient_connected; completion on returned_mL >= return_target_mL enters disconnecting. UF/substitution are off during return.

**Coverage:** direct assertion or named fixture; current result acceptance pending

**Design:** [docs/design/TREATMENT.md](../docs/design/TREATMENT.md).

**Existing test:** `test_guided.GuidedProcessTests.test_full_guided_cycle_preserves_water_solutes_and_stage_evidence`.

## SWF-07 — UI-REQ-002

Disinfection shall require explicit disconnection and both endpoint conditions.

**Acceptance:** CLEAN is rejected until disconnected. Complete only when configured duration and flush target have both been reached.

**Coverage:** Complete guided phase/action/guard, endpoint and reset unit matrices now executable; independent approval remains pending.

**Design:** [docs/design/TREATMENT.md](../docs/design/TREATMENT.md).

**Existing test:** `test_audit_closure.AuditClosureTests.test_complete_guided_state_guard_endpoint_and_hazard_mask_matrices`.

## SWF-08 — M5-REQ-004

Alarm handling shall not restart circulation.

**Acceptance:** ACK/silence do not clear restrictions. Reset requires recovery with three safe observations; guided restart requires separate RESUME. Terminal stop cannot resume.

**Coverage:** Complete guided phase/action/guard, endpoint and reset unit matrices now executable; independent approval remains pending.

**Design:** [docs/design/TREATMENT.md](../docs/design/TREATMENT.md).

**Existing test:** `test_audit_closure.AuditClosureTests.test_complete_guided_state_guard_endpoint_and_hazard_mask_matrices`.

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

**Coverage:** Actual plant/patient pipe campaign covers every single and pair mask in five active phases. IPC/deployment independence remains a separate gate.

**Design:** [docs/design/INTERFACES.md](../docs/design/INTERFACES.md).

**Existing test:** `test_audit_closure.AuditClosureTests.test_all_single_and_pair_hazards_defeat_hostile_control_in_active_phases`.

## SIF-03 — REQ-004

Invalid protection observations shall constrain outputs before integration.

**Acceptance:** Sequence/time/validity must match the current frozen sample; invalid, missing, stale, future or replayed samples are unusable. No tick commits unrestricted outputs on an unusable protection sample.

**Coverage:** All five freshness faults on both roles exercised on the current guided plant. Wall-clock service loss remains separately tested.

**Design:** [docs/design/INTERFACES.md](../docs/design/INTERFACES.md).

**Existing test:** `test_audit_closure.AuditClosureTests.test_each_freshness_fault_per_role_on_current_guided_model`.

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

## SACC-01 — REQ-001

Device clients shall not gain administrative or patient configuration authority.

**Acceptance:** Reject device-role access to admin and patient paths; retain valid device observation and permitted request access. Native same-UID trust and Compose mount enforcement are assessed separately.

**Coverage:** Named method covers a supporting case; full parent acceptance additionally requires tools/verify_ui_compose.py. No deployment pass inferred from a unit fixture.

**Design:** [docs/design/INTERFACES.md](../docs/design/INTERFACES.md).

**Existing test:** `test_device_sessions.DeviceSessionTests.test_device_roles_and_old_sessions_do_not_mutate_plant`.

## SALM-01 — REQ-005

Alarm acknowledgment and silence shall preserve the active protective mask.

**Acceptance:** ACK and SILENCE change annotation only; a new alarm becomes annunciating; expiration follows virtual time.

**Coverage:** Executable case allocated; execution and reviewed semantic acceptance are recorded separately.

**Design:** [docs/design/TREATMENT.md](../docs/design/TREATMENT.md).

**Existing test:** `test_machine.MachineTests.test_ack_silence_expiration_new_alarm_and_override_never_reset`.

## SALM-02 — REQ-005

Protective reset shall require three safe samples in recovery.

**Acceptance:** Before three safe observations reject RESET. Guided reset enters recovery_ready with no automatic pump restart.

**Coverage:** Executable case allocated; execution and reviewed semantic acceptance are recorded separately.

**Design:** [docs/design/TREATMENT.md](../docs/design/TREATMENT.md).

**Existing test:** `test_audit_closure.AuditClosureTests.test_complete_guided_state_guard_endpoint_and_hazard_mask_matrices`.

## SBUILD-01 — M1-REQ-001

The core build shall produce separate plant, control and protection executables.

**Acceptance:** CMake C++17 build succeeds and records source and executable hashes for all three roles.

**Coverage:** Named method covers a supporting case; full parent acceptance additionally requires tools/verify_compose.py on a Docker-capable host. No deployment pass inferred from a unit fixture.

**Design:** [docs/design/INTERFACES.md](../docs/design/INTERFACES.md).

**Existing test:** `test_m1.M1Processes.test_nominal_conservation_and_build_identity`.

## SBUILD-02 — M1-REQ-001

Deployment shall isolate the patient and runner from the three decision/equipment services.

**Acceptance:** Compose creates five role services with the declared mounts and resource settings and retains their image/configuration identities.

**Coverage:** Named method covers a supporting case; full parent acceptance additionally requires tools/verify_compose.py on a Docker-capable host. No deployment pass inferred from a unit fixture.

**Design:** [docs/design/INTERFACES.md](../docs/design/INTERFACES.md).

**Existing test:** `test_publication.PublicationChecks.test_actual_context_is_explicit_reviewed_subset`.

## SREP-01 — M1-REQ-002

Tick requests shall be contiguous and deterministic on the same build.

**Acceptance:** Same complete configuration and seed yield byte-identical trajectories; duplicate/out-of-order requests reject.

**Coverage:** Named method covers a supporting case; full parent acceptance additionally requires tools/verify_reproducibility.py. No deployment pass inferred from a unit fixture.

**Design:** [docs/design/INTERFACES.md](../docs/design/INTERFACES.md).

**Existing test:** `test_m1.M1Processes.test_same_seed_exact_replay`.

## SREP-02 — M1-REQ-002

Reproducibility shall include independent clean builds.

**Acceptance:** Same-toolchain clean builds produce identical executables; cross-build trajectory numeric comparisons use absolute/relative 1e-9.

**Coverage:** Named method covers a supporting case; full parent acceptance additionally requires tools/verify_reproducibility.py. No deployment pass inferred from a unit fixture.

**Design:** [docs/design/INTERFACES.md](../docs/design/INTERFACES.md).

**Existing test:** `test_m1.M1Processes.test_nominal_conservation_and_build_identity`.

## SLEG-01 — M1-REQ-003

The limited HD model shall conserve water independently of its implementation ledger.

**Acceptance:** Nominal, zero-UF and partial-flow independent Decimal balance error <=1e-8 mL.

**Coverage:** Executable case allocated; execution and reviewed semantic acceptance are recorded separately.

**Design:** [docs/design/MODELS.md](../docs/design/MODELS.md).

**Existing test:** `test_m1.M1Processes.test_zero_and_partial_flow_independent_balance`.

## SLEG-02 — M1-REQ-003

The limited patient ledger shall bound long-run drift.

**Acceptance:** 100000 ordered steps leave cumulative water residual <=1e-8 mL.

**Coverage:** Executable case allocated; execution and reviewed semantic acceptance are recorded separately.

**Design:** [docs/design/MODELS.md](../docs/design/MODELS.md).

**Existing test:** `test_m1.M1Configuration.test_patient_sequence_and_conservation_long_run`.

## SPROT-01 — M1-REQ-004

Synthetic occlusion shall stop the limited HD outputs within one frozen-sample cycle.

**Acceptance:** Tick-5 resistance produces 600 mmHg; at the 250 mmHg synthetic threshold blood/UF become zero and clamp closes within 100 ms.

**Coverage:** Executable case allocated; execution and reviewed semantic acceptance are recorded separately.

**Design:** [docs/design/SAFETY_SECURITY.md](../docs/design/SAFETY_SECURITY.md).

**Existing test:** `test_m1.M1Processes.test_occlusion_bound_and_persistent_conflicting_commands`.

## SPROT-02 — M1-REQ-004

Protection shall reach plant arbitration after control process loss.

**Acceptance:** A killed control process cannot prevent the protective command from latching zero outputs.

**Coverage:** Executable case allocated; execution and reviewed semantic acceptance are recorded separately.

**Design:** [docs/design/SAFETY_SECURITY.md](../docs/design/SAFETY_SECURITY.md).

**Existing test:** `test_m1.M1Processes.test_protection_acts_when_control_is_killed`.

## SPROT-03 — M1-REQ-005

Later permits or conflicting demands shall not clear the limited-model latch.

**Acceptance:** Repeated 300 mL/min demand and PERMIT leave blood/UF zero and clamp closed.

**Coverage:** Executable case allocated; execution and reviewed semantic acceptance are recorded separately.

**Design:** [docs/design/SAFETY_SECURITY.md](../docs/design/SAFETY_SECURITY.md).

**Existing test:** `test_m1.M1Processes.test_occlusion_bound_and_persistent_conflicting_commands`.

## SPROT-04 — M1-REQ-005

Role and duplicate-tick violations shall fail closed.

**Acceptance:** Unauthorized role or repeated decision/tick cannot commit an unprotected output.

**Coverage:** Executable case allocated; execution and reviewed semantic acceptance are recorded separately.

**Design:** [docs/design/SAFETY_SECURITY.md](../docs/design/SAFETY_SECURITY.md).

**Existing test:** `test_m1.M1Processes.test_role_authority_and_duplicate_tick_rejection`.

## SOBS-01 — M1-REQ-006

Protection shall reject unusable sample clocks and validity.

**Acceptance:** Invalid, missing, stale, future and replayed samples trigger the specified stop within one 100 ms interval.

**Coverage:** Executable case allocated; execution and reviewed semantic acceptance are recorded separately.

**Design:** [docs/design/INTERFACES.md](../docs/design/INTERFACES.md).

**Existing test:** `test_m1.M1Processes.test_measurement_invalidity_bound`.

## SOBS-02 — M1-REQ-006

Control sample fault injection shall not mutate the protection observation.

**Acceptance:** Control-only fault leaves independently frozen protection data intact.

**Coverage:** Executable case allocated; execution and reviewed semantic acceptance are recorded separately.

**Design:** [docs/design/INTERFACES.md](../docs/design/INTERFACES.md).

**Existing test:** `test_m1.M1Processes.test_control_sensor_fault_is_separate`.

## SREC-01 — M1-REQ-008

Trajectory recording shall stream 100000 complete ordered records.

**Acceptance:** Written-byte independent hash equals manifest/stream hash and repeated-run hash; runner RSS <=64 MiB under 128 MiB Compose limit.

**Coverage:** Named method covers a supporting case; full parent acceptance additionally requires tools/verify_m1_review.py for two actual Compose runs. No deployment pass inferred from a unit fixture.

**Design:** [docs/design/INTERFACES.md](../docs/design/INTERFACES.md).

**Existing test:** `test_trajectory.TrajectoryTests.test_100000_records_rss_order_repeatability_and_hash`.

## SREC-02 — M1-REQ-008

Interrupted recording shall retain a recoverable complete prefix.

**Acceptance:** After SIGKILL recover only contiguous complete records; discard only an incomplete tail and preserve original bytes.

**Coverage:** Named method covers a supporting case; full parent acceptance additionally requires tools/verify_m1_review.py for two actual Compose runs. No deployment pass inferred from a unit fixture.

**Design:** [docs/design/INTERFACES.md](../docs/design/INTERFACES.md).

**Existing test:** `test_trajectory.TrajectoryTests.test_killed_real_runner_retains_complete_written_prefix`.

## SHYD-01 — M2-REQ-001

The compliant network shall reproduce analytic resistor/RC limiting cases.

**Acceptance:** Analytic step response agrees within declared fixture tolerance and error decreases on step halving.

**Coverage:** Executable case allocated; execution and reviewed semantic acceptance are recorded separately.

**Design:** [docs/design/MODELS.md](../docs/design/MODELS.md).

**Existing test:** `test_circuit.CircuitTests.test_rc_solution_and_step_halving`.

## SHYD-02 — M2-REQ-001

Topology and component changes shall affect actual network flow.

**Acceptance:** Branch resistance, clamp closure and component changes match independent steady-flow expectations.

**Coverage:** Executable case allocated; execution and reviewed semantic acceptance are recorded separately.

**Design:** [docs/design/MODELS.md](../docs/design/MODELS.md).

**Existing test:** `test_circuit.CircuitTests.test_branch_resistance_clamps_and_steady_flow`.

## SHYD-03 — M2-REQ-002

Network storage shall be included in the independent water ledger.

**Acceptance:** Per-tick residual <=1e-8 mL and cumulative <=1e-6 mL with node volumes computed independently.

**Coverage:** Executable case allocated; execution and reviewed semantic acceptance are recorded separately.

**Design:** [docs/design/MODELS.md](../docs/design/MODELS.md).

**Existing test:** `test_circuit.CircuitTests.test_water_balance_independent_decimal_ledger`.

## SSOL-01 — M2-REQ-003

Dialyzer profiles shall give distinct diffusion and convection behavior.

**Acceptance:** Two profiles satisfy the independent clearance formula and equilibrium/zero-flow/zero-membrane cases; gross filtration respects available pressure.

**Coverage:** Executable case allocated; execution and reviewed semantic acceptance are recorded separately.

**Design:** [docs/design/MODELS.md](../docs/design/MODELS.md).

**Existing test:** `test_circuit.CircuitTests.test_transport_oracle_profiles_equilibrium_and_no_flow`.

## SCOUP-01 — M2-REQ-004

Circuit extension shall preserve fault isolation and exact replay.

**Acceptance:** Repeated real-process trajectories agree; occlusion latches by 1000 ms; a lost STEP does not commit circuit storage.

**Coverage:** Named method covers a supporting case; full parent acceptance additionally requires tools/verify_models.py --compose. No deployment pass inferred from a unit fixture.

**Design:** [docs/design/INTERFACES.md](../docs/design/INTERFACES.md).

**Existing test:** `test_circuit.CircuitTests.test_lost_step_reply_preserves_circuit_storage_and_cancels_tick`.

## SBODY-01 — M3-REQ-002

Body exchange shall reproduce an independent analytic transient.

**Acceptance:** Step-halving reduces exchange error; whole-system water and six-solute residuals <=1e-6 mL/mmol.

**Coverage:** Executable case allocated; execution and reviewed semantic acceptance are recorded separately.

**Design:** [docs/design/MODELS.md](../docs/design/MODELS.md).

**Existing test:** `test_compartments.CompartmentNumerics.test_two_compartment_analytic_transient_and_convergence`.

## SBODY-02 — M3-REQ-002

Patient iteration shall retain bounded memory over 100000 steps.

**Acceptance:** Fresh process RSS <64 MiB; cumulative inventories remain finite and conservative.

**Coverage:** Executable case allocated; execution and reviewed semantic acceptance are recorded separately.

**Design:** [docs/design/MODELS.md](../docs/design/MODELS.md).

**Existing test:** `test_compartments.CompartmentNumerics.test_100000_steps_rss_and_mass_ledger`.

## SBODY-03 — M3-REQ-003

Body-water weight shall account separately for external sources and sinks.

**Acceptance:** Independent infusion, generation and excretion cases match volume/species ledgers; weight changes only by modeled body water /1000 kg.

**Coverage:** Executable case allocated; execution and reviewed semantic acceptance are recorded separately.

**Design:** [docs/design/MODELS.md](../docs/design/MODELS.md).

**Existing test:** `test_compartments.CompartmentNumerics.test_external_inputs_generation_outputs_and_weight`.

## SBODY-04 — M3-REQ-003

Synthetic imbalance scenarios shall retain their distinct initial conditions.

**Acceptance:** Baseline/overload/imbalance and profile variants execute with independently checked mass and water.

**Coverage:** Executable case allocated; execution and reviewed semantic acceptance are recorded separately.

**Design:** [docs/design/MODELS.md](../docs/design/MODELS.md).

**Existing test:** `test_compartments.CoupledProcesses.test_synthetic_scenarios_mass_water_and_profile_effect`.

## SCOUP-02 — M3-REQ-004

Patient rejection after plant commit shall abort with evidence of the partial transaction.

**Acceptance:** Actual patient failure cannot be represented as a fully accepted joint tick; recorded build/configuration and partial evidence remain identifiable.

**Coverage:** Named method covers a supporting case; full parent acceptance additionally requires tools/verify_models.py --compose. No deployment pass inferred from a unit fixture.

**Design:** [docs/design/INTERFACES.md](../docs/design/INTERFACES.md).

**Existing test:** `test_compartments.CoupledProcesses.test_repeatability_and_real_patient_failure`.

## SHDF-01 — M4-REQ-001

HD and both substitution routes shall maintain distinct water/solute ledgers.

**Acceptance:** Independent balances <=1e-6 mL/mmol, with gross UF, PRE/POST substitution, storage and patient loss reported separately.

**Coverage:** Executable case allocated; execution and reviewed semantic acceptance are recorded separately.

**Design:** [docs/design/MODELS.md](../docs/design/MODELS.md).

**Existing test:** `test_treatment.TreatmentTests.test_modes_independent_gross_net_water_and_solutes`.

## SPREP-01 — M4-REQ-002

Preparation reservoir and thermal response shall match analytic limiting behavior.

**Acceptance:** Equilibrium/transient and filter pressure losses match the independent fixture oracle.

**Coverage:** Executable case allocated; execution and reviewed semantic acceptance are recorded separately.

**Design:** [docs/design/MODELS.md](../docs/design/MODELS.md).

**Existing test:** `test_treatment.TreatmentTests.test_reservoir_analytic_mixing_temperature_and_filter_hydraulics`.

## SPREP-02 — M4-REQ-002

Reservoir transient discretization error shall decrease with refinement.

**Acceptance:** Halving step size reduces error in the declared first-order mixing/temperature case.

**Coverage:** Executable case allocated; execution and reviewed semantic acceptance are recorded separately.

**Design:** [docs/design/MODELS.md](../docs/design/MODELS.md).

**Existing test:** `test_treatment.TreatmentTests.test_reservoir_first_order_convergence`.

## SQUAL-01 — M4-REQ-003

Observable quality failure shall inhibit prepared fluid outputs before commit.

**Acceptance:** Within one observed cycle, latch UF, substitution and dialysate off despite conflicting control. Blood follows separate hazards.

**Coverage:** Executable case allocated; execution and reviewed semantic acceptance are recorded separately.

**Design:** [docs/design/SAFETY_SECURITY.md](../docs/design/SAFETY_SECURITY.md).

**Existing test:** `test_treatment.TreatmentTests.test_quality_latch_cannot_be_overridden_by_conflicting_control`.

## SQUAL-02 — M4-REQ-003

Unobserved contamination shall not be presented as detected.

**Acceptance:** Hidden contamination without failed modeled integrity indication remains an explicit detection gap.

**Coverage:** Executable case allocated; execution and reviewed semantic acceptance are recorded separately.

**Design:** [docs/design/SAFETY_SECURITY.md](../docs/design/SAFETY_SECURITY.md).

**Existing test:** `test_treatment.TreatmentTests.test_hidden_contamination_is_not_a_protective_sensor`.

## SCOUP-03 — M4-REQ-004

Treatment integration evidence shall identify exact configuration and build.

**Acceptance:** Repeated real modes/fault runs match; stale identity rejects; actual Compose repetitions required separately.

**Coverage:** Named method covers a supporting case; full parent acceptance additionally requires tools/verify_models.py --compose. No deployment pass inferred from a unit fixture.

**Design:** [docs/design/INTERFACES.md](../docs/design/INTERFACES.md).

**Existing test:** `test_treatment.TreatmentTests.test_reproducibility_and_configuration_rejection`.

## SPHASE-01 — M5-REQ-001

Guided phase transitions shall enforce the complete state/action table.

**Acceptance:** All 16 states and 13 actions under nominal/unsafe/terminal guards match SDD and rejected actions preserve state.

**Coverage:** Executable case allocated; execution and reviewed semantic acceptance are recorded separately.

**Design:** [docs/design/TREATMENT.md](../docs/design/TREATMENT.md).

**Existing test:** `test_audit_closure.AuditClosureTests.test_complete_guided_state_guard_endpoint_and_hazard_mask_matrices`.

## SPROT-05 — M5-REQ-003

Aggregate constraints shall be the union of active hazards.

**Acceptance:** All bit masks at all states preserve required blood/fluid restrictions; all singles and pairs defeat hostile demand at the actual plant.

**Coverage:** Executable case allocated; execution and reviewed semantic acceptance are recorded separately.

**Design:** [docs/design/SAFETY_SECURITY.md](../docs/design/SAFETY_SECURITY.md).

**Existing test:** `test_audit_closure.AuditClosureTests.test_all_single_and_pair_hazards_defeat_hostile_control_in_active_phases`.

## SPROT-06 — M5-REQ-003

Current guided observation faults shall act in the same commit cycle.

**Acceptance:** Each of five freshness/validity faults on each role prevents unsafe blood/UF actuation; unusable protection latches measurement alarm.

**Coverage:** Executable case allocated; execution and reviewed semantic acceptance are recorded separately.

**Design:** [docs/design/SAFETY_SECURITY.md](../docs/design/SAFETY_SECURITY.md).

**Existing test:** `test_audit_closure.AuditClosureTests.test_each_freshness_fault_per_role_on_current_guided_model`.

## SDEV-01 — M5-REQ-005

Device requests shall use guarded confirmation and authoritative telemetry.

**Acceptance:** Invalid authority, state, prescription or confirmation does not change effective machine state; STOP remains available.

**Coverage:** Named method covers a supporting case; full parent acceptance additionally requires tools/verify_ui_compose.py for mount denial. No deployment pass inferred from a unit fixture.

**Design:** [docs/design/INTERFACES.md](../docs/design/INTERFACES.md).

**Existing test:** `test_machine.MachineTests.test_device_authority_confirmation_prescription_and_stop`.

## SCOUP-04 — M5-REQ-006

The lifecycle shall execute through real services and conserve isolated flush transfers.

**Acceptance:** Native/Compose HD/PRE/POST workflows, faults and replay retain actual state and independent water/species balances.

**Coverage:** Named method covers a supporting case; full parent acceptance additionally requires tools/verify_models.py --compose. No deployment pass inferred from a unit fixture.

**Design:** [docs/design/INTERFACES.md](../docs/design/INTERFACES.md).

**Existing test:** `test_machine.MachineTests.test_hd_pre_post_lifecycle_flush_and_independent_balances`.

## SLVGL-01 — M6-REQ-001

The device application shall render with actual LVGL.

**Acceptance:** Native/headless actual renderer succeeds with the selected dependency profile; graphical display and Compose require their own execution.

**Coverage:** Named method covers a supporting case; full parent acceptance additionally requires tools/verify_device_ui.py and tools/verify_ui_compose.py. No deployment pass inferred from a unit fixture.

**Design:** [docs/design/INTERACTION.md](../docs/design/INTERACTION.md).

**Existing test:** `test_guided.GuidedUnitTests.test_guided_machine_protocol_and_actual_lvgl_view`.

## SLVGL-02 — M6-REQ-002

Prescriptions shall show units and bounds and require confirmation.

**Acceptance:** HD/PRE/POST requests expose pending/applied/rejected results; the server rejects out-of-range and wrong-state changes.

**Coverage:** Named method covers a supporting case; full parent acceptance additionally requires tools/verify_device_ui.py for real widget paths. No deployment pass inferred from a unit fixture.

**Design:** [docs/design/INTERACTION.md](../docs/design/INTERACTION.md).

**Existing test:** `test_machine.MachineTests.test_device_authority_confirmation_prescription_and_stop`.

## SLVGL-03 — M6-REQ-003

Measured values and trends shall preserve freshness and absence.

**Acceptance:** Timestamped values, invalid/stale/disconnected states and UF/substitution/net counters remain distinct; absent data never becomes a fabricated zero.

**Coverage:** Executable case allocated; execution and reviewed semantic acceptance are recorded separately.

**Design:** [docs/design/INTERACTION.md](../docs/design/INTERACTION.md).

**Existing test:** `test_inspection.InspectionTests.test_nested_values_bounds_missing_samples_and_session_resets`.

## SLVGL-04 — M6-REQ-004

The device alarm interface shall not provide a protective override.

**Acceptance:** ACK/silence/reset remain separate; device roles cannot access admin/patient truth or erase latches with annotation.

**Coverage:** Named method covers a supporting case; full parent acceptance additionally requires tools/verify_ui_compose.py. No deployment pass inferred from a unit fixture.

**Design:** [docs/design/SAFETY_SECURITY.md](../docs/design/SAFETY_SECURITY.md).

**Existing test:** `test_machine.MachineTests.test_ack_silence_expiration_new_alarm_and_override_never_reset`.

## SLVGL-05 — M6-REQ-006

UI evidence shall exercise actual widgets and rendering.

**Acceptance:** Capture real input/RPC/render paths with build/dependency/configuration identities; synthetic unit screenshots do not count as live integration.

**Coverage:** Named method covers a supporting case; full parent acceptance additionally requires tools/verify_device_ui.py and tools/verify_ui_compose.py. No deployment pass inferred from a unit fixture.

**Design:** [docs/design/INTERACTION.md](../docs/design/INTERACTION.md).

**Existing test:** `test_inspection.InspectionTests.test_history_controls_fit_and_receive_pointer_clicks_with_setup_open`.

## SCON-01 — M7-REQ-001

The experiment console shall remain a separate real application.

**Acceptance:** Actual console widgets operate native/headless/Compose services; WSLg execution is separately identified.

**Coverage:** Named method covers a supporting case; full parent acceptance additionally requires tools/verify_console.py and tools/verify_experiments_compose.py. No deployment pass inferred from a unit fixture.

**Design:** [docs/design/INTERACTION.md](../docs/design/INTERACTION.md).

**Existing test:** `test_inspection.InspectionTests.test_recorded_console_is_read_only_and_hold_freezes_samples`.

## SCON-02 — M7-REQ-002

Accepted experiment configuration shall be immutable for the active run.

**Acceptance:** Validated complete patient/circuit/dialyzer/mode/workflow/fault edits change only the next draft.

**Coverage:** Executable case allocated; execution and reviewed semantic acceptance are recorded separately.

**Design:** [docs/design/INTERACTION.md](../docs/design/INTERACTION.md).

**Existing test:** `test_experiments.ExperimentTests.test_pause_liveness_immutable_configuration_exact_replay_compare_export`.

## SCON-03 — M7-REQ-002

Guided experiment presets shall be discoverable and executable under scheduled authority.

**Acceptance:** Catalog includes physical HD/PRE/POST workflows; default is guided HD; launch reaches CLEANED with real services and ordinary device mutations remain scheduled-locked.

**Coverage:** Executable case allocated; execution and reviewed semantic acceptance are recorded separately.

**Design:** [docs/design/INTERACTION.md](../docs/design/INTERACTION.md).

**Existing test:** `test_experiments.ExperimentTests.test_discovered_guided_presets_launch_real_scheduled_services`.

## SCON-04 — M7-REQ-005

Broker administration shall reject invalid credentials and stale identities.

**Acceptance:** Bad token/revision/run/path/size requests reject without unauthorized truth disclosure or configuration mutation.

**Coverage:** Executable case allocated; execution and reviewed semantic acceptance are recorded separately.

**Design:** [docs/design/INTERFACES.md](../docs/design/INTERFACES.md).

**Existing test:** `test_experiments.ExperimentTests.test_authentication_limits_paths_and_compare_reject_tampering`.

## SCON-05 — M7-REQ-006

Interrupted experiments shall retain evidence and start fresh on restart.

**Acceptance:** Failed service/interrupted artifacts remain exportable; subsequent run creates new services and never resumes hidden state.

**Coverage:** Named method covers a supporting case; full parent acceptance additionally requires tools/verify_experiments_compose.py. No deployment pass inferred from a unit fixture.

**Design:** [docs/design/INTERFACES.md](../docs/design/INTERFACES.md).

**Existing test:** `test_experiments.ExperimentTests.test_failed_service_keeps_fault_manifest_and_restart_never_resumes`.

## SSEC-01 — M8-REQ-001

One producer shall not replace the other device endpoint.

**Acceptance:** Actual mount/role spoofing is denied while each permitted producer/reader retains access. Native same-UID limitations remain explicit.

**Coverage:** Named method covers a supporting case; full parent acceptance additionally requires tools/verify_ui_compose.py. No deployment pass inferred from a unit fixture.

**Design:** [docs/design/SAFETY_SECURITY.md](../docs/design/SAFETY_SECURITY.md).

**Existing test:** `test_device_sessions.DeviceSessionTests.test_device_roles_and_old_sessions_do_not_mutate_plant`.

## SSEC-02 — M8-REQ-002

Owner death shall terminate native child services and retain uncertainty.

**Acceptance:** Real broker SIGKILL ends children and preserves partial records; absent final observation is not recorded as observed zero.

**Coverage:** Executable case allocated; execution and reviewed semantic acceptance are recorded separately.

**Design:** [docs/design/SAFETY_SECURITY.md](../docs/design/SAFETY_SECURITY.md).

**Existing test:** `test_security.SecurityTests.test_killed_broker_terminates_actual_children_preserves_unknown_stop`.

## SSEC-03 — M8-REQ-003

JSON input shall reject duplicate, deep and nonfinite structures.

**Acceptance:** Strict parser rejects ambiguous/unbounded input before state mutation.

**Coverage:** Executable case allocated; execution and reviewed semantic acceptance are recorded separately.

**Design:** [docs/design/SAFETY_SECURITY.md](../docs/design/SAFETY_SECURITY.md).

**Existing test:** `test_security.SecurityTests.test_strict_json_rejects_ambiguous_and_unbounded_inputs`.

## SSEC-04 — M8-REQ-003

Slow input clients shall not extend frame deadlines or liveness.

**Acceptance:** Four slow DX1 clients are bounded and recovery remains possible; partial device requests cannot maintain plant lease.

**Coverage:** Executable case allocated; execution and reviewed semantic acceptance are recorded separately.

**Design:** [docs/design/SAFETY_SECURITY.md](../docs/design/SAFETY_SECURITY.md).

**Existing test:** `test_security.SecurityTests.test_broker_four_slow_clients_are_bounded_and_recover`.

## SSUP-01 — M8-REQ-004

Selected dependencies shall have immutable pins and reviewed license notices.

**Acceptance:** Changed pin/notice/action is rejected; preferred application license policy and all consumer notices remain enforced.

**Coverage:** Named method covers a supporting case; full parent acceptance additionally requires tools/dependency_report.py with actual images. No deployment pass inferred from a unit fixture.

**Design:** [docs/design/SAFETY_SECURITY.md](../docs/design/SAFETY_SECURITY.md).

**Existing test:** `test_dependencies.DependencyTests.test_inventory_rejects_changed_pins_notices_and_ci_actions`.

## SSUP-02 — M8-REQ-004

SBOM identity shall derive from actual binaries and runtime files.

**Acceptance:** Reproducible SBOM lists actual native/image hashes; stale or mismatched image runtime files reject.

**Coverage:** Named method covers a supporting case; full parent acceptance additionally requires tools/dependency_report.py with actual images. No deployment pass inferred from a unit fixture.

**Design:** [docs/design/SAFETY_SECURITY.md](../docs/design/SAFETY_SECURITY.md).

**Existing test:** `test_dependencies.DependencyTests.test_container_sbom_uses_actual_image_binary_and_runtime_identities`.

## SSUP-03 — M8-REQ-005

Analysis reports shall distinguish findings from unavailable coverage.

**Acceptance:** Static/advisory commands, timestamps, complete pagination and errors are retained; unavailable analysis is BLOCKED and never a clean scan.

**Coverage:** Named method covers a supporting case; full parent acceptance additionally requires tools/security_scan.py --advisories with fresh actual inventory. No deployment pass inferred from a unit fixture.

**Design:** [docs/design/SAFETY_SECURITY.md](../docs/design/SAFETY_SECURITY.md).

**Existing test:** `test_dependencies.DependencyTests.test_advisory_errors_and_repeated_pages_are_blocked`.

## SSUP-04 — M8-REQ-005

Advisory matches shall remain open until disposition is supported.

**Acceptance:** Retain every matching page and version/scope fact; a lack of runtime invocation alone does not prove not-affected or accepted residual risk.

**Coverage:** Named method covers a supporting case; full parent acceptance additionally requires tools/security_scan.py --advisories with fresh actual inventory. No deployment pass inferred from a unit fixture.

**Design:** [docs/design/SAFETY_SECURITY.md](../docs/design/SAFETY_SECURITY.md).

**Existing test:** `test_dependencies.DependencyTests.test_advisory_pagination_preserves_all_findings`.

## SINT-01 — M9-REQ-001

Integration shall cover every supported patient/modality/dialyzer combination.

**Acceptance:** 18 configurations run twice natively and twice in Compose with complete lifecycle, exact replay and water/species residual <=1e-6.

**Coverage:** Named method covers a supporting case; full parent acceptance additionally requires tools/verify_integrated.py; this fixture is not the 72-run campaign. No deployment pass inferred from a unit fixture.

**Design:** [docs/design/MODELS.md](../docs/design/MODELS.md).

**Existing test:** `test_integration.IntegrationTests.test_sustained_fixture_reaches_deliverable_gross_uf_without_alarm`.

## SINT-02 — M9-REQ-002

Sustained HDF shall exercise treatment rather than idle ticks.

**Acceptance:** Two native and two Compose 100000-tick cases exceed 99000 treatment ticks and 100000 mL gross UF; RSS <=64 MiB and no OOM under 128 MiB.

**Coverage:** Named method covers a supporting case; full parent acceptance additionally requires tools/verify_integrated.py and tools/audit_campaign.py --mode resource. No deployment pass inferred from a unit fixture.

**Design:** [docs/design/MODELS.md](../docs/design/MODELS.md).

**Existing test:** `test_integration.IntegrationTests.test_sustained_fixture_reaches_deliverable_gross_uf_without_alarm`.

## SINT-03 — M9-REQ-002

Distributed-model resource evidence shall identify the larger record and actual solver path.

**Acceptance:** A fresh native coupled plant/patient/writer campaign streams 100000 full distributed records with RSS <=64 MiB; actual Compose cgroup acceptance remains separate.

**Coverage:** Named method covers a supporting case; full parent acceptance additionally requires tools/verify_integrated.py and tools/audit_campaign.py --mode resource. No deployment pass inferred from a unit fixture.

**Design:** [docs/design/MODELS.md](../docs/design/MODELS.md).

**Existing test:** `test_dynamics.DynamicsTests.test_distributed_transit_delay_conservation_and_atomic_rejection`.

## SINT-04 — M9-REQ-003

Simultaneous device and console use shall preserve STOP and session authority.

**Acceptance:** Widget pause/replay/STOP/cancel/state/epoch/isolation tests execute headless and on a supported graphical target; device STOP during virtual pause needs no RESUME.

**Coverage:** Named method covers a supporting case; full parent acceptance additionally requires tools/verify_console.py and tools/verify_experiments_compose.py; WSLg assessed separately. No deployment pass inferred from a unit fixture.

**Design:** [docs/design/INTERACTION.md](../docs/design/INTERACTION.md).

**Existing test:** `test_experiments.ExperimentTests.test_external_stop_while_paused_aborts_without_resume_or_another_tick`.

## SINT-05 — M9-REQ-004

The source package shall reproduce its allowlist and execute after extraction.

**Acceptance:** Two allowlisted archives match; extracted sources build/test/render without relying on unlisted checkout files; packaging failure evidence is retained.

**Coverage:** Named method covers a supporting case; full parent acceptance additionally requires tools/verify_package.py. No deployment pass inferred from a unit fixture.

**Design:** [docs/design/INTERFACES.md](../docs/design/INTERFACES.md).

**Existing test:** `test_integration.IntegrationTests.test_package_without_git_retains_actual_failed_packaging_evidence`.

## SINT-06 — M9-REQ-005

The supported evidence package shall retain actual results and open obligations.

**Acceptance:** Exact CI evidence bytes recover independently; source/config identities and model limitations remain visible; release obligations cannot be relabeled passing.

**Coverage:** Executable case allocated; execution and reviewed semantic acceptance are recorded separately.

**Design:** [docs/design/INTERFACES.md](../docs/design/INTERFACES.md).

**Existing test:** `test_ci.CITests.test_exact_byte_retention_includes_every_sbom_and_platform_file`.

## SVIS-01 — UI-REQ-001

Inspection shall show bounded circuit histories with correct authority.

**Acceptance:** Selectable quantities have time/units and bounded retention; missing/stale values remain distinguishable; recorded console cannot submit commands.

**Coverage:** Executable case allocated; execution and reviewed semantic acceptance are recorded separately.

**Design:** [docs/design/INTERACTION.md](../docs/design/INTERACTION.md).

**Existing test:** `test_inspection.InspectionTests.test_recorded_console_is_read_only_and_hold_freezes_samples`.

## SWIRE-01 — M5-REQ-005

C++ and Python current device decoders shall share numeric bounds.

**Acceptance:** For MACHINE5/8 and OBS5/8/9/10 accept each boundary and reject below/above, nonfinite, missing and surplus values in both actual decoders.

**Coverage:** Field-by-field numeric and arity campaign; physical plausibility and clock matching remain semantic checks.

**Design:** [docs/design/WIRE_PROTOCOL.md](../docs/design/WIRE_PROTOCOL.md).

**Existing test:** `test_document_contracts.WireWitnessTests.test_cpp_python_reject_every_documented_numeric_boundary_violation`.

## SWIRE-02 — DYN-REQ-001

Accepted initial dialysate volume shall be usable by plant and patient initialization.

**Acceptance:** Current dynamic machine domain is 50..1000 mL inclusive; Python outer validator and C++ plant agree, and both endpoints initialize the patient successfully.

**Coverage:** Real C++ initialization and Python patient; no upper-domain expansion implied.

**Design:** [docs/design/WIRE_PROTOCOL.md](../docs/design/WIRE_PROTOCOL.md).

**Existing test:** `test_audit_closure.AuditClosureTests.test_dynamic_initial_volume_bounds_match_actual_plant_and_patient`.

## MIX-OBL-001 — MIX-REQ-001

Each source line shall retain its configured internal volume and initial air, water or concentrate occupancy up to the mixing junction.

**Acceptance:** Exercise dry, wetted and residual-liquid starts; downstream arrival follows displaced volume and conserves inventories. Bounds fixed in STP-MIX-01.

**Coverage:** Implemented synthetic candidate. Full preparation suite also covers three real Plant/patient cycles, all occupancy starts and eight-hour depletion. Empirical/independent acceptance remains open.

**Design:** [docs/design/PREPARATION.md](../docs/design/PREPARATION.md).

**Existing test:** `test_preparation.PreparationTests.test_line_air_water_and_concentrate_displacement`.

## MIX-OBL-002 — MIX-REQ-002

Acid and bicarbonate shall have distinct metering pumps with command and actual transfer represented separately.

**Acceptance:** Exercise zero command, pressure load, air aspiration and actuator saturation; actual liquid delivery follows the declared pump law, not commanded displacement alone. Bounds fixed in STP-MIX-01.

**Coverage:** Implemented synthetic candidate. Full preparation suite also covers three real Plant/patient cycles, all occupancy starts and eight-hour depletion. Empirical/independent acceptance remains open.

**Design:** [docs/design/PREPARATION.md](../docs/design/PREPARATION.md).

**Existing test:** `test_preparation.PreparationTests.test_distinct_pump_displacement_pressure_and_air_efficiency`.

## MIX-OBL-003 — MIX-REQ-003

The cartridge shall separately account for liquid volume, gas inventory, solid bicarbonate and dissolved bicarbonate.

**Acceptance:** Fill and withdraw from known initial inventories; storage changes match all boundary transfers and inventories remain nonnegative. Bounds fixed in STP-MIX-01.

**Coverage:** Implemented synthetic candidate. Full preparation suite also covers three real Plant/patient cycles, all occupancy starts and eight-hour depletion. Empirical/independent acceptance remains open.

**Design:** [docs/design/PREPARATION.md](../docs/design/PREPARATION.md).

**Existing test:** `test_preparation.PreparationTests.test_cartridge_liquid_gas_and_solute_storage`.

## MIX-OBL-004 — MIX-REQ-004

Cartridge pressure shall respond to gas compression, liquid transfer and declared vent paths.

**Acceptance:** Block vent, restrict inlet and increase withdrawal; pressure follows the declared law and limit violations inhibit the conflicting actuator before the allocated deadline. Bounds fixed in STP-MIX-01.

**Coverage:** Implemented synthetic candidate. Full preparation suite also covers three real Plant/patient cycles, all occupancy starts and eight-hour depletion. Empirical/independent acceptance remains open.

**Design:** [docs/design/PREPARATION.md](../docs/design/PREPARATION.md).

**Existing test:** `test_preparation.PreparationTests.test_pressure_stop_and_bounded_startup_failures`.

## MIX-OBL-005 — MIX-REQ-005

Dissolution shall depend on the declared saturation relation, available solid and finite dissolution kinetics.

**Acceptance:** At adequate residence time approach saturation; under dissolution-limited withdrawal remain below saturation despite remaining solid. Bounds fixed in STP-MIX-01.

**Coverage:** Implemented synthetic candidate. Full preparation suite also covers three real Plant/patient cycles, all occupancy starts and eight-hour depletion. Empirical/independent acceptance remains open.

**Design:** [docs/design/PREPARATION.md](../docs/design/PREPARATION.md).

**Existing test:** `test_preparation.PreparationTests.test_saturation_and_finite_dissolution_with_solid_remaining`.

## MIX-OBL-006 — MIX-REQ-006

Solid exhaustion shall not erase remaining dissolved bicarbonate.

**Acceptance:** Exhaust solid and continue water throughput; dissolved inventory washes out conservatively rather than disappearing or remaining indefinitely constant. Bounds fixed in STP-MIX-01.

**Coverage:** Implemented synthetic candidate. Full preparation suite also covers three real Plant/patient cycles, all occupancy starts and eight-hour depletion. Empirical/independent acceptance remains open.

**Design:** [docs/design/PREPARATION.md](../docs/design/PREPARATION.md).

**Existing test:** `test_preparation.PreparationTests.test_solid_exhaustion_preserves_dissolved_washout`.

## MIX-OBL-007 — MIX-REQ-007

Acid concentration shall be a configurable source property, distinct from remaining bag volume.

**Acceptance:** Apply nominal, diluted and exhausted-source cases; concentration and delivered mass change consistently, including configured air ingress after depletion. Bounds fixed in STP-MIX-01.

**Coverage:** Implemented synthetic candidate. Full preparation suite also covers three real Plant/patient cycles, all occupancy starts and eight-hour depletion. Empirical/independent acceptance remains open.

**Design:** [docs/design/PREPARATION.md](../docs/design/PREPARATION.md).

**Existing test:** `test_preparation.PreparationTests.test_acid_concentration_step_and_bag_depletion`.

## MIX-OBL-008 — MIX-REQ-008

Downstream mixing shall conserve species and liquid storage and represent declared transport delays.

**Acceptance:** Compare a well-mixed tank with its analytic step response and transport with volume/flow delay; verify independent inventory residuals. Bounds fixed in STP-MIX-01.

**Coverage:** Implemented synthetic candidate. Full preparation suite also covers three real Plant/patient cycles, all occupancy starts and eight-hour depletion. Empirical/independent acceptance remains open.

**Design:** [docs/design/PREPARATION.md](../docs/design/PREPARATION.md).

**Existing test:** `test_preparation.PreparationTests.test_mixed_tank_matches_independent_exponential`.

## MIX-OBL-009 — MIX-REQ-009

Control shall use simulated sensor outputs with timestamps, temperature compensation, latency and validity rather than hidden source inventory.

**Acceptance:** Inject delayed, stale, invalid and air-exposed measurements; invalid signals cannot authorize readiness. Changing hidden inventory alone cannot directly change a control decision with identical sensor history. Bounds fixed in STP-MIX-01.

**Coverage:** Implemented synthetic candidate. Full preparation suite also covers three real Plant/patient cycles, all occupancy starts and eight-hour depletion. Empirical/independent acceptance remains open.

**Design:** [docs/design/PREPARATION.md](../docs/design/PREPARATION.md).

**Existing test:** `test_preparation.PreparationTests.test_delayed_stale_invalid_sensors_and_control_input_boundary`.

## MIX-OBL-010 — MIX-REQ-010

Each metering command shall combine declared feedforward with bounded PI correction and defined anti-windup/invalid-measurement behavior.

**Acceptance:** Apply flow/concentration steps, saturation and invalidity; commands remain bounded, integrator behavior matches the specified policy and recovery meets prospective response criteria. Bounds fixed in STP-MIX-01.

**Coverage:** Implemented synthetic candidate. Full preparation suite also covers three real Plant/patient cycles, all occupancy starts and eight-hour depletion. Empirical/independent acceptance remains open.

**Design:** [docs/design/PREPARATION.md](../docs/design/PREPARATION.md).

**Existing test:** `test_preparation.PreparationTests.test_pi_saturation_antiwindup_and_invalid_freeze`.

## MIX-OBL-011 — MIX-REQ-011

Composition qualification shall include intermediate observations and ratio checks rather than final conductivity alone.

**Acceptance:** Construct compensating acid/bicarbonate errors with similar final conductivity; documented intermediate checks detect the observable cases and remaining detection gaps are reported. Bounds fixed in STP-MIX-01.

**Coverage:** Implemented synthetic candidate. Full preparation suite also covers three real Plant/patient cycles, all occupancy starts and eight-hour depletion. Empirical/independent acceptance remains open.

**Design:** [docs/design/PREPARATION.md](../docs/design/PREPARATION.md).

**Existing test:** `test_preparation.PreparationTests.test_compensating_errors_and_continuous_dwell`.

## MIX-OBL-012 — MIX-REQ-012

Acid and bicarbonate startup sequences shall progress independently with observable guards and bounded failure timeouts.

**Acceptance:** Hold each prerequisite false in turn; reject premature dosing qualification and enter the declared failure response on timeout. Bounds fixed in STP-MIX-01.

**Coverage:** Implemented synthetic candidate. Full preparation suite also covers three real Plant/patient cycles, all occupancy starts and eight-hour depletion. Empirical/independent acceptance remains open.

**Design:** [docs/design/PREPARATION.md](../docs/design/PREPARATION.md).

**Existing test:** `test_preparation.PreparationTests.test_pressure_stop_and_bounded_startup_failures`.

## MIX-OBL-013 — MIX-REQ-013

The preparation supervisor shall divert unqualified fluid to waste and prevent its delivery to the dialyzer/substitution paths.

**Acceptance:** Challenge every startup phase, each invalid guard and loss of qualification; verify actual routed volumes, not just displayed state. Bounds fixed in STP-MIX-01.

**Coverage:** Implemented synthetic candidate. Full preparation suite also covers three real Plant/patient cycles, all occupancy starts and eight-hour depletion. Empirical/independent acceptance remains open.

**Design:** [docs/design/PREPARATION.md](../docs/design/PREPARATION.md).

**Existing test:** `test_preparation.PreparationTests.test_final_authority_blocks_unqualified_fluid_despite_forged_permits`.

## MIX-OBL-014 — MIX-REQ-014

Readiness shall require valid liquid-presence evidence, acceptable pressure/composition and continuous stability for a configured dwell interval.

**Acceptance:** Test just below/at/above the dwell boundary and an intervening invalid sample; interruptions reset qualification and a single valid sample cannot authorize delivery. Bounds fixed in STP-MIX-01.

**Coverage:** Implemented synthetic candidate. Full preparation suite also covers three real Plant/patient cycles, all occupancy starts and eight-hour depletion. Empirical/independent acceptance remains open.

**Design:** [docs/design/PREPARATION.md](../docs/design/PREPARATION.md).

**Existing test:** `test_preparation.PreparationTests.test_compensating_errors_and_continuous_dwell`.

## MIX-OBL-015 — MIX-REQ-015

The model shall provide separate boundary ledgers for source supply, stored liquid/species, gas exchange, waste and usable output.

**Acceptance:** Independently reconstruct balances across startup, zero flow, partial steps and exhaustion; refinements of timestep and transport discretization satisfy predeclared error budgets. Bounds fixed in STP-MIX-01.

**Coverage:** Implemented synthetic candidate. Full preparation suite also covers three real Plant/patient cycles, all occupancy starts and eight-hour depletion. Empirical/independent acceptance remains open.

**Design:** [docs/design/PREPARATION.md](../docs/design/PREPARATION.md).

**Existing test:** `test_preparation.PreparationTests.test_time_refinement_against_predeclared_budget`.

## MIX-OBL-016 — MIX-REQ-016

Preparation evidence shall identify requirements, implementation revision, parameters, test oracle and execution outcome.

**Acceptance:** Reproduce a fixed scenario and verify complete trace in both directions; changed source/configuration invalidates prior applicability. Bounds fixed in STP-MIX-01.

**Coverage:** Implemented synthetic candidate. Full preparation suite also covers three real Plant/patient cycles, all occupancy starts and eight-hour depletion. Empirical/independent acceptance remains open.

**Design:** [docs/design/PREPARATION.md](../docs/design/PREPARATION.md).

**Existing test:** `test_preparation.PreparationTests.test_evidence_identity_changes_with_source_and_configuration`.

## SYN-OBL-001 — SYN-REQ-001

Treatment home shall show a large simplified external dialyzer and extracorporeal circuit with directional flow and explicit HD / HDF PRE / HDF POST routing. Roller pumps, chamber detail, containers and full plumbing shall be available in dedicated Blood circuit and Hydraulics tabs. Render each mode and assert active branches and view allocation.

**Acceptance:** Proposed engineering criteria recorded before implementation in the design. No independent acceptance is inferred from execution.

**Coverage:** Synthetic telemetry and real LVGL rendering/pointer checks; Unix IPC and physical touch hardware are separate gates.

**Design:** [docs/design/ANIMATED_SYNOPTIC.md](../docs/design/ANIMATED_SYNOPTIC.md).

**Existing test:** `test_synoptic.SynopticTests.test_actual_lvgl_modes_responsive_touch_and_stale`.

## SYN-OBL-002 — SYN-REQ-002

Motion shall use current valid observed/model telemetry, never prescribed flow. Zero flow freezes phase; stale/invalid telemetry freezes motion and displays its status, without portraying unknown as zero. Changing flow preserves phase. Unit checks exercise zero, restart, rate changes and loss/recovery of freshness.

**Acceptance:** Proposed engineering criteria recorded before implementation in the design. No independent acceptance is inferred from execution.

**Coverage:** Synthetic telemetry and real LVGL rendering/pointer checks; Unix IPC and physical touch hardware are separate gates.

**Design:** [docs/design/ANIMATED_SYNOPTIC.md](../docs/design/ANIMATED_SYNOPTIC.md).

**Existing test:** `test_synoptic.SynopticTests.test_motion_freshness_routes_and_inventory`.

## SYN-OBL-003 — SYN-REQ-003

Pump activity and fluid passage shall be distinguished. Concentrate drive and delivered liquid require separate versioned observations; older observations show unavailable fields. No mechanical RPM shall be claimed. Test C++/Python round trips and a dry-line fixture.

**Acceptance:** Proposed engineering criteria recorded before implementation in the design. No independent acceptance is inferred from execution.

**Coverage:** Synthetic telemetry and real LVGL rendering/pointer checks; Unix IPC and physical touch hardware are separate gates.

**Design:** [docs/design/ANIMATED_SYNOPTIC.md](../docs/design/ANIMATED_SYNOPTIC.md).

**Existing test:** `test_document_contracts.WireWitnessTests.test_concentrate_drive_is_distinct_from_dry_liquid_and_legacy_is_absent`.

## SYN-OBL-004 — SYN-REQ-004

Dialysate traversal, bypass and unknown route shall be distinguished with labels and valve/path geometry. Motion in a bypass shall not imply membrane traversal. Test bypass with positive feed and zero/unknown feed.

**Acceptance:** Proposed engineering criteria recorded before implementation in the design. No independent acceptance is inferred from execution.

**Coverage:** Synthetic telemetry and real LVGL rendering/pointer checks; Unix IPC and physical touch hardware are separate gates.

**Design:** [docs/design/ANIMATED_SYNOPTIC.md](../docs/design/ANIMATED_SYNOPTIC.md).

**Existing test:** `test_synoptic.SynopticTests.test_actual_lvgl_modes_responsive_touch_and_stale`.

## SYN-OBL-005 — SYN-REQ-005

Phase progress, phase/session time, net UF and substitution totals versus explicitly labelled current-prescription goals shall remain visible on home. Totals come from authoritative meters and survive pause/resume; no UI integration or invented target history. Test paused totals, HD, changed prescriptions and unavailable observations.

**Acceptance:** Proposed engineering criteria recorded before implementation in the design. No independent acceptance is inferred from execution.

**Coverage:** Synthetic telemetry and real LVGL rendering/pointer checks; Unix IPC and physical touch hardware are separate gates.

**Design:** [docs/design/ANIMATED_SYNOPTIC.md](../docs/design/ANIMATED_SYNOPTIC.md).

**Existing test:** `test_synoptic.SynopticTests.test_actual_lvgl_modes_responsive_touch_and_stale`.

## SYN-OBL-006 — SYN-REQ-006

Filled icons shall accompany text on navigation and actions. Guided controls shall have at least 48 logical pixels height; STOP shall remain visible outside scrollable content. Reflow shall support 800x890, 1100x890 and 1440x1000 without scaling hit targets. Test bounds, non-overlap and real LVGL rendering.

**Acceptance:** Proposed engineering criteria recorded before implementation in the design. No independent acceptance is inferred from execution.

**Coverage:** Synthetic telemetry and real LVGL rendering/pointer checks; Unix IPC and physical touch hardware are separate gates.

**Design:** [docs/design/ANIMATED_SYNOPTIC.md](../docs/design/ANIMATED_SYNOPTIC.md).

**Existing test:** `test_synoptic.SynopticTests.test_actual_lvgl_modes_responsive_touch_and_stale`.

## SYN-OBL-007 — SYN-REQ-007

Chamber fractions shall use measured fractions. Container bars shall be explicitly relative to first observed session inventory, with absolute quantities/units; missing baselines and unavailable telemetry shall not show fabricated capacity. Session changes reset presentation history. Test inventory depletion, stale data and reset.

**Acceptance:** Proposed engineering criteria recorded before implementation in the design. No independent acceptance is inferred from execution.

**Coverage:** Synthetic telemetry and real LVGL rendering/pointer checks; Unix IPC and physical touch hardware are separate gates.

**Design:** [docs/design/ANIMATED_SYNOPTIC.md](../docs/design/ANIMATED_SYNOPTIC.md).

**Existing test:** `test_synoptic.SynopticTests.test_motion_freshness_routes_and_inventory`.

## SYN-OBL-008 — SYN-REQ-008

A reduced-motion toggle shall freeze decorative motion without hiding numerical values, route, status or progress. Motion limits shall be visible and documented. Verify freeze and continued value updates.

**Acceptance:** Proposed engineering criteria recorded before implementation in the design. No independent acceptance is inferred from execution.

**Coverage:** Synthetic telemetry and real LVGL rendering/pointer checks; Unix IPC and physical touch hardware are separate gates.

**Design:** [docs/design/ANIMATED_SYNOPTIC.md](../docs/design/ANIMATED_SYNOPTIC.md).

**Existing test:** `test_synoptic.SynopticTests.test_actual_lvgl_modes_responsive_touch_and_stale`.

## SYN-OBL-009 — SYN-REQ-009

Dialysate outlet and bypass shall remain outside the venous chamber and lead to effluent. POST substitution shall enter a dedicated venous-chamber inlet; PRE enters before the filter. Blood enters above and leaves below. Non-joining crossings shall have visible clearance.

**Acceptance:** Exact intended connector endpoints and no dialysate intersection with the venous-chamber rectangle in actual HD/PRE/POST, bypass and stale renders at all three test sizes. A separate POST tracer check uses an independent scalar mixing oracle with 1e-12 mmol/L tolerance and existing 1e-6 mmol residual limit. Proposed engineering criteria; no bubble-capture or independent usability acceptance.

**Coverage:** Actual drawn segment endpoints and chamber exclusion in all fixture sizes, modes, bypass and stale states; additional POST tracer regression in test_synoptic. No bubble-trap validation.

**Design:** [docs/design/ANIMATED_SYNOPTIC.md](../docs/design/ANIMATED_SYNOPTIC.md).

**Existing test:** `test_synoptic.SynopticTests.test_actual_lvgl_modes_responsive_touch_and_stale`.

## SYN-OBL-010 — SYN-REQ-010

Home shall prioritize the filter and extracorporeal flow with a simplified overview, animated fluid-direction cues and measured acid/bicarbonate liquid, dialysate feed, drain, membrane UF and substitution quantities in mL/min. Mechanical roller motion, tanks and full valve plumbing shall be confined to the Blood circuit and Hydraulics tabs. PRE/POST destination, bypass, zero/unknown flow, freshness and reduced motion remain explicit. Test distinct render modes, actual tab events, source-to-value mapping and simplified topology at all three fixture sizes.

**Acceptance:** Proposed engineering criteria recorded before implementation in the design. No independent acceptance is inferred from execution.

**Coverage:** Synthetic telemetry and real LVGL rendering/pointer checks; Unix IPC and physical touch hardware are separate gates.

**Design:** [docs/design/ANIMATED_SYNOPTIC.md](../docs/design/ANIMATED_SYNOPTIC.md).

**Existing test:** `test_synoptic.SynopticTests.test_actual_lvgl_modes_responsive_touch_and_stale`.

## WEB-OBL-001 — WEB-REQ-001

Run production C++ Plant, control/protection decisions and existing Python patient/physical coupling locally using WebAssembly and Pyodide. HD/PRE/POST must reach treatment with finite results and conserved water/solute inventories; no replacement physical equations or prerecorded telemetry.

**Acceptance:** Criteria declared before execution; native/Wasm comparison and real Chromium UI gates.

**Coverage:** Selected synthetic full cycles and browser interactions; no process isolation, independent usability approval, long-duration/mobile qualification or global numerical closure.

**Design:** [docs/design/BROWSER_RUNTIME.md](../docs/design/BROWSER_RUNTIME.md).

**Existing test:** `test_browser.BrowserRuntimeTests.test_full_wasm_portability`.

## WEB-OBL-002 — WEB-REQ-002

Render existing LVGL guided views in a browser canvas with touch/pointer input and working lifecycle actions, prescription, STOP, detail tabs and reduced motion. Keep simulation time independent of animation frame rate.

**Acceptance:** Criteria declared before execution; native/Wasm comparison and real Chromium UI gates.

**Coverage:** Selected synthetic full cycles and browser interactions; no process isolation, independent usability approval, long-duration/mobile qualification or global numerical closure.

**Design:** [docs/design/BROWSER_RUNTIME.md](../docs/design/BROWSER_RUNTIME.md).

**Existing test:** `test_browser.BrowserRuntimeTests.test_real_browser_ui`.

## WEB-OBL-003 — WEB-REQ-003

Compare the same deterministic scenarios/commands and initial conditions in native and WebAssembly execution. Discrete stages/alarms must match exactly; finite numeric outputs use abs(a-b) <= 1e-8 + 1e-9*max(abs(a),abs(b)), in each field's documented units. Water and solute conservation retain existing 1e-6 mL/mmol bounds. These are proposed portability budgets, not global numerical accuracy approval.

**Acceptance:** Criteria declared before execution; native/Wasm comparison and real Chromium UI gates.

**Coverage:** Selected synthetic full cycles and browser interactions; no process isolation, independent usability approval, long-duration/mobile qualification or global numerical closure.

**Design:** [docs/design/BROWSER_RUNTIME.md](../docs/design/BROWSER_RUNTIME.md).

**Existing test:** `test_browser.BrowserRuntimeTests.test_full_wasm_portability`.

## WEB-OBL-004 — WEB-REQ-004

Serve static assets only; computation and patient state stay in the browser. Pause when hidden, do not catch up elapsed wall time, prevent overlapping ticks; stop advancing after runtime failure and report unavailable state. Reset must discard queued actions and old patient state.

**Acceptance:** Criteria declared before execution; native/Wasm comparison and real Chromium UI gates.

**Coverage:** Selected synthetic full cycles and browser interactions; no process isolation, independent usability approval, long-duration/mobile qualification or global numerical closure.

**Design:** [docs/design/BROWSER_RUNTIME.md](../docs/design/BROWSER_RUNTIME.md).

**Existing test:** `test_browser.BrowserRuntimeTests.test_real_browser_ui`.

## WEB-OBL-005 — WEB-REQ-005

Pin toolchain/runtime dependencies, preserve source/configuration identifiers, build instructions and native/Wasm comparison results. Published build must identify its source and dependency artifacts.

**Acceptance:** Criteria declared before execution; native/Wasm comparison and real Chromium UI gates.

**Coverage:** Selected synthetic full cycles and browser interactions; no process isolation, independent usability approval, long-duration/mobile qualification or global numerical closure.

**Design:** [docs/design/BROWSER_RUNTIME.md](../docs/design/BROWSER_RUNTIME.md).

**Existing test:** `test_browser.BrowserRuntimeTests.test_full_wasm_portability`.

## WEB-OBL-006 — WEB-REQ-006

Delayed manual PRIME must remain usable beyond the batch horizon in an explicitly interactive session.

**Acceptance:** HD/PRE/POST wait 2400 ticks then confirmed PRIME and complete lifecycle, zero alarms, conservation and native/Wasm budgets retained; batch limit and STOP retained.

**Coverage:** Finite synthetic delayed-start regression; independent review, arbitrary duration and cross-browser/device qualification remain open.

**Design:** [docs/design/BROWSER_RUNTIME.md](../docs/design/BROWSER_RUNTIME.md).

**Existing test:** `test_browser.BrowserRuntimeTests.test_delayed_manual_prime`.
