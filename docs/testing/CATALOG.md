# Current verification catalogue

Document ID STC-01; revision controlled by Git. Generated inventory, not a test report.

Read [Master plan](PLAN.md) first. [Current status](STATUS.md) identifies baseline applicability.
Historical outcomes and milestone reports belong to the separate Project Log and are not
rendered here. A method name proves that a test exists, not that it ran or fully covers a requirement.

## Registered verification obligations

### System boundaries and protective principles

#### TEST-001

**Requirements:** REQ-001.

**Procedure:** Attempt patient edits, fault injection and simulation clock changes from the device-ui identity; repeat from the authorized external console.

**Expected:** Device identity requests are denied; authorized console requests are recorded and allowed.

**Current acceptance:** not independently approved; no historical result inherited.

#### TEST-002

**Requirements:** REQ-002.

**Procedure:** Inject each approved protection state and conflicting control commands, including control restart and duplicate messages.

**Expected:** Protective outputs persist; reset only follows the approved hazard-specific conditions.

**Current acceptance:** not independently approved; no historical result inherited.

#### TEST-003

**Requirements:** REQ-003.

**Procedure:** Run zero-removal, constant-flow, pre/post HDF and interrupted-substitution scenarios against independently derived balances.

**Expected:** Recorded balances agree with the independent oracle within predeclared tolerances.

**Current acceptance:** not independently approved; no historical result inherited.

#### TEST-004

**Requirements:** REQ-004.

**Procedure:** Inject stale, missing, reordered, invalid and biased measurements; pause/accelerate the simulation and separately kill a process.

**Expected:** Responses match the approved fault policy, with measured timing and no mistaken pause-induced result.

**Current acceptance:** not independently approved; no historical result inherited.

#### TEST-005

**Requirements:** REQ-005.

**Procedure:** Acknowledge and silence persistent alarms, disconnect the UI and attempt invalid resets.

**Expected:** Protective behavior and displayed/alarm-delivery state match the approved alarm catalog.

**Current acceptance:** not independently approved; no historical result inherited.

#### TEST-006

**Requirements:** REQ-006.

**Procedure:** Inject composition, thermal, route and integrity faults, including faults without a corresponding measurement/test signal.

**Expected:** Observable cases follow the protective policy; unobservable cases are not falsely reported as detected or proof of sterility.

**Current acceptance:** not independently approved; no historical result inherited.

### Execution, failure handling and records

#### M1-TEST-001

**Requirements:** M1-REQ-001.

**Procedure:** Execute native build, Compose nominal/occlusion runs, publication and container boundary tests.

**Expected:** CMake builds successfully; Compose runs five isolated services and records source, binary and configuration identities.

**Current acceptance:** not independently approved; no historical result inherited.

#### M1-TEST-002

**Requirements:** M1-REQ-002.

**Procedure:** Run same-seed replay, cross-build comparison and clean-build binary hash comparison.

**Expected:** Identical configuration and seed yield byte-identical same-build trajectories; cross-build numerics agree within absolute/relative 1e-9; clean same-toolchain CMake builds produce identical executables.

**Current acceptance:** not independently approved; no historical result inherited.

#### M1-TEST-003

**Requirements:** M1-REQ-003.

**Procedure:** Calculate expected fluid loss from input rates, interval duration and independently specified active interval count; compare both service totals and patient volume.

**Expected:** Nominal, zero-UF, stopped-flow and partial-flow runs match independent Decimal balances within 1e-8 mL; long patient ledger drift stays below 1e-8 mL.

**Current acceptance:** not independently approved; no historical result inherited.

#### M1-TEST-004

**Requirements:** M1-REQ-004.

**Procedure:** Run occlusion scenario and kill control at fault onset; inspect protection observation, decision and applied actuator state.

**Expected:** Tick-5 resistance increase produces a measured pressure of 600 mmHg; the synthetic 250 mmHg trip stops blood/UF and closes clamp within one 100 ms virtual interval, including when control has died.

**Current acceptance:** not independently approved; no historical result inherited.

#### M1-TEST-005

**Requirements:** M1-REQ-005.

**Procedure:** Continue conflicting control demand after occlusion; issue role-forged and duplicate commands and inspect resulting state.

**Expected:** Repeated 300 mL/min control demand and later PERMIT cannot release latched zero blood/UF and closed clamp; unauthorized role and duplicate tick messages fail closed.

**Current acceptance:** not independently approved; no historical result inherited.

#### M1-TEST-006

**Requirements:** M1-REQ-006.

**Procedure:** Inject every supported sensor fault at tick 5 and verify timing, channel separation, and conservation.

**Expected:** Invalid, missing, stale, future and replayed protection samples trip within one 100 ms interval; a control-only fault does not corrupt the protection channel.

**Current acceptance:** not independently approved; no historical result inherited.

#### M1-TEST-007

**Requirements:** M1-REQ-007.

**Procedure:** Run process-kill/pause tests plus test_rpc_abort: discard control and protection STEP replies after real plant acceptance; assert call order, absence of COMMIT/ADVANCE, independently observed stop, late-command rejection, unacknowledged HALT and unavailable STATUS. Observe the independent watchdog separately after failed delivery.

**Expected:** Failed STEP (including lost reply after plant acceptance) sends no COMMIT/ADVANCE; HALT cancels pending decisions and rejects later commits. Abort cause, stop acknowledgment and observed outputs are distinct; failed stop/observation never implies confirmed zero. Plant/patient loss aborts; runner loss trips the wall lease without virtual advancement.

**Current acceptance:** not independently approved; no historical result inherited.

#### M1-TEST-008

**Requirements:** M1-REQ-008.

**Procedure:** Run test_trajectory regressions (RSS, short writes, torn tail, killed real runner) and verify_m1_review long Docker scenarios.

**Expected:** Two actual 100000-tick Compose runs complete under 128 MiB with peak runner RSS <=64 MiB. Records are ordered/complete and repeated hashes agree with independently hashed written bytes. SIGKILL preserves a recoverable complete prefix.

**Current acceptance:** not independently approved; no historical result inherited.

#### M1-TEST-009

**Requirements:** M1-REQ-009.

**Procedure:** Run test_compose_collection command-order/error regressions and three real failure/recovery cases in verify_m1_review.

**Expected:** Aborted runner, pre-start failure and failed extraction retain logs/reports; original exit code is preserved. Failed extraction retains volumes and stopped containers with usable recovery commands; verify actual artifact recovery before cleanup.

**Current acceptance:** not independently approved; no historical result inherited.

### Hydraulics, patient and prepared fluids

#### M2-TEST-001

**Requirements:** M2-REQ-001.

**Procedure:** Run tests/test_circuit.py and tools/verify_models.py natively and in Compose.

**Expected:** Analytic RC and resistor solutions, decreasing step-halving errors, clamps and component changes.

**Current acceptance:** not independently approved; no historical result inherited.

#### M2-TEST-002

**Requirements:** M2-REQ-002.

**Procedure:** Run tests/test_circuit.py and tools/verify_models.py natively and in Compose.

**Expected:** Per-tick residual <=1e-8 mL and cumulative <=1e-6 mL with independent node-volume accounting.

**Current acceptance:** not independently approved; no historical result inherited.

#### M2-TEST-003

**Requirements:** M2-REQ-003.

**Procedure:** Run tests/test_circuit.py and tools/verify_models.py natively and in Compose.

**Expected:** Two profiles, independent clearance formula, equilibrium and zero-flow/zero-membrane cases.

**Current acceptance:** not independently approved; no historical result inherited.

#### M2-TEST-004

**Requirements:** M2-REQ-004.

**Procedure:** Run tests/test_circuit.py and tools/verify_models.py natively and in Compose.

**Expected:** Actual process/Compose runs; repeated hashes; occlusion latch by 1000 ms and lost STEP cancels commit.

**Current acceptance:** not independently approved; no historical result inherited.

#### M3-TEST-001

**Requirements:** M3-REQ-001.

**Procedure:** Run tests/test_compartments.py and tools/verify_models.py with patient scenarios natively/in Compose.

**Expected:** Ordered bounded transactions preserve positive mass and concentration; rejected updates leave the prior state intact.

**Current acceptance:** not independently approved; no historical result inherited.

#### M3-TEST-002

**Requirements:** M3-REQ-002.

**Procedure:** Run tests/test_compartments.py and tools/verify_models.py with patient scenarios natively/in Compose.

**Expected:** Independent balances <=1e-6 mL/mmol, analytic transient and step-halving tests, 100000-step process RSS below 64 MiB.

**Current acceptance:** not independently approved; no historical result inherited.

#### M3-TEST-003

**Requirements:** M3-REQ-003.

**Procedure:** Run tests/test_compartments.py and tools/verify_models.py with patient scenarios natively/in Compose.

**Expected:** Synthetic baseline/overload/imbalance scenarios and independently calculated infusion/generation/excretion cases.

**Current acceptance:** not independently approved; no historical result inherited.

#### M3-TEST-004

**Requirements:** M3-REQ-004.

**Procedure:** Run tests/test_compartments.py and tools/verify_models.py with patient scenarios natively/in Compose.

**Expected:** Native and Compose runs repeat, identify exact build/config, enforce protective stops and retain partial transactions on patient failure.

**Current acceptance:** not independently approved; no historical result inherited.

#### M4-TEST-001

**Requirements:** M4-REQ-001.

**Procedure:** Run treatment numerical/process tests and real Compose mode/fault matrix.

**Expected:** Independent whole-system balances <=1e-6 mL/mmol; distinct gross UF/substitution/storage/net loss.

**Current acceptance:** not independently approved; no historical result inherited.

#### M4-TEST-002

**Requirements:** M4-REQ-002.

**Procedure:** Run treatment numerical/process tests and real Compose mode/fault matrix.

**Expected:** Analytic equilibrium/transient, convergence and filter pressure-loss checks.

**Current acceptance:** not independently approved; no historical result inherited.

#### M4-TEST-003

**Requirements:** M4-REQ-003.

**Procedure:** Run treatment numerical/process tests and real Compose mode/fault matrix.

**Expected:** Quality latch within one dt after observable threshold; no delivery/UF/dialysate despite conflicting control.

**Current acceptance:** not independently approved; no historical result inherited.

#### M4-TEST-004

**Requirements:** M4-REQ-004.

**Procedure:** Run treatment numerical/process tests and real Compose mode/fault matrix.

**Expected:** Repeat native/Compose modes/faults; exact build/config identity and compatibility regressions.

**Current acceptance:** not independently approved; no historical result inherited.

#### PHY-TEST-001

**Requirements:** PHY-REQ-001.

**Procedure:** Run PhysicalTests and GuidedUnitTests: equations, 648 operating points, complete HD/pre/post in-process plant/patient cycles, hematocrit/refill, conservation, protocol and actual LVGL rendering.

**Expected:** Local laws, constraints and independent segment/ledger checks pass; no clinical validation claimed.

**Current acceptance:** not independently approved; no historical result inherited.

#### PHY-TEST-002

**Requirements:** PHY-REQ-001.

**Procedure:** Run PhysicalProcessTests on the socket-capable CI host with native and sanitized service binaries; independently verify retained physical trajectories.

**Expected:** Complete three physical modality cycles through real RPC and verify all physical and patient ledgers.

**Current acceptance:** not independently approved; no historical result inherited.

#### DYN-TEST-001

**Requirements:** DYN-REQ-001.

**Procedure:** Execute dynamic equations, complete HD/PRE/POST plant/patient cycles, independent trajectory balances, malformed/oversize rejection, streaming memory and actual LVGL/console checks.

**Expected:** All scoped numerical/software assertions pass with calibration limits explicitly retained.

**Current acceptance:** not independently approved; no historical result inherited.

#### DYN-TEST-002

**Requirements:** DYN-REQ-001.

**Procedure:** Fit selected public urea reference points at Qb 300, check held-out Qb 400 within the stated 5% comparison tolerance, and execute the exported largest profile in three modalities.

**Expected:** All scoped numerical/software assertions pass with calibration limits explicitly retained.

**Current acceptance:** not independently approved; no historical result inherited.

#### DYN-TEST-003

**Requirements:** DYN-REQ-001.

**Procedure:** Run PhysicalProcessTests in native and sanitized CI; run all three physical modalities through Compose and verify retained trajectories.

**Expected:** Bounded real RPC and containers preserve lifecycle constraints and all physical/distributed ledgers.

**Current acceptance:** not independently approved; no historical result inherited.

#### MIX-TEST-001

**Requirements:** MIX-REQ-001.

**Procedure:** test_preparation.PreparationTests.test_line_air_water_and_concentrate_displacement; full campaign: python3 tools/verify_preparation.py --output <new-report.json>

**Expected:** Exercise dry, wetted and residual-liquid starts; downstream arrival follows displaced volume and conserves inventories.

**Current acceptance:** not independently approved; no historical result inherited.

#### MIX-TEST-002

**Requirements:** MIX-REQ-002.

**Procedure:** test_preparation.PreparationTests.test_distinct_pump_displacement_pressure_and_air_efficiency; full campaign: python3 tools/verify_preparation.py --output <new-report.json>

**Expected:** Exercise zero command, pressure load, air aspiration and actuator saturation; actual liquid delivery follows the declared pump law, not commanded displacement alone.

**Current acceptance:** not independently approved; no historical result inherited.

#### MIX-TEST-003

**Requirements:** MIX-REQ-003.

**Procedure:** test_preparation.PreparationTests.test_cartridge_liquid_gas_and_solute_storage; full campaign: python3 tools/verify_preparation.py --output <new-report.json>

**Expected:** Fill and withdraw from known initial inventories; storage changes match all boundary transfers and inventories remain nonnegative.

**Current acceptance:** not independently approved; no historical result inherited.

#### MIX-TEST-004

**Requirements:** MIX-REQ-004.

**Procedure:** test_preparation.PreparationTests.test_pressure_stop_and_bounded_startup_failures; full campaign: python3 tools/verify_preparation.py --output <new-report.json>

**Expected:** Block vent, restrict inlet and increase withdrawal; pressure follows the declared law and limit violations inhibit the conflicting actuator before the allocated deadline.

**Current acceptance:** not independently approved; no historical result inherited.

#### MIX-TEST-005

**Requirements:** MIX-REQ-005.

**Procedure:** test_preparation.PreparationTests.test_saturation_and_finite_dissolution_with_solid_remaining; full campaign: python3 tools/verify_preparation.py --output <new-report.json>

**Expected:** At adequate residence time approach saturation; under dissolution-limited withdrawal remain below saturation despite remaining solid.

**Current acceptance:** not independently approved; no historical result inherited.

#### MIX-TEST-006

**Requirements:** MIX-REQ-006.

**Procedure:** test_preparation.PreparationTests.test_solid_exhaustion_preserves_dissolved_washout; full campaign: python3 tools/verify_preparation.py --output <new-report.json>

**Expected:** Exhaust solid and continue water throughput; dissolved inventory washes out conservatively rather than disappearing or remaining indefinitely constant.

**Current acceptance:** not independently approved; no historical result inherited.

#### MIX-TEST-007

**Requirements:** MIX-REQ-007.

**Procedure:** test_preparation.PreparationTests.test_acid_concentration_step_and_bag_depletion; full campaign: python3 tools/verify_preparation.py --output <new-report.json>

**Expected:** Apply nominal, diluted and exhausted-source cases; concentration and delivered mass change consistently, including configured air ingress after depletion.

**Current acceptance:** not independently approved; no historical result inherited.

#### MIX-TEST-008

**Requirements:** MIX-REQ-008.

**Procedure:** test_preparation.PreparationTests.test_mixed_tank_matches_independent_exponential; full campaign: python3 tools/verify_preparation.py --output <new-report.json>

**Expected:** Compare a well-mixed tank with its analytic step response and transport with volume/flow delay; verify independent inventory residuals.

**Current acceptance:** not independently approved; no historical result inherited.

#### MIX-TEST-009

**Requirements:** MIX-REQ-009.

**Procedure:** test_preparation.PreparationTests.test_delayed_stale_invalid_sensors_and_control_input_boundary; full campaign: python3 tools/verify_preparation.py --output <new-report.json>

**Expected:** Inject delayed, stale, invalid and air-exposed measurements; invalid signals cannot authorize readiness. Changing hidden inventory alone cannot directly change a control decision with identical sensor history.

**Current acceptance:** not independently approved; no historical result inherited.

#### MIX-TEST-010

**Requirements:** MIX-REQ-010.

**Procedure:** test_preparation.PreparationTests.test_pi_saturation_antiwindup_and_invalid_freeze; full campaign: python3 tools/verify_preparation.py --output <new-report.json>

**Expected:** Apply flow/concentration steps, saturation and invalidity; commands remain bounded, integrator behavior matches the specified policy and recovery meets prospective response criteria.

**Current acceptance:** not independently approved; no historical result inherited.

#### MIX-TEST-011

**Requirements:** MIX-REQ-011.

**Procedure:** test_preparation.PreparationTests.test_compensating_errors_and_continuous_dwell; full campaign: python3 tools/verify_preparation.py --output <new-report.json>

**Expected:** Construct compensating acid/bicarbonate errors with similar final conductivity; documented intermediate checks detect the observable cases and remaining detection gaps are reported.

**Current acceptance:** not independently approved; no historical result inherited.

#### MIX-TEST-012

**Requirements:** MIX-REQ-012.

**Procedure:** test_preparation.PreparationTests.test_pressure_stop_and_bounded_startup_failures; full campaign: python3 tools/verify_preparation.py --output <new-report.json>

**Expected:** Hold each prerequisite false in turn; reject premature dosing qualification and enter the declared failure response on timeout.

**Current acceptance:** not independently approved; no historical result inherited.

#### MIX-TEST-013

**Requirements:** MIX-REQ-013.

**Procedure:** test_preparation.PreparationTests.test_final_authority_blocks_unqualified_fluid_despite_forged_permits; full campaign: python3 tools/verify_preparation.py --output <new-report.json>

**Expected:** Challenge every startup phase, each invalid guard and loss of qualification; verify actual routed volumes, not just displayed state.

**Current acceptance:** not independently approved; no historical result inherited.

#### MIX-TEST-014

**Requirements:** MIX-REQ-014.

**Procedure:** test_preparation.PreparationTests.test_compensating_errors_and_continuous_dwell; full campaign: python3 tools/verify_preparation.py --output <new-report.json>

**Expected:** Test just below/at/above the dwell boundary and an intervening invalid sample; interruptions reset qualification and a single valid sample cannot authorize delivery.

**Current acceptance:** not independently approved; no historical result inherited.

#### MIX-TEST-015

**Requirements:** MIX-REQ-015.

**Procedure:** test_preparation.PreparationTests.test_time_refinement_against_predeclared_budget; full campaign: python3 tools/verify_preparation.py --output <new-report.json>

**Expected:** Independently reconstruct balances across startup, zero flow, partial steps and exhaustion; refinements of timestep and transport discretization satisfy predeclared error budgets.

**Current acceptance:** not independently approved; no historical result inherited.

#### MIX-TEST-016

**Requirements:** MIX-REQ-016.

**Procedure:** test_preparation.PreparationTests.test_evidence_identity_changes_with_source_and_configuration; full campaign: python3 tools/verify_preparation.py --output <new-report.json>

**Expected:** Reproduce a fixed scenario and verify complete trace in both directions; changed source/configuration invalidates prior applicability.

**Current acceptance:** not independently approved; no historical result inherited.

#### MIX-TEST-017

**Requirements:** MIX-REQ-017.

**Procedure:** Deferred replacement protocol MIX-TEST-017; no executable method or execution claim.

**Expected:** Deferred protocol; blocked pending replacement design. No replacement implementation or successful test is claimed.

**Current acceptance:** not independently approved; no historical result inherited.

### Treatment lifecycle and operator interface

#### M5-TEST-001

**Requirements:** M5-REQ-001.

**Procedure:** Execute lifecycle/protection/device-interface process tests and repeated native/Compose workflow/fault matrix.

**Expected:** All required normal and forbidden transitions tested; safe startup/end and requested versus effective state.

**Current acceptance:** not independently approved; no historical result inherited.

#### M5-TEST-002

**Requirements:** M5-REQ-002.

**Procedure:** Execute lifecycle/protection/device-interface process tests and repeated native/Compose workflow/fault matrix.

**Expected:** Independent water/six-species source/waste balances <=1e-6 mL/mmol; patient isolated during flush.

**Current acceptance:** not independently approved; no historical result inherited.

#### M5-TEST-003

**Requirements:** M5-REQ-003.

**Procedure:** Execute lifecycle/protection/device-interface process tests and repeated native/Compose workflow/fault matrix.

**Expected:** Pressure/flow/air/leak/quality/balance/validity/comms actions immediate before commit within declared virtual/wall budgets.

**Current acceptance:** not independently approved; no historical result inherited.

#### M5-TEST-004

**Requirements:** M5-REQ-004.

**Procedure:** Execute lifecycle/protection/device-interface process tests and repeated native/Compose workflow/fault matrix.

**Expected:** No override; three safe observations in recovery for reset; failures/restarts cannot auto-resume.

**Current acceptance:** not independently approved; no historical result inherited.

#### M5-TEST-005

**Requirements:** M5-REQ-005.

**Procedure:** Execute lifecycle/protection/device-interface process tests and repeated native/Compose workflow/fault matrix.

**Expected:** Validated requests/confirmations and modeled observations; no UI mount/access to administration or patient truth.

**Current acceptance:** not independently approved; no historical result inherited.

#### M5-TEST-006

**Requirements:** M5-REQ-006.

**Procedure:** Execute lifecycle/protection/device-interface process tests and repeated native/Compose workflow/fault matrix.

**Expected:** Real native/Compose workflows/faults/restarts/replay, numerical balances and all affected regressions.

**Current acceptance:** not independently approved; no historical result inherited.

#### M6-TEST-001

**Requirements:** M6-REQ-001.

**Procedure:** Execute actual device widget/service tests, native/Compose headless and available graphical workflows, retained screenshots and existing regressions.

**Expected:** Native/Compose headless and available graphical rendering against actual services.

**Current acceptance:** not independently approved; no historical result inherited.

#### M6-TEST-002

**Requirements:** M6-REQ-002.

**Procedure:** Execute actual device widget/service tests, native/Compose headless and available graphical workflows, retained screenshots and existing regressions.

**Expected:** HD/pre/post setup, visible units/bounds, actual server completion and rejection handling.

**Current acceptance:** not independently approved; no historical result inherited.

#### M6-TEST-003

**Requirements:** M6-REQ-003.

**Procedure:** Execute actual device widget/service tests, native/Compose headless and available graphical workflows, retained screenshots and existing regressions.

**Expected:** Distinct intent/state, UF/sub/net counters, timestamps, invalid/stale/disconnected data; no invented zeros.

**Current acceptance:** not independently approved; no historical result inherited.

#### M6-TEST-004

**Requirements:** M6-REQ-004.

**Procedure:** Execute actual device widget/service tests, native/Compose headless and available graphical workflows, retained screenshots and existing regressions.

**Expected:** Separate ACK/silence/reset, no overrides/admin endpoints, actual device-only mount denial tests.

**Current acceptance:** not independently approved; no historical result inherited.

#### M6-TEST-005

**Requirements:** M6-REQ-005.

**Procedure:** Execute actual device widget/service tests, native/Compose headless and available graphical workflows, retained screenshots and existing regressions.

**Expected:** New session clears pending/trends, rejects old confirmations, no automatic retry of ambiguous critical requests.

**Current acceptance:** not independently approved; no historical result inherited.

#### M6-TEST-006

**Requirements:** M6-REQ-006.

**Procedure:** Execute actual device widget/service tests, native/Compose headless and available graphical workflows, retained screenshots and existing regressions.

**Expected:** Real widgets/RPCs/screenshots, exact build/dependencies/configuration and affected regressions; no mocked integration.

**Current acceptance:** not independently approved; no historical result inherited.

#### UI-TEST-001

**Requirements:** UI-REQ-001.

**Procedure:** Run tests/test_inspection.py and inspect actual headless recorded-data console captures.

**Expected:** Bounded numeric history; session resets; recorded read-only navigation and hold/resume.

**Current acceptance:** not independently approved; no historical result inherited.

#### UI-TEST-002

**Requirements:** UI-REQ-001.

**Procedure:** Run verify_console.py, verify_device_ui.py and experiment Compose/WSLg checks on a socket-capable Linux/WSL2 host.

**Expected:** Live plotting/animation and protective command regressions pass without loss of freshness or session isolation.

**Current acceptance:** not independently approved; no historical result inherited.

#### UI-TEST-003

**Requirements:** UI-REQ-002.

**Procedure:** Run tests/test_guided.py GuidedUnitTests including the real C++ plant in-process and the LVGL render fixture.

**Expected:** Transitions/guards, serialization, actual phase-dependent widgets and conserved rinseback transfers pass in all three modalities.

**Current acceptance:** not independently approved; no historical result inherited.

#### UI-TEST-004

**Requirements:** UI-REQ-002.

**Procedure:** Run GuidedProcessTests and existing native/Compose device and experiment acceptance on a socket-capable Linux/WSL2 host. Include test_guided_live_blood_and_active_infusion_edits in tests/ui_regressions.py for both HDF routes.

**Expected:** Complete HD, HDF pre/post guided cycles retain correct state and patient balances across real RPC boundaries; existing sessions, confirmation and STOP regressions pass.

**Current acceptance:** not independently approved; no historical result inherited.

#### SYN-TEST-001

**Requirements:** SYN-REQ-001.

**Procedure:** test_synoptic.SynopticTests.test_actual_lvgl_modes_responsive_touch_and_stale; python3 tools/verify_synoptic.py --output <new-report.json>

**Expected:** Treatment home shall show a large simplified external dialyzer and extracorporeal circuit with directional flow and explicit HD / HDF PRE / HDF POST routing. Roller pumps, chamber detail, containers and full plumbing shall be available in dedicated Blood circuit and Hydraulics tabs. Render each mode and assert active branches and view allocation.

**Current acceptance:** not independently approved; no historical result inherited.

#### SYN-TEST-002

**Requirements:** SYN-REQ-002.

**Procedure:** test_synoptic.SynopticTests.test_motion_freshness_routes_and_inventory; python3 tools/verify_synoptic.py --output <new-report.json>

**Expected:** Motion shall use current valid observed/model telemetry, never prescribed flow. Zero flow freezes phase; stale/invalid telemetry freezes motion and displays its status, without portraying unknown as zero. Changing flow preserves phase. Unit checks exercise zero, restart, rate changes and loss/recovery of freshness.

**Current acceptance:** not independently approved; no historical result inherited.

#### SYN-TEST-003

**Requirements:** SYN-REQ-003.

**Procedure:** test_document_contracts.WireWitnessTests.test_concentrate_drive_is_distinct_from_dry_liquid_and_legacy_is_absent; python3 tools/verify_synoptic.py --output <new-report.json>

**Expected:** Pump activity and fluid passage shall be distinguished. Concentrate drive and delivered liquid require separate versioned observations; older observations show unavailable fields. No mechanical RPM shall be claimed. Test C++/Python round trips and a dry-line fixture.

**Current acceptance:** not independently approved; no historical result inherited.

#### SYN-TEST-004

**Requirements:** SYN-REQ-004.

**Procedure:** test_synoptic.SynopticTests.test_actual_lvgl_modes_responsive_touch_and_stale; python3 tools/verify_synoptic.py --output <new-report.json>

**Expected:** Dialysate traversal, bypass and unknown route shall be distinguished with labels and valve/path geometry. Motion in a bypass shall not imply membrane traversal. Test bypass with positive feed and zero/unknown feed.

**Current acceptance:** not independently approved; no historical result inherited.

#### SYN-TEST-005

**Requirements:** SYN-REQ-005.

**Procedure:** test_synoptic.SynopticTests.test_actual_lvgl_modes_responsive_touch_and_stale; python3 tools/verify_synoptic.py --output <new-report.json>

**Expected:** Phase progress, phase/session time, net UF and substitution totals versus explicitly labelled current-prescription goals shall remain visible on home. Totals come from authoritative meters and survive pause/resume; no UI integration or invented target history. Test paused totals, HD, changed prescriptions and unavailable observations.

**Current acceptance:** not independently approved; no historical result inherited.

#### SYN-TEST-006

**Requirements:** SYN-REQ-006.

**Procedure:** test_synoptic.SynopticTests.test_actual_lvgl_modes_responsive_touch_and_stale; python3 tools/verify_synoptic.py --output <new-report.json>; test_synoptic.SynopticTests.test_sdl_resize_finger_input_and_focus_cancellation

**Expected:** Filled icons shall accompany text on navigation and actions. Guided controls shall have at least 48 logical pixels height; STOP shall remain visible outside scrollable content. Reflow shall support 800x890, 1100x890 and 1440x1000 without scaling hit targets. Test bounds, non-overlap and real LVGL rendering.

**Current acceptance:** not independently approved; no historical result inherited.

#### SYN-TEST-007

**Requirements:** SYN-REQ-007.

**Procedure:** test_synoptic.SynopticTests.test_motion_freshness_routes_and_inventory; python3 tools/verify_synoptic.py --output <new-report.json>

**Expected:** Chamber fractions shall use measured fractions. Container bars shall be explicitly relative to first observed session inventory, with absolute quantities/units; missing baselines and unavailable telemetry shall not show fabricated capacity. Session changes reset presentation history. Test inventory depletion, stale data and reset.

**Current acceptance:** not independently approved; no historical result inherited.

#### SYN-TEST-008

**Requirements:** SYN-REQ-008.

**Procedure:** test_synoptic.SynopticTests.test_actual_lvgl_modes_responsive_touch_and_stale; python3 tools/verify_synoptic.py --output <new-report.json>

**Expected:** A reduced-motion toggle shall freeze decorative motion without hiding numerical values, route, status or progress. Motion limits shall be visible and documented. Verify freeze and continued value updates.

**Current acceptance:** not independently approved; no historical result inherited.

#### SYN-TEST-009

**Requirements:** SYN-REQ-009.

**Procedure:** test_synoptic.SynopticTests.test_actual_lvgl_modes_responsive_touch_and_stale; test_synoptic.SynopticTests.test_post_tracer_enters_venous_chamber_before_return; python3 tools/verify_synoptic.py --output <new-report.json>

**Expected:** Dialysate outlet and bypass shall remain outside the venous chamber and lead to effluent. POST substitution shall enter a dedicated venous-chamber inlet; PRE enters before the filter. Blood enters above and leaves below. Non-joining crossings shall have visible clearance.

**Current acceptance:** not independently approved; no historical result inherited.

#### SYN-TEST-010

**Requirements:** SYN-REQ-010.

**Procedure:** test_synoptic.SynopticTests.test_actual_lvgl_modes_responsive_touch_and_stale; test_synoptic.SynopticTests.test_sdl_resize_finger_input_and_focus_cancellation; test_synoptic.SynopticTests.test_motion_freshness_routes_and_inventory; python3 tools/verify_synoptic.py --output <new-report.json>

**Expected:** Home shall prioritize the filter and extracorporeal flow with a simplified overview, animated fluid-direction cues and measured acid/bicarbonate liquid, dialysate feed, drain, membrane UF and substitution quantities in mL/min. Mechanical roller motion, tanks and full valve plumbing shall be confined to the Blood circuit and Hydraulics tabs. PRE/POST destination, bypass, zero/unknown flow, freshness and reduced motion remain explicit. Test distinct render modes, actual tab events, source-to-value mapping and simplified topology at all three fixture sizes.

**Current acceptance:** not independently approved; no historical result inherited.

### Complete browser execution

#### WEB-TEST-001

**Requirements:** WEB-REQ-001.

**Procedure:** test_browser.BrowserRuntimeTests.test_full_wasm_portability; DIALYSISLAB_BROWSER_ACCEPTANCE=<new-directory> python3 -m unittest discover -s tests -p test_browser.py -v

**Expected:** Run production C++ Plant, control/protection decisions and existing Python patient/physical coupling locally using WebAssembly and Pyodide. HD/PRE/POST must reach treatment with finite results and conserved water/solute inventories; no replacement physical equations or prerecorded telemetry.

**Current acceptance:** not independently approved; no historical result inherited.

#### WEB-TEST-002

**Requirements:** WEB-REQ-002.

**Procedure:** test_browser.BrowserRuntimeTests.test_real_browser_ui; DIALYSISLAB_BROWSER_ACCEPTANCE=<new-directory> python3 -m unittest discover -s tests -p test_browser.py -v

**Expected:** Render existing LVGL guided views in a browser canvas with touch/pointer input and working lifecycle actions, prescription, STOP, detail tabs and reduced motion. Keep simulation time independent of animation frame rate.

**Current acceptance:** not independently approved; no historical result inherited.

#### WEB-TEST-003

**Requirements:** WEB-REQ-003.

**Procedure:** test_browser.BrowserRuntimeTests.test_full_wasm_portability; DIALYSISLAB_BROWSER_ACCEPTANCE=<new-directory> python3 -m unittest discover -s tests -p test_browser.py -v

**Expected:** Compare the same deterministic scenarios/commands and initial conditions in native and WebAssembly execution. Discrete stages/alarms must match exactly; finite numeric outputs use abs(a-b) <= 1e-8 + 1e-9*max(abs(a),abs(b)), in each field's documented units. Water and solute conservation retain existing 1e-6 mL/mmol bounds. These are proposed portability budgets, not global numerical accuracy approval.

**Current acceptance:** not independently approved; no historical result inherited.

#### WEB-TEST-004

**Requirements:** WEB-REQ-004.

**Procedure:** test_browser.BrowserRuntimeTests.test_real_browser_ui; DIALYSISLAB_BROWSER_ACCEPTANCE=<new-directory> python3 -m unittest discover -s tests -p test_browser.py -v

**Expected:** Serve static assets only; computation and patient state stay in the browser. Pause when hidden, do not catch up elapsed wall time, prevent overlapping ticks; stop advancing after runtime failure and report unavailable state. Reset must discard queued actions and old patient state.

**Current acceptance:** not independently approved; no historical result inherited.

#### WEB-TEST-005

**Requirements:** WEB-REQ-005.

**Procedure:** test_browser.BrowserRuntimeTests.test_full_wasm_portability; DIALYSISLAB_BROWSER_ACCEPTANCE=<new-directory> python3 -m unittest discover -s tests -p test_browser.py -v

**Expected:** Pin toolchain/runtime dependencies, preserve source/configuration identifiers, build instructions and native/Wasm comparison results. Published build must identify its source and dependency artifacts.

**Current acceptance:** not independently approved; no historical result inherited.

#### WEB-TEST-006

**Requirements:** WEB-REQ-006.

**Procedure:** test_browser.BrowserRuntimeTests.test_delayed_manual_prime; tools/verify_browser.py --manual-delay-ticks 2400; live browser manual PRIME

**Expected:** Interactive sessions must permit delayed manual PRIME beyond the batch tick limit, preserving physical time and protection behavior; bounded sessions retain their limit and export identifies the profile.

**Current acceptance:** not independently approved; no historical result inherited.

#### WEB-TEST-007

**Requirements:** WEB-REQ-007.

**Procedure:** test_mobile.MobileTests.test_lvgl_phone_layout

**Expected:** Reflow the production LVGL guided interface for phone and landscape widths with readable controls, retained actions, scrolling and resize confirmation cancellation.

**Current acceptance:** not independently approved; no historical result inherited.

#### WEB-TEST-008

**Requirements:** WEB-REQ-008.

**Procedure:** test_mobile.MobileTests.test_fluid_quality_and_identity

**Expected:** Show arterial red, venous blue and fresh dialysate quality green only for all three valid in-range measurements; orange for known out-of-range and neutral for incomplete quality.

**Current acceptance:** not independently approved; no historical result inherited.

### Experiments and inspection

#### M7-TEST-001

**Requirements:** M7-REQ-001.

**Procedure:** Execute real broker/role/widget/native/Compose regressions; retain commands, identities, artifacts and the single phase review.

**Expected:** Actual native/headless/X11/Compose services and widgets

**Current acceptance:** not independently approved; no historical result inherited.

#### M7-TEST-002

**Requirements:** M7-REQ-002.

**Procedure:** Execute real broker/role/widget/native/Compose regressions; retain commands, identities, artifacts and the single phase review.

**Expected:** Patient/circuit/dialyzer/mode/workflow/fault edits validated; live configuration unchanged

**Current acceptance:** not independently approved; no historical result inherited.

#### M7-TEST-003

**Requirements:** M7-REQ-003.

**Procedure:** Execute real broker/role/widget/native/Compose regressions; retain commands, identities, artifacts and the single phase review.

**Expected:** Pause >2 wall seconds preserves sequence/liveness; stop records actual HALT observation

**Current acceptance:** not independently approved; no historical result inherited.

#### M7-TEST-004

**Requirements:** M7-REQ-004.

**Procedure:** Execute real broker/role/widget/native/Compose regressions; retain commands, identities, artifacts and the single phase review.

**Expected:** Fresh services reproduce exact bytes; streaming comparison/export rejects corrupt evidence

**Current acceptance:** not independently approved; no historical result inherited.

#### M7-TEST-005

**Requirements:** M7-REQ-005.

**Procedure:** Execute real broker/role/widget/native/Compose regressions; retain commands, identities, artifacts and the single phase review.

**Expected:** Bad token/revision/run/path/size rejected; device has no truth administration

**Current acceptance:** not independently approved; no historical result inherited.

#### M7-TEST-006

**Requirements:** M7-REQ-006.

**Procedure:** Execute real broker/role/widget/native/Compose regressions; retain commands, identities, artifacts and the single phase review.

**Expected:** Multiple Compose/native runs without Docker socket; interrupted artifacts retained, no implicit resume

**Current acceptance:** not independently approved; no historical result inherited.

### Security, dependencies and integration

#### M8-TEST-001

**Requirements:** M8-REQ-001.

**Procedure:** Execute M8 real process/container/analysis/CI tests and preserve exact source/configuration/command/results.

**Expected:** Actual role spoofing denied; device clients retain authorized access

**Current acceptance:** not independently approved; no historical result inherited.

#### M8-TEST-002

**Requirements:** M8-REQ-002.

**Procedure:** Execute M8 real process/container/analysis/CI tests and preserve exact source/configuration/command/results.

**Expected:** Real owner SIGKILL ends children, preserves partial records and does not invent observed zero

**Current acceptance:** not independently approved; no historical result inherited.

#### M8-TEST-003

**Requirements:** M8-REQ-003.

**Procedure:** Execute M8 real process/container/analysis/CI tests and preserve exact source/configuration/command/results.

**Expected:** Duplicate/deep/oversized/trickle inputs rejected; watchdog/protection remain effective

**Current acceptance:** not independently approved; no historical result inherited.

#### M8-TEST-004

**Requirements:** M8-REQ-004.

**Procedure:** Execute M8 real process/container/analysis/CI tests and preserve exact source/configuration/command/results.

**Expected:** Reproducible versioned SBOM, license/pin/notice checks and identified platform packages

**Current acceptance:** not independently approved; no historical result inherited.

#### M8-TEST-005

**Requirements:** M8-REQ-005.

**Procedure:** Execute M8 real process/container/analysis/CI tests and preserve exact source/configuration/command/results.

**Expected:** Actual static/advisory reports identify commands, findings, coverage and blocks

**Current acceptance:** not independently approved; no historical result inherited.

#### M8-TEST-006

**Requirements:** M8-REQ-006.

**Procedure:** Execute M8 real process/container/analysis/CI tests and preserve exact source/configuration/command/results.

**Expected:** Real builds/processes/widgets/Compose and assurance/publication CI with retained outcomes

**Current acceptance:** not independently approved; no historical result inherited.

#### M9-TEST-001

**Requirements:** M9-REQ-001.

**Procedure:** Execute the predeclared M9 integration/package matrix and retain actual identified artifacts.

**Expected:** 18 configurations twice natively/twice Compose; exact replay, complete lifecycle and independent water/species conservation <=1e-6

**Current acceptance:** not independently approved; no historical result inherited.

#### M9-TEST-002

**Requirements:** M9-REQ-002.

**Procedure:** Execute the predeclared M9 integration/package matrix and retain actual identified artifacts.

**Expected:** Two native/two Compose100000-tick HDF runs; >99000 treatment ticks, grossUF>100000mL, RSS<=64MiB/no OOM at128MiB

**Current acceptance:** not independently approved; no historical result inherited.

#### M9-TEST-003

**Requirements:** M9-REQ-003.

**Procedure:** Execute the predeclared M9 integration/package matrix and retain actual identified artifacts.

**Expected:** Actual widget pause/replay/STOP/cancellation/state/epoch/isolation tests, headless and WSLg

**Current acceptance:** not independently approved; no historical result inherited.

#### M9-TEST-004

**Requirements:** M9-REQ-004.

**Procedure:** Execute the predeclared M9 integration/package matrix and retain actual identified artifacts.

**Expected:** Identical allowlisted archives and real build/tests/widgets from extracted sources

**Current acceptance:** not independently approved; no historical result inherited.

#### M9-TEST-005

**Requirements:** M9-REQ-005.

**Procedure:** Execute the predeclared M9 integration/package matrix and retain actual identified artifacts.

**Expected:** Identified actual CI recovery, commands, model limits, trace links and unchanged open release obligations

**Current acceptance:** not independently approved; no historical result inherited.

## Concrete Python test entry points

Run from repository root after building the required profile. `PYTHONPATH=python:tools:tests`
makes the listed module/class/method selectable with `python3 -m unittest -v`.
Inspect each fixture for process, display and Docker prerequisites; report skipped cases.

### [tests/test_audit_closure.py](../../tests/test_audit_closure.py)

- `test_audit_closure.AuditClosureTests.test_complete_guided_state_guard_endpoint_and_hazard_mask_matrices`
- `test_audit_closure.AuditClosureTests.test_dynamic_initial_volume_bounds_match_actual_plant_and_patient`
- `test_audit_closure.AuditClosureTests.test_all_single_and_pair_hazards_defeat_hostile_control_in_active_phases`
- `test_audit_closure.AuditClosureTests.test_each_freshness_fault_per_role_on_current_guided_model`
- `test_audit_closure.GuidedPresetTests.test_catalog_default_and_loading_validate_complete_scheduled_guided_profiles`
- `test_audit_closure.GuidedPresetTests.test_distributed_long_fixture_is_valid_and_has_no_early_return`
- `test_audit_closure.GuidedPresetTests.test_dynamic_resource_retention_keeps_failed_run_evidence`

### [tests/test_browser.py](../../tests/test_browser.py)

- `test_browser.BrowserRuntimeTests.test_native_tick_stop_and_old_session`
- `test_browser.BrowserRuntimeTests.test_bad_sequence_stops_session_and_rejects_further_ticks`
- `test_browser.BrowserRuntimeTests.test_delayed_manual_prime`
- `test_browser.BrowserRuntimeTests.test_bounded_session_retains_tick_limit`
- `test_browser.BrowserRuntimeTests.test_full_wasm_portability`
- `test_browser.BrowserRuntimeTests.test_real_browser_ui`

### [tests/test_ci.py](../../tests/test_ci.py)

- `test_ci.CITests.test_actual_manifest_drift_stops_before_build`
- `test_ci.CITests.test_actual_stale_workflow_stops_ci_and_retains_diagnostic`
- `test_ci.CITests.test_failed_dependency_preflight_stops_before_download_build_and_tests`
- `test_ci.CITests.test_release_checker_crash_and_timeout_fail_actual_orchestration`
- `test_ci.CITests.test_only_valid_outstanding_release_obligations_are_exempt`
- `test_ci.CITests.test_exact_byte_retention_includes_every_sbom_and_platform_file`
- `test_ci.CITests.test_corruption_order_truncation_and_path_escape_are_rejected`

### [tests/test_ci_lifecycle.py](../../tests/test_ci_lifecycle.py)

- `test_ci_lifecycle.ShortLifecycleTests.test_exact_scheduled_ten_minute_cycle_repeats_with_progress_enabled`
- `test_ci_lifecycle.ShortLifecycleTests.test_progress_is_atomic_diagnostic_and_retained_on_failure`
- `test_ci_lifecycle.ShortLifecycleTests.test_live_command_preserves_failure_and_timeout_output`
- `test_ci_lifecycle.HostedRunnerProgressTests.test_real_runner_progress_and_aborted_prefix`

### [tests/test_circuit.py](../../tests/test_circuit.py)

- `test_circuit.CircuitTests.test_rc_solution_and_step_halving`
- `test_circuit.CircuitTests.test_branch_resistance_clamps_and_steady_flow`
- `test_circuit.CircuitTests.test_water_balance_independent_decimal_ledger`
- `test_circuit.CircuitTests.test_transport_oracle_profiles_equilibrium_and_no_flow`
- `test_circuit.CircuitTests.test_occlusion_observation_bound_and_isolated_storage`
- `test_circuit.CircuitTests.test_sensor_fault_and_repeatability`
- `test_circuit.CircuitTests.test_config_rejection_and_admin_authority`
- `test_circuit.CircuitTests.test_lost_step_reply_preserves_circuit_storage_and_cancels_tick`
- `test_circuit.CircuitTests.test_watchdog_after_commit_preserves_atomic_water_snapshot`
- `test_circuit.CircuitTests.test_volume_ceiling_drainage_and_explicit_roundoff_budget`
- `test_circuit.CircuitTests.test_evidence_rejects_wrong_configuration_digest_and_stale_build`

### [tests/test_compartments.py](../../tests/test_compartments.py)

- `test_compartments.CompartmentNumerics.test_concentration_ceiling_roundoff_retains_mass_without_clipping`
- `test_compartments.CompartmentNumerics.test_subnormal_bicarbonate_and_prospective_response_atomicity`
- `test_compartments.CompartmentNumerics.test_100000_steps_rss_and_mass_ledger`
- `test_compartments.CompartmentNumerics.test_two_compartment_analytic_transient_and_convergence`
- `test_compartments.CompartmentNumerics.test_equilibrium_zero_mass_and_acid_base_indicator`
- `test_compartments.CompartmentNumerics.test_external_inputs_generation_outputs_and_weight`
- `test_compartments.CompartmentNumerics.test_random_transfers_conserve_each_species_without_negative_mass`
- `test_compartments.CompartmentNumerics.test_rejected_transaction_is_atomic_and_inputs_are_bounded`
- `test_compartments.CoupledProcesses.test_oversized_json_integers_reject_without_killing_service`
- `test_compartments.CoupledProcesses.test_equilibrium_ceiling_crosses_the_real_transport_boundary`
- `test_compartments.CoupledProcesses.test_evidence_rejects_inconsistent_water_and_nonfinite_mass`
- `test_compartments.CoupledProcesses.test_synthetic_scenarios_mass_water_and_profile_effect`
- `test_compartments.CoupledProcesses.test_repeatability_and_real_patient_failure`
- `test_compartments.CoupledProcesses.test_sensor_failure_stops_device_without_freezing_body_exchange`

### [tests/test_compose_collection.py](../../tests/test_compose_collection.py)

- `test_compose_collection.ComposeCollectionTests.test_aborted_runner_artifacts_collected_before_volume_removal`
- `test_compose_collection.ComposeCollectionTests.test_failure_before_runner_start_preserves_original_code`
- `test_compose_collection.ComposeCollectionTests.test_failed_extraction_keeps_volume_and_recovery_commands`
- `test_compose_collection.ComposeCollectionTests.test_collection_failure_after_success_has_separate_error`
- `test_compose_collection.ComposeCollectionTests.test_cleanup_failure_does_not_replace_original_exit_code`

### [tests/test_dependencies.py](../../tests/test_dependencies.py)

- `test_dependencies.DependencyTests.test_check_only_needs_no_build_and_still_rejects_unreviewed_workflow`
- `test_dependencies.DependencyTests.test_container_sbom_uses_actual_image_binary_and_runtime_identities`
- `test_dependencies.DependencyTests.test_inventory_rejects_changed_pins_notices_and_ci_actions`
- `test_dependencies.DependencyTests.test_sbom_reproducible_and_actual_binary_hashes`
- `test_dependencies.DependencyTests.test_roboto_license_and_dependencies_follow_each_gui_binary`
- `test_dependencies.DependencyTests.test_advisory_pagination_preserves_all_findings`
- `test_dependencies.DependencyTests.test_advisory_errors_and_repeated_pages_are_blocked`

### [tests/test_device_sessions.py](../../tests/test_device_sessions.py)

- `test_device_sessions.DeviceSessionTests.test_device_roles_and_old_sessions_do_not_mutate_plant`
- `test_device_sessions.DeviceSessionTests.test_restart_reusing_intent_number_cannot_accept_old_confirmation`
- `test_device_sessions.WallPacingTests.test_slow_wall_pacing_keeps_heartbeat_and_identical_virtual_records`

### [tests/test_document_contracts.py](../../tests/test_document_contracts.py)

- `test_document_contracts.ContractRegisterTests.test_missing_method_cannot_be_accepted_as_coverage`
- `test_document_contracts.ContractRegisterTests.test_source_edit_requires_contract_review`
- `test_document_contracts.ContractRegisterTests.test_unknown_parent_cannot_disappear_from_trace`
- `test_document_contracts.ContractRegisterTests.test_bad_wire_bounds_and_duplicate_fields_are_rejected`
- `test_document_contracts.ContractRegisterTests.test_unallocated_parent_and_partial_scope_remain_visible`
- `test_document_contracts.WireWitnessTests.test_actual_cpp_serializers_match_documented_positions_and_python_decoders`
- `test_document_contracts.WireWitnessTests.test_concentrate_drive_is_distinct_from_dry_liquid_and_legacy_is_absent`
- `test_document_contracts.WireWitnessTests.test_python_configuration_encoder_matches_documented_field_order`
- `test_document_contracts.WireWitnessTests.test_cpp_python_reject_every_documented_numeric_boundary_violation`
- `test_document_contracts.WireWitnessTests.test_all_current_configuration_fields_reject_outside_bounds_in_actual_plant`

### [tests/test_documentation.py](../../tests/test_documentation.py)

- `test_documentation.DocumentationTests.test_historical_pass_does_not_become_current_acceptance`
- `test_documentation.DocumentationTests.test_last_requirement_edit_invalidates_generated_candidate`
- `test_documentation.DocumentationTests.test_missing_and_outside_root_links_are_rejected`
- `test_documentation.DocumentationTests.test_current_report_selection_preserves_history_and_rejects_drift`
- `test_documentation.DocumentationTests.test_unallocated_or_duplicate_requirements_cannot_disappear`

### [tests/test_dynamics.py](../../tests/test_dynamics.py)

- `test_dynamics.DynamicsTests.test_gas_pumps_balancing_and_independent_level_protection`
- `test_dynamics.DynamicsTests.test_reference_holdout_and_discretization_are_reported`
- `test_dynamics.DynamicsTests.test_distributed_transit_delay_conservation_and_atomic_rejection`

### [tests/test_experiments.py](../../tests/test_experiments.py)

- `test_experiments.ExperimentTests.test_discovered_guided_presets_launch_real_scheduled_services`
- `test_experiments.ExperimentTests.test_pause_liveness_immutable_configuration_exact_replay_compare_export`
- `test_experiments.ExperimentTests.test_external_stop_while_paused_aborts_without_resume_or_another_tick`
- `test_experiments.ExperimentTests.test_broker_stop_retains_partial_manifest_and_fresh_run_succeeds`
- `test_experiments.ExperimentTests.test_authentication_limits_paths_and_compare_reject_tampering`
- `test_experiments.ExperimentTests.test_duplicate_start_ids_are_idempotent_and_stale_run_controls_fail`
- `test_experiments.ExperimentTests.test_failed_service_keeps_fault_manifest_and_restart_never_resumes`
- `test_experiments.ExperimentRecoveryTests.test_interrupted_prefix_and_prestart_failure_export_only_available_evidence`
- `test_experiments.ExperimentRecoveryTests.test_patient_circuit_profile_and_fault_calendar_are_actual_accepted_run_inputs`
- `test_experiments.ExperimentRecoveryTests.test_full_frame_deadline_and_configuration_bound_preserve_broker`
- `test_experiments.ExperimentReviewTests.test_stop_reaches_actual_plant_when_journal_write_fails`
- `test_experiments.ExperimentReviewTests.test_shutdown_rejects_new_start_and_replay_before_joining`
- `test_experiments.ExperimentReviewTests.test_incomplete_metadata_does_not_hide_valid_runs_or_lose_files`
- `test_experiments.ExperimentReviewTests.test_slow_artifact_writer_retains_ownership_after_join_timeout`
- `test_experiments.ExperimentReviewTests.test_revisions_cannot_repeat_across_broker_incarnations`
- `test_experiments.ExperimentReviewTests.test_maximum_schedule_persists_replays_compares_and_exports`
- `test_experiments.ExperimentReviewTests.test_journal_limit_does_not_block_terminal_metadata_or_export`
- `test_experiments.ExperimentReviewTests.test_comparison_and_export_reject_every_contradictory_identity`
- `test_experiments.ExperimentReviewTests.test_initial_and_final_manifest_record_external_pacing_without_double_wait`
- `test_experiments.ExperimentReviewTests.test_restarted_inventory_selects_latest_creation_times_not_random_ids`
- `test_experiments.ExperimentReviewTests.test_unauthenticated_header_does_not_disclose_experiment_state`

### [tests/test_flow_refinement.py](../../tests/test_flow_refinement.py)

- `test_flow_refinement.FaceAdvectionTests.test_both_directions_match_closed_two_cell_mass_solution`
- `test_flow_refinement.FaceAdvectionTests.test_random_internal_reversals_conserve_mass_and_preserve_bounds`
- `test_flow_refinement.FaceAdvectionTests.test_external_flow_reversal_remains_rejected_atomically`
- `test_flow_refinement.FlowRefinementTests.test_valve_volume_and_event_times_match_analytic_pulse_train`
- `test_flow_refinement.FlowRefinementTests.test_fine_step_coupled_hd_and_hdf_accept_internal_reversals`

### [tests/test_gui_dependencies.py](../../tests/test_gui_dependencies.py)

- `test_gui_dependencies.GuiDependencyTests.test_verified_archive_does_not_authorize_modified_extracted_sources`
- `test_gui_dependencies.GuiDependencyTests.test_unknown_links_and_traversal_are_not_extracted`

### [tests/test_guided.py](../../tests/test_guided.py)

- `test_guided.GuidedUnitTests.test_configuration_rejects_invalid_duration_and_sensor_position`
- `test_guided.GuidedUnitTests.test_return_salinity_body_gain_and_all_solute_balances`
- `test_guided.GuidedUnitTests.test_guided_machine_protocol_and_actual_lvgl_view`
- `test_guided.GuidedUnitTests.test_in_process_hydraulics_complete_cycle_and_patient_transactions`
- `test_guided.GuidedProcessTests.test_full_guided_cycle_preserves_water_solutes_and_stage_evidence`

### [tests/test_inspection.py](../../tests/test_inspection.py)

- `test_inspection.InspectionTests.test_nested_values_bounds_missing_samples_and_session_resets`
- `test_inspection.InspectionTests.test_recorded_console_is_read_only_and_hold_freezes_samples`
- `test_inspection.InspectionTests.test_history_controls_fit_and_receive_pointer_clicks_with_setup_open`

### [tests/test_integration.py](../../tests/test_integration.py)

- `test_integration.IntegrationTests.test_partial_enospc_report_write_preserves_previous_completed_case`
- `test_integration.IntegrationTests.test_sustained_fixture_reaches_deliverable_gross_uf_without_alarm`
- `test_integration.IntegrationTests.test_generated_compose_fixture_is_readable_under_restrictive_umask`
- `test_integration.IntegrationTests.test_package_without_git_retains_actual_failed_packaging_evidence`
- `test_integration.IntegrationTests.test_integrated_evidence_rejects_consistent_but_wrong_virtual_time`
- `test_integration.IntegrationTests.test_archived_trajectory_restores_original_order_hash_and_existing_readers`
- `test_integration.IntegrationTests.test_wrong_hash_or_existing_archive_preserves_raw_trajectory`

### [tests/test_m1.py](../../tests/test_m1.py)

- `test_m1.M1Configuration.test_reject_configuration_before_execution`
- `test_m1.M1Configuration.test_patient_sequence_and_conservation_long_run`
- `test_m1.M1Processes.test_nominal_conservation_and_build_identity`
- `test_m1.M1Processes.test_same_seed_exact_replay`
- `test_m1.M1Processes.test_zero_and_partial_flow_independent_balance`
- `test_m1.M1Processes.test_occlusion_bound_and_persistent_conflicting_commands`
- `test_m1.M1Processes.test_measurement_invalidity_bound`
- `test_m1.M1Processes.test_control_sensor_fault_is_separate`
- `test_m1.M1Processes.test_protection_acts_when_control_is_killed`
- `test_m1.M1Processes.test_missing_control_or_protection_blocks_commit`
- `test_m1.M1Processes.test_plant_or_patient_loss_aborts_uncommitted_record`
- `test_m1.M1Processes.test_virtual_pause_maintains_liveness_without_integrating`
- `test_m1.M1Processes.test_runner_loss_wall_watchdog_does_not_advance_clock`
- `test_m1.M1Processes.test_role_authority_and_duplicate_tick_rejection`
- `test_m1.M1Processes.test_malformed_frames_fail_closed`

### [tests/test_machine.py](../../tests/test_machine.py)

- `test_machine.MachineTests.test_real_transport_accepts_representable_subnormal_concentrations`
- `test_machine.MachineTests.test_isolated_100000_tick_flush_keeps_body_ceiling_and_conserves_mass`
- `test_machine.MachineTests.test_evidence_cross_checks_alarm_mask_latches_and_every_actuator_class`
- `test_machine.MachineTests.test_quality_detectors_trip_in_their_first_unsafe_observation_cycle`
- `test_machine.MachineTests.test_flush_quality_stops_external_pump_and_missing_decision_is_terminal`
- `test_machine.MachineTests.test_confirmation_expires_in_wall_time_without_advancing_physics`
- `test_machine.MachineTests.test_hd_pre_post_lifecycle_flush_and_independent_balances`
- `test_machine.MachineTests.test_illegal_transition_matrix_preserves_actual_state`
- `test_machine.MachineTests.test_readiness_and_priming_cannot_be_bypassed_through_recovery`
- `test_machine.MachineTests.test_each_detector_observation_bound_and_specific_actuator_action`
- `test_machine.MachineTests.test_simultaneous_hazards_apply_before_commit_and_defeat_hostile_control`
- `test_machine.MachineTests.test_ack_silence_expiration_new_alarm_and_override_never_reset`
- `test_machine.MachineTests.test_reset_needs_three_safe_cycles_and_never_resumes_automatically`
- `test_machine.MachineTests.test_unproven_low_flow_filter_and_retained_pressure_do_not_reset`
- `test_machine.MachineTests.test_latent_stuck_air_detector_is_an_explicit_detection_gap`
- `test_machine.MachineTests.test_device_authority_confirmation_prescription_and_stop`
- `test_machine.MachineTests.test_lost_step_each_role_stops_and_invalidates_pending_m5_decisions`
- `test_machine.MachineTests.test_control_and_protection_loss_restart_cannot_clear_latches`
- `test_machine.MachineTests.test_m5_wall_watchdog_terminal_state_and_observation_remain_separate`
- `test_machine.MachineTests.test_evidence_rejects_forged_flush_water_and_solute`
- `test_machine.MachineTests.test_configuration_bounds_and_exact_replay`

### [tests/test_mobile.py](../../tests/test_mobile.py)

- `test_mobile.MobileTests.test_fluid_quality_and_identity`
- `test_mobile.MobileTests.test_lvgl_phone_layout`
- `test_mobile.MobileTests.test_sdl_mobile_window_dimensions`

### [tests/test_physical.py](../../tests/test_physical.py)

- `test_physical.PhysicalTests.test_equations_and_limits`
- `test_physical.PhysicalTests.test_initial_hematocrit_and_geometry_are_configuration_only`
- `test_physical.PhysicalTests.test_uf_hemoconcentration_refill_and_rbc_conservation`
- `test_physical.PhysicalTests.test_in_process_physical_treatments`
- `test_physical.PhysicalProcessTests.test_real_services_and_retained_evidence`

### [tests/test_preparation.py](../../tests/test_preparation.py)

- `test_preparation.PreparationTests.test_line_air_water_and_concentrate_displacement`
- `test_preparation.PreparationTests.test_distinct_pump_displacement_pressure_and_air_efficiency`
- `test_preparation.PreparationTests.test_cartridge_liquid_gas_and_solute_storage`
- `test_preparation.PreparationTests.test_saturation_and_finite_dissolution_with_solid_remaining`
- `test_preparation.PreparationTests.test_solid_exhaustion_preserves_dissolved_washout`
- `test_preparation.PreparationTests.test_mixed_tank_matches_independent_exponential`
- `test_preparation.PreparationTests.test_startup_all_occupancies_and_independent_balances`
- `test_preparation.PreparationTests.test_acid_concentration_step_and_bag_depletion`
- `test_preparation.PreparationTests.test_delayed_stale_invalid_sensors_and_control_input_boundary`
- `test_preparation.PreparationTests.test_pi_saturation_antiwindup_and_invalid_freeze`
- `test_preparation.PreparationTests.test_compensating_errors_and_continuous_dwell`
- `test_preparation.PreparationTests.test_pressure_stop_and_bounded_startup_failures`
- `test_preparation.PreparationTests.test_time_refinement_against_predeclared_budget`
- `test_preparation.PreparationTests.test_eight_hours_depletion_and_boundary_balances`
- `test_preparation.PreparationTests.test_actual_hd_pre_post_startup_and_complete_patient_cycles`
- `test_preparation.PreparationTests.test_final_authority_blocks_unqualified_fluid_despite_forged_permits`
- `test_preparation.PreparationTests.test_configuration_and_wire_reject_malformed_inputs`
- `test_preparation.PreparationTests.test_evidence_identity_changes_with_source_and_configuration`

### [tests/test_publication.py](../../tests/test_publication.py)

- `test_publication.PublicationChecks.test_source_and_build_formats`
- `test_publication.PublicationChecks.test_reject_binary_source_and_restricted_format`
- `test_publication.PublicationChecks.test_paths_symlinks_and_duplicates`
- `test_publication.PublicationChecks.test_actual_context_is_explicit_reviewed_subset`
- `test_publication.PublicationChecks.test_context_rejects_broad_inclusion`
- `test_publication.OwnedCaptureChecks.test_only_registered_encoder_profile_with_matching_digest_is_allowed`
- `test_publication.OwnedDiagramChecks.test_passive_diagram_and_ownership`
- `test_publication.OwnedDiagramChecks.test_reject_active_external_or_unexpected_content`
- `test_publication.OwnedDiagramChecks.test_registered_svg_is_packaged_and_restricted_hash_still_rejected`

### [tests/test_rpc_abort.py](../../tests/test_rpc_abort.py)

- `test_rpc_abort.RpcAbortTests.test_control_step_reply_lost_after_plant_acceptance`
- `test_rpc_abort.RpcAbortTests.test_protection_step_reply_lost_after_plant_acceptance`
- `test_rpc_abort.RpcAbortTests.test_halt_not_delivered_reports_observed_running_outputs`
- `test_rpc_abort.RpcAbortTests.test_halt_reply_lost_keeps_acknowledgment_distinct_from_observation`
- `test_rpc_abort.RpcAbortTests.test_halt_and_status_failures_leave_output_state_unknown`
- `test_rpc_abort.RpcAbortTests.test_halt_acknowledgment_is_not_an_output_observation`

### [tests/test_security.py](../../tests/test_security.py)

- `test_security.SecurityTests.test_disappearing_proc_stat_is_terminated_but_access_errors_are_not_hidden`
- `test_security.SecurityTests.test_strict_json_rejects_ambiguous_and_unbounded_inputs`
- `test_security.SecurityTests.test_patient_rejects_duplicate_or_deep_json_and_survives`
- `test_security.SecurityTests.test_broker_bad_frames_do_not_change_draft_or_disclose_credentials`
- `test_security.SecurityTests.test_broker_four_slow_clients_are_bounded_and_recover`
- `test_security.SecurityTests.test_partial_device_request_cannot_extend_plant_liveness`
- `test_security.SecurityTests.test_killed_broker_terminates_actual_children_preserves_unknown_stop`

### [tests/test_synoptic.py](../../tests/test_synoptic.py)

- `test_synoptic.SynopticTests.test_post_tracer_enters_venous_chamber_before_return`
- `test_synoptic.SynopticTests.test_motion_freshness_routes_and_inventory`
- `test_synoptic.SynopticTests.test_actual_lvgl_modes_responsive_touch_and_stale`
- `test_synoptic.SynopticTests.test_sdl_resize_finger_input_and_focus_cancellation`

### [tests/test_traceability.py](../../tests/test_traceability.py)

- `test_traceability.TraceChecks.test_complete_synthetic_graph`
- `test_traceability.TraceChecks.test_draft_cannot_pass_release`
- `test_traceability.TraceChecks.test_pass_without_evidence_is_error`
- `test_traceability.TraceChecks.test_tampered_evidence`
- `test_traceability.TraceChecks.test_wrong_baseline`
- `test_traceability.TraceChecks.test_broken_bidirectional_link`
- `test_traceability.TraceChecks.test_unknown_reference`
- `test_traceability.TraceChecks.test_orphan_hazard`
- `test_traceability.TraceChecks.test_outside_root_artifact`
- `test_traceability.TraceChecks.test_duplicate_id`
- `test_traceability.TraceChecks.test_open_prerequisite`
- `test_traceability.TraceChecks.test_planned_test_is_not_pass`

### [tests/test_trajectory.py](../../tests/test_trajectory.py)

- `test_trajectory.TrajectoryTests.test_rss_measurement_does_not_inherit_parent_address_space`
- `test_trajectory.TrajectoryTests.test_100000_records_rss_order_repeatability_and_hash`
- `test_trajectory.TrajectoryTests.test_short_writes_hash_exactly_the_written_bytes`
- `test_trajectory.TrajectoryTests.test_recovery_discards_only_an_incomplete_final_line`
- `test_trajectory.TrajectoryTests.test_killed_real_runner_retains_complete_written_prefix`

### [tests/test_treatment.py](../../tests/test_treatment.py)

- `test_treatment.TreatmentTests.test_quality_command_isolates_live_fluids_before_any_commit`
- `test_treatment.TreatmentTests.test_computed_mixture_ceiling_passes_patient_boundary`
- `test_treatment.TreatmentTests.test_replacement_head_can_exceed_blood_pump_head`
- `test_treatment.TreatmentTests.test_state4_versions_cumulative_gross_uf_and_stop_decoding`
- `test_treatment.TreatmentTests.test_evidence_rejects_forged_replacement_rates_and_solute_ledger`
- `test_treatment.TreatmentTests.test_modes_independent_gross_net_water_and_solutes`
- `test_treatment.TreatmentTests.test_reservoir_analytic_mixing_temperature_and_filter_hydraulics`
- `test_treatment.TreatmentTests.test_reservoir_first_order_convergence`
- `test_treatment.TreatmentTests.test_quality_faults_observation_bound_and_blood_specific_action`
- `test_treatment.TreatmentTests.test_quality_latch_cannot_be_overridden_by_conflicting_control`
- `test_treatment.TreatmentTests.test_hidden_contamination_is_not_a_protective_sensor`
- `test_treatment.TreatmentTests.test_hard_pressure_and_invalid_sensor_stop_all_treatment_outputs`
- `test_treatment.TreatmentTests.test_step_loss_halts_all_three_outputs_and_pending_tick`
- `test_treatment.TreatmentTests.test_patient_replacement_ledger_and_atomic_rejection`
- `test_treatment.TreatmentTests.test_reproducibility_and_configuration_rejection`
