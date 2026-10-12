# Current obligation–design–test allocation

Document ID STM-01; generated from the atomic acceptance register.

All rows are proposed and await independent acceptance. Method existence is checked
against the actual Python test AST. The checker cannot decide semantic completeness.
Read [current execution applicability](STATUS.md) separately. Additional cases and
approval rules are in [closure protocols](CLOSURE.md).

| Obligation / parent | Design | Existing executable entry point | Coverage limitation |
| --- | --- | --- | --- |
| SWF-01 / UI-REQ-002 | [docs/design/TREATMENT.md](../../docs/design/TREATMENT.md) | `test_guided.GuidedUnitTests.test_guided_machine_protocol_and_actual_lvgl_view` | Integrity negative case and nominal completion exist; six other individual check failures need explicit cases. |
| SWF-02 / UI-REQ-002 | [docs/design/TREATMENT.md](../../docs/design/TREATMENT.md) | `test_guided.GuidedUnitTests.test_guided_machine_protocol_and_actual_lvgl_view` | direct assertion or named fixture; current result acceptance pending |
| SWF-03 / M5-REQ-002 | [docs/design/TREATMENT.md](../../docs/design/TREATMENT.md) | `test_guided.GuidedUnitTests.test_in_process_hydraulics_complete_cycle_and_patient_transactions` | direct assertion or named fixture; current result acceptance pending |
| SWF-04 / UI-REQ-002 | [docs/design/TREATMENT.md](../../docs/design/TREATMENT.md) | `test_guided.GuidedUnitTests.test_guided_machine_protocol_and_actual_lvgl_view` | direct assertion or named fixture; current result acceptance pending |
| SWF-05 / UI-REQ-002 | [docs/design/TREATMENT.md](../../docs/design/TREATMENT.md) | `test_guided.GuidedUnitTests.test_guided_machine_protocol_and_actual_lvgl_view` | direct assertion or named fixture; current result acceptance pending |
| SWF-06 / UI-REQ-002 | [docs/design/TREATMENT.md](../../docs/design/TREATMENT.md) | `test_guided.GuidedProcessTests.test_full_guided_cycle_preserves_water_solutes_and_stage_evidence` | direct assertion or named fixture; current result acceptance pending |
| SWF-07 / UI-REQ-002 | [docs/design/TREATMENT.md](../../docs/design/TREATMENT.md) | `test_guided.GuidedUnitTests.test_guided_machine_protocol_and_actual_lvgl_view` | direct assertion or named fixture; current result acceptance pending |
| SWF-08 / M5-REQ-004 | [docs/design/TREATMENT.md](../../docs/design/TREATMENT.md) | `test_machine.MachineTests.test_reset_needs_three_safe_cycles_and_never_resumes_automatically` | Legacy reset test plus guided fixture; complete alarm-by-guided-phase matrix is a planned test obligation. |
| SUI-01 / UI-REQ-002 | [docs/design/INTERACTION.md](../../docs/design/INTERACTION.md) | `test_guided.GuidedUnitTests.test_guided_machine_protocol_and_actual_lvgl_view` | direct assertion or named fixture; current result acceptance pending |
| SUI-02 / UI-REQ-002 | [docs/design/INTERACTION.md](../../docs/design/INTERACTION.md) | `test_guided.GuidedUnitTests.test_guided_machine_protocol_and_actual_lvgl_view` | direct assertion or named fixture; current result acceptance pending |
| SUI-03 / UI-REQ-002 | [docs/design/INTERACTION.md](../../docs/design/INTERACTION.md) | `test_guided.GuidedUnitTests.test_guided_machine_protocol_and_actual_lvgl_view` | direct assertion or named fixture; current result acceptance pending |
| SUI-04 / M6-REQ-005 | [docs/design/INTERACTION.md](../../docs/design/INTERACTION.md) | `test_device_sessions.DeviceSessionTests.test_restart_reusing_intent_number_cannot_accept_old_confirmation` | Direct old-confirmation rejection after session replacement; independent acceptance pending. |
| SIF-01 / M1-REQ-007 | [docs/design/INTERFACES.md](../../docs/design/INTERFACES.md) | `test_machine.MachineTests.test_lost_step_each_role_stops_and_invalidates_pending_m5_decisions` | direct assertion or named fixture; current result acceptance pending |
| SIF-02 / REQ-002 | [docs/design/INTERFACES.md](../../docs/design/INTERFACES.md) | `test_machine.MachineTests.test_simultaneous_hazards_apply_before_commit_and_defeat_hostile_control` | direct assertion or named fixture; current result acceptance pending |
| SIF-03 / REQ-004 | [docs/design/INTERFACES.md](../../docs/design/INTERFACES.md) | `test_machine.MachineTests.test_each_detector_observation_bound_and_specific_actuator_action` | Detector fixture exists; explicit five-corruption channel matrix is allocated in the parent protocol. |
| SIF-04 / M1-REQ-007 | [docs/design/INTERFACES.md](../../docs/design/INTERFACES.md) | `test_machine.MachineTests.test_m5_wall_watchdog_terminal_state_and_observation_remain_separate` | direct assertion or named fixture; current result acceptance pending |
| SIF-05 / M1-REQ-009 | [docs/design/INTERFACES.md](../../docs/design/INTERFACES.md) | `test_compose_collection.ComposeCollectionTests.test_failed_extraction_keeps_volume_and_recovery_commands` | Direct extraction failure/retention case; other collection phases covered by adjacent suite methods. |
| SMOD-01 / REQ-003 | [docs/design/MODELS.md](../../docs/design/MODELS.md) | `test_physical.PhysicalProcessTests.test_real_services_and_retained_evidence` | direct assertion or named fixture; current result acceptance pending |
| SMOD-02 / DYN-REQ-001 | [docs/design/MODELS.md](../../docs/design/MODELS.md) | `test_dynamics.DynamicsTests.test_distributed_transit_delay_conservation_and_atomic_rejection` | direct assertion or named fixture; current result acceptance pending |
| SMOD-03 / PHY-REQ-001 | [docs/design/MODELS.md](../../docs/design/MODELS.md) | `test_physical.PhysicalTests.test_uf_hemoconcentration_refill_and_rbc_conservation` | direct assertion or named fixture; current result acceptance pending |
| SMOD-04 / PHY-REQ-001 | [docs/design/MODELS.md](../../docs/design/MODELS.md) | `test_physical.PhysicalTests.test_equations_and_limits` | direct assertion or named fixture; current result acceptance pending |
| SMOD-05 / DYN-REQ-001 | [docs/design/MODELS.md](../../docs/design/MODELS.md) | `test_dynamics.DynamicsTests.test_gas_pumps_balancing_and_independent_level_protection` | direct assertion or named fixture; current result acceptance pending |
| SMOD-06 / DYN-REQ-001 | [docs/design/MODELS.md](../../docs/design/MODELS.md) | `test_physical.PhysicalTests.test_in_process_physical_treatments` | direct assertion or named fixture; current result acceptance pending |
| SMOD-07 / DYN-REQ-001 | [docs/design/MODELS.md](../../docs/design/MODELS.md) | `test_dynamics.DynamicsTests.test_gas_pumps_balancing_and_independent_level_protection` | direct assertion or named fixture; current result acceptance pending |
| SMOD-08 / DYN-REQ-001 | [docs/design/MODELS.md](../../docs/design/MODELS.md) | `test_dynamics.DynamicsTests.test_gas_pumps_balancing_and_independent_level_protection` | direct assertion or named fixture; current result acceptance pending |
| SMOD-09 / DYN-REQ-001 | [docs/design/MODELS.md](../../docs/design/MODELS.md) | `test_dynamics.DynamicsTests.test_distributed_transit_delay_conservation_and_atomic_rejection` | Transit/atomic-rejection fixture exists; route allocation also relies on physical three-mode cycles. |
| SMOD-10 / PHY-REQ-001 | [docs/design/MODELS.md](../../docs/design/MODELS.md) | `test_physical.PhysicalTests.test_equations_and_limits` | direct assertion or named fixture; current result acceptance pending |
| SMOD-11 / REQ-006 | [docs/design/MODELS.md](../../docs/design/MODELS.md) | `test_machine.MachineTests.test_quality_detectors_trip_in_their_first_unsafe_observation_cycle` | direct assertion or named fixture; current result acceptance pending |
| SMOD-12 / DYN-REQ-001 | [docs/design/MODELS.md](../../docs/design/MODELS.md) | `test_dynamics.DynamicsTests.test_reference_holdout_and_discretization_are_reported` | direct assertion or named fixture; current result acceptance pending |
| SMOD-13 / M3-REQ-001 | [docs/design/MODELS.md](../../docs/design/MODELS.md) | `test_dynamics.DynamicsTests.test_distributed_transit_delay_conservation_and_atomic_rejection` | direct assertion or named fixture; current result acceptance pending |
| SEXP-01 / M7-REQ-003 | [docs/design/INTERACTION.md](../../docs/design/INTERACTION.md) | `test_experiments.ExperimentTests.test_external_stop_while_paused_aborts_without_resume_or_another_tick` | direct assertion or named fixture; current result acceptance pending |
| SEXP-02 / M7-REQ-004 | [docs/design/INTERACTION.md](../../docs/design/INTERACTION.md) | `test_experiments.ExperimentReviewTests.test_comparison_and_export_reject_every_contradictory_identity` | direct assertion or named fixture; current result acceptance pending |
| SQA-01 / M8-REQ-006 | [docs/design/INTERFACES.md](../../docs/design/INTERFACES.md) | `test_documentation.DocumentationTests.test_last_requirement_edit_invalidates_generated_candidate` | direct assertion or named fixture; current result acceptance pending |
| SQA-02 / M8-REQ-006 | [docs/design/INTERFACES.md](../../docs/design/INTERFACES.md) | `test_documentation.DocumentationTests.test_historical_pass_does_not_become_current_acceptance` | direct assertion or named fixture; current result acceptance pending |

## Parent obligations outside this supplemental decomposition

These parents remain in the SRS and existing catalogue; they are not considered
atomically covered merely because another requirement has a test allocation.

M1-REQ-001, M1-REQ-002, M1-REQ-003, M1-REQ-004, M1-REQ-005, M1-REQ-006, M1-REQ-008, M2-REQ-001, M2-REQ-002, M2-REQ-003, M2-REQ-004, M3-REQ-002, M3-REQ-003, M3-REQ-004, M4-REQ-001, M4-REQ-002, M4-REQ-003, M4-REQ-004, M5-REQ-001, M5-REQ-003, M5-REQ-005, M5-REQ-006, M6-REQ-001, M6-REQ-002, M6-REQ-003, M6-REQ-004, M6-REQ-006, M7-REQ-001, M7-REQ-002, M7-REQ-005, M7-REQ-006, M8-REQ-001, M8-REQ-002, M8-REQ-003, M8-REQ-004, M8-REQ-005, M9-REQ-001, M9-REQ-002, M9-REQ-003, M9-REQ-004, M9-REQ-005, REQ-001, REQ-005, UI-REQ-001.
