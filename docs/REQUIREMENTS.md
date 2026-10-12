# Software requirements specification

Document ID SRS-01; revision controlled by Git. Status: review candidate; no independent approval recorded.

Read next: [Architecture](ARCHITECTURE.md). Definitions: [Glossary](GLOSSARY.md).

## Intended use and users

DialysisLab is an open-source simulation and software-development reference for engineers,
researchers and educators. It operates only simulated equipment and patients. It supports
intermittent HD and HDF PRE/POST, including modeled online substitution preparation.
It is not intended to prescribe or deliver treatment to people. EU is the first target
for future lifecycle adaptation; this is not a medical-device classification decision.

The device operator controls treatment; the experiment user configures patient, equipment,
faults and time. Patient configuration remains outside the device UI. C++17 implements
equipment/control/protection and graphical clients; Python 3.9+ implements the patient
and experiment runtime. Linux and WSL2 are supported development targets. Application
dependencies prefer MIT, BSD, Apache-2.0 or zlib; exceptions need explicit review.

## Reading and acceptance rules

Requirements are grouped by function. Existing IDs remain stable for traceability; an M
prefix is not the reading order. Statements and acceptance text below are generated
from the maintained register without silently rewriting obligations. Some obligations
remain too broad or need justified numerical criteria; the current audit identifies them.

**Current verification decision:** implementation is recorded for these requirements,
but requirement-level independent acceptance is not recorded. Historical test passes
are intentionally not carried forward here. Use the current verification record to
assess baseline applicability; consult the separate Project Log only for history.

Simulation bounds and synthetic alarm thresholds are not clinical limits. Supported
legacy scenarios are compatibility requirements, not the current interactive default.
The default is the guided dynamic scenario documented in the design chapters.

## Operational reference

The guided sequence is tests → preparation → priming → connection → therapy → return
→ disconnection → disinfection. Priming and return terminate on measured volume;
therapy on delivered treatment time; disinfection needs both time and volume. Manual
phases wait for confirmation. The detailed guards and progress criteria are in
[Treatment design](design/TREATMENT.md) and [workflow protocol](testing/WORKFLOW.md).

Safety-class assignment, quantitative risk acceptability, independent approval and
validated model operating envelopes remain required decisions, not assumptions.

## System boundaries and protective principles

### REQ-001

Device UI access shall be restricted to permitted machine command and telemetry interfaces.

**Acceptance:** Calls from the device-ui identity to patient/scenario administration are denied; permitted treatment requests remain available.

**Trace:** needs NEED-001; risks HAZ-001; design DES-001; verification TEST-001.

**Implementation locations:** [compose.experiments.yaml](../compose.experiments.yaml), [tools/verify_experiments_compose.py](../tools/verify_experiments_compose.py), [src/ui/client.hpp](../src/ui/client.hpp), [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md), [docs/design/INTERFACES.md](../docs/design/INTERFACES.md), [docs/testing/FAILURES.md](../docs/testing/FAILURES.md).

### REQ-002

Control commands shall not override an active protective constraint at actuator arbitration.

**Acceptance:** For every approved active protection state, all conflicting control commands preserve the specified protective outputs until the approved reset sequence completes.

**Trace:** needs NEED-002; risks HAZ-002; design DES-002; verification TEST-002.

**Implementation locations:** [src/plant.cpp](../src/plant.cpp), [src/machine.hpp](../src/machine.hpp), [tests/test_machine.py](../tests/test_machine.py), [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md), [docs/design/INTERFACES.md](../docs/design/INTERFACES.md), [docs/testing/FAILURES.md](../docs/testing/FAILURES.md).

### REQ-003

Fluid accounting shall separately track gross membrane transfer, substitution, other inputs/outputs and circuit storage.

**Acceptance:** Patient and whole-system fluid-balance residuals stay within independently justified tolerances in HD and both HDF routes, including substitution interruption.

**Trace:** needs NEED-003; risks HAZ-003; design DES-003; verification TEST-003.

**Implementation locations:** [python/dialysislab/compartments.py](../python/dialysislab/compartments.py), [src/circuit.hpp](../src/circuit.hpp), [tools/verify_models.py](../tools/verify_models.py), [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md), [docs/design/INTERFACES.md](../docs/design/INTERFACES.md), [docs/testing/FAILURES.md](../docs/testing/FAILURES.md), [docs/design/MODELS.md](../docs/design/MODELS.md), [docs/testing/MODELS.md](../docs/testing/MODELS.md).

### REQ-004

Protection shall evaluate measurement validity and age and apply the approved hazard-specific response to unusable data.

**Acceptance:** All invalidity/staleness cases trigger the specified response within the allocated detection/action budget; paused virtual time follows its documented semantics.

**Trace:** needs NEED-004; risks HAZ-004; design DES-004; verification TEST-004.

**Implementation locations:** [src/protection.cpp](../src/protection.cpp), [src/wire.hpp](../src/wire.hpp), [tests/test_rpc_abort.py](../tests/test_rpc_abort.py), [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md), [docs/design/INTERFACES.md](../docs/design/INTERFACES.md), [docs/testing/FAILURES.md](../docs/testing/FAILURES.md).

### REQ-005

Alarm acknowledgment or permitted silence shall not by itself clear an active hazardous condition or protective constraint.

**Acceptance:** Each alarm follows its reviewed priority/state/silence/reset specification; a continuing hazard retains the required protective outputs.

**Trace:** needs NEED-005; risks HAZ-005; design DES-005; verification TEST-005.

**Implementation locations:** [src/protection.cpp](../src/protection.cpp), [src/ui/device_ui.cpp](../src/ui/device_ui.cpp), [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md), [docs/design/INTERFACES.md](../docs/design/INTERFACES.md), [docs/testing/FAILURES.md](../docs/testing/FAILURES.md).

### REQ-006

Substitution delivery shall be conditioned on approved preparation and observable integrity criteria.

**Acceptance:** All specified preparation/integrity failures with modeled observable evidence produce the approved response; unobservable failures are identified as detection gaps.

**Trace:** needs NEED-006; risks HAZ-006; design DES-006; verification TEST-006.

**Implementation locations:** [src/online.hpp](../src/online.hpp), [src/protection.cpp](../src/protection.cpp), [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md), [docs/design/INTERFACES.md](../docs/design/INTERFACES.md), [docs/testing/FAILURES.md](../docs/testing/FAILURES.md), [docs/design/MODELS.md](../docs/design/MODELS.md), [docs/testing/MODELS.md](../docs/testing/MODELS.md).

## Execution, failure handling and records

### M1-REQ-001

Build three C++17 services and deploy them with separate Python patient and runner services.

**Acceptance:** CMake builds successfully; Compose runs five isolated services and records source, binary and configuration identities.

**Trace:** needs M1-NEED-001; risks HAZ-001; design M1-DES-001; verification M1-TEST-001.

**Implementation locations:** [src/wire.hpp](../src/wire.hpp), [CMakeLists.txt](../CMakeLists.txt), [compose.yaml](../compose.yaml), [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md), [docs/design/INTERFACES.md](../docs/design/INTERFACES.md), [docs/testing/FAILURES.md](../docs/testing/FAILURES.md).

### M1-REQ-002

Advance simulation solely through contiguous integer virtual ticks and reproduce declared trajectories.

**Acceptance:** Identical configuration and seed yield byte-identical same-build trajectories; cross-build numerics agree within absolute/relative 1e-9; clean same-toolchain CMake builds produce identical executables.

**Trace:** needs M1-NEED-001; risks HAZ-004; design M1-DES-002; verification M1-TEST-002.

**Implementation locations:** [python/dialysislab/runner.py](../python/dialysislab/runner.py), [src/plant.cpp](../src/plant.cpp), [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md), [docs/design/INTERFACES.md](../docs/design/INTERFACES.md), [docs/testing/FAILURES.md](../docs/testing/FAILURES.md).

### M1-REQ-003

Conserve fluid in the limited HD model with separate patient and effluent accounting.

**Acceptance:** Nominal, zero-UF, stopped-flow and partial-flow runs match independent Decimal balances within 1e-8 mL; long patient ledger drift stays below 1e-8 mL.

**Trace:** needs M1-NEED-001; risks HAZ-003; design M1-DES-003; verification M1-TEST-003.

**Implementation locations:** [src/model.hpp](../src/model.hpp), [src/plant.cpp](../src/plant.cpp), [python/dialysislab/patient.py](../python/dialysislab/patient.py), [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md), [docs/design/INTERFACES.md](../docs/design/INTERFACES.md), [docs/testing/FAILURES.md](../docs/testing/FAILURES.md).

### M1-REQ-004

Detect synthetic occlusion and send a protective command directly to plant arbitration.

**Acceptance:** Tick-5 resistance increase produces a measured pressure of 600 mmHg; the synthetic 250 mmHg trip stops blood/UF and closes clamp within one 100 ms virtual interval, including when control has died.

**Trace:** needs M1-NEED-001; risks HAZ-002; design M1-DES-004; verification M1-TEST-004.

**Implementation locations:** [src/protection.cpp](../src/protection.cpp), [src/plant.cpp](../src/plant.cpp), [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md), [docs/design/INTERFACES.md](../docs/design/INTERFACES.md), [docs/testing/FAILURES.md](../docs/testing/FAILURES.md).

### M1-REQ-005

Preserve an active protective latch against conflicting commands and subsequent permits.

**Acceptance:** Repeated 300 mL/min control demand and later PERMIT cannot release latched zero blood/UF and closed clamp; unauthorized role and duplicate tick messages fail closed.

**Trace:** needs M1-NEED-001; risks HAZ-002; design M1-DES-005; verification M1-TEST-005.

**Implementation locations:** [src/plant.cpp](../src/plant.cpp), [src/control.cpp](../src/control.cpp), [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md), [docs/design/INTERFACES.md](../docs/design/INTERFACES.md), [docs/testing/FAILURES.md](../docs/testing/FAILURES.md).

### M1-REQ-006

Validate separate modeled control/protection observations before using them.

**Acceptance:** Invalid, missing, stale, future and replayed protection samples trip within one 100 ms interval; a control-only fault does not corrupt the protection channel.

**Trace:** needs M1-NEED-001; risks HAZ-004; design M1-DES-006; verification M1-TEST-006.

**Implementation locations:** [src/wire.hpp](../src/wire.hpp), [src/control.cpp](../src/control.cpp), [src/protection.cpp](../src/protection.cpp), [src/plant.cpp](../src/plant.cpp), [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md), [docs/design/INTERFACES.md](../docs/design/INTERFACES.md), [docs/testing/FAILURES.md](../docs/testing/FAILURES.md).

### M1-REQ-007

Handle missing processes and distinguish virtual pause from wall-clock liveness.

**Acceptance:** Failed STEP (including lost reply after plant acceptance) sends no COMMIT/ADVANCE; HALT cancels pending decisions and rejects later commits. Abort cause, stop acknowledgment and observed outputs are distinct; failed stop/observation never implies confirmed zero. Plant/patient loss aborts; runner loss trips the wall lease without virtual advancement.

**Trace:** needs M1-NEED-001; risks HAZ-002, HAZ-004; design M1-DES-007; verification M1-TEST-007.

**Implementation locations:** [src/plant.cpp](../src/plant.cpp), [src/wire.hpp](../src/wire.hpp), [python/dialysislab/runner.py](../python/dialysislab/runner.py), [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md), [docs/design/INTERFACES.md](../docs/design/INTERFACES.md), [docs/testing/FAILURES.md](../docs/testing/FAILURES.md).

### M1-REQ-008

Stream and recover all supported 100000-tick trajectory records with bounded memory.

**Acceptance:** Two actual 100000-tick Compose runs complete under 128 MiB with peak runner RSS <=64 MiB. Records are ordered/complete and repeated hashes agree with independently hashed written bytes. SIGKILL preserves a recoverable complete prefix.

**Trace:** needs M1-NEED-001; risks HAZ-003, HAZ-004; design M1-DES-008; verification M1-TEST-008.

**Implementation locations:** [python/dialysislab/trajectory.py](../python/dialysislab/trajectory.py), [python/dialysislab/runner.py](../python/dialysislab/runner.py), [tools/recover_trajectory.py](../tools/recover_trajectory.py), [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md), [docs/design/INTERFACES.md](../docs/design/INTERFACES.md), [docs/testing/FAILURES.md](../docs/testing/FAILURES.md).

### M1-REQ-009

Retain available Compose failure evidence and preserve original error identity.

**Acceptance:** Aborted runner, pre-start failure and failed extraction retain logs/reports; original exit code is preserved. Failed extraction retains volumes and stopped containers with usable recovery commands; verify actual artifact recovery before cleanup.

**Trace:** needs M1-NEED-001; risks HAZ-001; design M1-DES-009; verification M1-TEST-009.

**Implementation locations:** [tools/verify_compose.py](../tools/verify_compose.py), [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md), [docs/design/INTERFACES.md](../docs/design/INTERFACES.md), [docs/testing/FAILURES.md](../docs/testing/FAILURES.md).

## Hydraulics, patient and prepared fluids

### M2-REQ-001

Configurable compliant hydraulic network and measured sensors

**Acceptance:** Analytic RC and resistor solutions, decreasing step-halving errors, clamps and component changes.

**Trace:** needs M2-NEED-001; risks HAZ-002, HAZ-004; design M2-DES-001; verification M2-TEST-001.

**Implementation locations:** [src/circuit.hpp](../src/circuit.hpp), [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md), [docs/design/MODELS.md](../docs/design/MODELS.md), [docs/testing/MODELS.md](../docs/testing/MODELS.md).

### M2-REQ-002

Conserve patient, circuit and effluent water

**Acceptance:** Per-tick residual <=1e-8 mL and cumulative <=1e-6 mL with independent node-volume accounting.

**Trace:** needs M2-NEED-001; risks HAZ-003; design M2-DES-002; verification M2-TEST-002.

**Implementation locations:** [src/circuit.hpp](../src/circuit.hpp), [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md), [docs/design/MODELS.md](../docs/design/MODELS.md), [docs/testing/MODELS.md](../docs/testing/MODELS.md).

### M2-REQ-003

Synthetic dialyzer diffusion, convection and pressure-limited UF

**Acceptance:** Two profiles, independent clearance formula, equilibrium and zero-flow/zero-membrane cases.

**Trace:** needs M2-NEED-001; risks HAZ-003; design M2-DES-003; verification M2-TEST-003.

**Implementation locations:** [src/circuit.hpp](../src/circuit.hpp), [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md), [docs/design/MODELS.md](../docs/design/MODELS.md), [docs/testing/MODELS.md](../docs/testing/MODELS.md).

### M2-REQ-004

Integrate extended circuit without losing independent protection or reproducibility

**Acceptance:** Actual process/Compose runs; repeated hashes; occlusion latch by 1000 ms and lost STEP cancels commit.

**Trace:** needs M2-NEED-001; risks HAZ-001, HAZ-002, HAZ-004; design M2-DES-004; verification M2-TEST-004.

**Implementation locations:** [python/dialysislab/circuit.py](../python/dialysislab/circuit.py), [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md), [docs/design/MODELS.md](../docs/design/MODELS.md), [docs/testing/MODELS.md](../docs/testing/MODELS.md).

### M3-REQ-001

Conservative positive patient compartments and six solute inventories

**Acceptance:** Ordered bounded transactions preserve positive mass and concentration; rejected updates leave the prior state intact.

**Trace:** needs M3-NEED-001; risks HAZ-003, HAZ-004; design M3-DES-001; verification M3-TEST-001.

**Implementation locations:** [python/dialysislab/compartments.py](../python/dialysislab/compartments.py), [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md), [docs/design/MODELS.md](../docs/design/MODELS.md), [docs/testing/MODELS.md](../docs/testing/MODELS.md).

### M3-REQ-002

Independent whole-system water and solute accounting

**Acceptance:** Independent balances <=1e-6 mL/mmol, analytic transient and step-halving tests, 100000-step process RSS below 64 MiB.

**Trace:** needs M3-NEED-001; risks HAZ-003; design M3-DES-002; verification M3-TEST-002.

**Implementation locations:** [python/dialysislab/compartments.py](../python/dialysislab/compartments.py), [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md), [docs/design/MODELS.md](../docs/design/MODELS.md), [docs/testing/MODELS.md](../docs/testing/MODELS.md).

### M3-REQ-003

Distinct gross UF, external fluxes, circuit storage, patient loss and water-only weight

**Acceptance:** Synthetic baseline/overload/imbalance scenarios and independently calculated infusion/generation/excretion cases.

**Trace:** needs M3-NEED-001; risks HAZ-003; design M3-DES-003; verification M3-TEST-003.

**Implementation locations:** [python/dialysislab/compartments.py](../python/dialysislab/compartments.py), [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md), [docs/design/MODELS.md](../docs/design/MODELS.md), [docs/testing/MODELS.md](../docs/testing/MODELS.md).

### M3-REQ-004

Couple real Python patient to atomic C++ circuit coefficients

**Acceptance:** Native and Compose runs repeat, identify exact build/config, enforce protective stops and retain partial transactions on patient failure.

**Trace:** needs M3-NEED-001; risks HAZ-001, HAZ-003, HAZ-004; design M3-DES-004; verification M3-TEST-004.

**Implementation locations:** [python/dialysislab/runner.py](../python/dialysislab/runner.py), [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md), [docs/design/MODELS.md](../docs/design/MODELS.md), [docs/testing/MODELS.md](../docs/testing/MODELS.md).

### M4-REQ-001

Implement explicit HD/pre/post HDF water and solute delivery

**Acceptance:** Independent whole-system balances <=1e-6 mL/mmol; distinct gross UF/substitution/storage/net loss.

**Trace:** needs M4-NEED-001; risks HAZ-003; design M4-DES-001; verification M4-TEST-001.

**Implementation locations:** [python/dialysislab/compartments.py](../python/dialysislab/compartments.py), [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md), [docs/design/MODELS.md](../docs/design/MODELS.md), [docs/testing/MODELS.md](../docs/testing/MODELS.md).

### M4-REQ-002

Model preparation reservoir, thermal and filter/delivery hydraulics

**Acceptance:** Analytic equilibrium/transient, convergence and filter pressure-loss checks.

**Trace:** needs M4-NEED-001; risks HAZ-003, HAZ-006; design M4-DES-002; verification M4-TEST-002.

**Implementation locations:** [src/online.hpp](../src/online.hpp), [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md), [docs/design/MODELS.md](../docs/design/MODELS.md), [docs/testing/MODELS.md](../docs/testing/MODELS.md).

### M4-REQ-003

Enforce observed quality protection at plant arbitration

**Acceptance:** Quality latch within one dt after observable threshold; no delivery/UF/dialysate despite conflicting control.

**Trace:** needs M4-NEED-001; risks HAZ-002, HAZ-004, HAZ-006; design M4-DES-003; verification M4-TEST-003.

**Implementation locations:** [src/plant.cpp](../src/plant.cpp), [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md), [docs/design/MODELS.md](../docs/design/MODELS.md), [docs/testing/MODELS.md](../docs/testing/MODELS.md).

### M4-REQ-004

Verify real treatment processes and deployment evidence

**Acceptance:** Repeat native/Compose modes/faults; exact build/config identity and compatibility regressions.

**Trace:** needs M4-NEED-001; risks HAZ-001, HAZ-003, HAZ-004, HAZ-006; design M4-DES-004; verification M4-TEST-004.

**Implementation locations:** [python/dialysislab/runner.py](../python/dialysislab/runner.py), [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md), [docs/design/MODELS.md](../docs/design/MODELS.md), [docs/testing/MODELS.md](../docs/testing/MODELS.md).

### PHY-REQ-001

Couple patient hematocrit, needle/disposable geometry, local filtration and viscosity to machine pressures, fluid delivery and preparation.

**Acceptance:** Initial hematocrit is scenario-only; RBC/protein/water/solute ledgers conserve to 1e-6. Needle resistance follows diameter^-4. Local forward filtration uses blood/dialysate/oncotic pressures; pre/post routes remain distinct and pump/filtration bounds limit actual outputs. Acid/bicarbonate stocks deplete independently; heater obeys finite power and thermal balance. Telemetry exposes pressures, limits and segment states without device patient-edit controls.

**Trace:** needs M7-NEED-001; risks HAZ-002, HAZ-003, HAZ-004, HAZ-006; design PHY-DES-001; verification PHY-TEST-001, PHY-TEST-002.

**Implementation locations:** [src/blood_physics.hpp](../src/blood_physics.hpp), [src/circuit.hpp](../src/circuit.hpp), [src/online.hpp](../src/online.hpp), [src/machine.hpp](../src/machine.hpp), [src/plant.cpp](../src/plant.cpp), [src/ui/client.hpp](../src/ui/client.hpp), [src/ui/guided.hpp](../src/ui/guided.hpp), [python/dialysislab/physical.py](../python/dialysislab/physical.py), [python/dialysislab/compartments.py](../python/dialysislab/compartments.py), [python/dialysislab/machine.py](../python/dialysislab/machine.py), [python/dialysislab/runner.py](../python/dialysislab/runner.py), [tests/physical_model.cpp](../tests/physical_model.cpp), [tests/test_physical.py](../tests/test_physical.py), [tools/verify_models.py](../tools/verify_models.py), [docs/PHYSICAL_MODEL.md](../docs/PHYSICAL_MODEL.md), [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md), [docs/design/MODELS.md](../docs/design/MODELS.md), [docs/testing/MODELS.md](../docs/testing/MODELS.md).

### DYN-REQ-001

Make chamber levels, dialysate control and blood/dialysate inventories evolve conservatively through the treatment lifecycle.

**Acceptance:** Preserve water, RBC, protein and six-solute inventories across HD/PRE/POST and rinseback. Differentiate pump, access and return flows. Use actual local retained blood properties for hydraulic coupling; expose levels and actuator states with bounded telemetry. Stop outputs on solver nonconvergence. Reference fits must separate fitting and holdout data and label uncalibrated parameters.

**Trace:** needs M7-NEED-001; risks HAZ-002, HAZ-003, HAZ-004, HAZ-006; design DYN-DES-001; verification DYN-TEST-001, DYN-TEST-002, DYN-TEST-003.

**Implementation locations:** [docs/DYNAMIC_MODEL.md](../docs/DYNAMIC_MODEL.md), [docs/GUIDED_TREATMENT.md](../docs/GUIDED_TREATMENT.md), [docs/PHYSICAL_MODEL.md](../docs/PHYSICAL_MODEL.md), [docs/UI_INSPECTION.md](../docs/UI_INSPECTION.md), [docs/images/physical-circuit.svg](../docs/images/physical-circuit.svg), [python/dialysislab/calibration.py](../python/dialysislab/calibration.py), [python/dialysislab/circuit.py](../python/dialysislab/circuit.py), [python/dialysislab/compartments.py](../python/dialysislab/compartments.py), [python/dialysislab/distributed.py](../python/dialysislab/distributed.py), [python/dialysislab/machine.py](../python/dialysislab/machine.py), [python/dialysislab/physical.py](../python/dialysislab/physical.py), [python/dialysislab/protocol.py](../python/dialysislab/protocol.py), [python/dialysislab/runner.py](../python/dialysislab/runner.py), [python/dialysislab/trajectory.py](../python/dialysislab/trajectory.py), [references/dialyzer_benchmarks.json](../references/dialyzer_benchmarks.json), [scenarios/device_guided.json](../scenarios/device_guided.json), [scenarios/physical_hd.json](../scenarios/physical_hd.json), [scenarios/physical_hdf_post.json](../scenarios/physical_hdf_post.json), [scenarios/physical_hdf_pre.json](../scenarios/physical_hdf_pre.json), [src/blood_physics.hpp](../src/blood_physics.hpp), [src/circuit.hpp](../src/circuit.hpp), [src/console/telemetry.hpp](../src/console/telemetry.hpp), [src/dynamics.hpp](../src/dynamics.hpp), [src/machine.hpp](../src/machine.hpp), [src/plant.cpp](../src/plant.cpp), [src/ui/client.hpp](../src/ui/client.hpp), [src/ui/device_ui.cpp](../src/ui/device_ui.cpp), [src/ui/guided.hpp](../src/ui/guided.hpp), [src/ui/synoptic.hpp](../src/ui/synoptic.hpp), [tests/dynamic_model.cpp](../tests/dynamic_model.cpp), [tests/guided_view.cpp](../tests/guided_view.cpp), [tests/test_dynamics.py](../tests/test_dynamics.py), [tests/test_inspection.py](../tests/test_inspection.py), [tests/test_physical.py](../tests/test_physical.py), [tools/calibrate_models.py](../tools/calibrate_models.py), [tools/ci_verify.py](../tools/ci_verify.py), [tools/verify_models.py](../tools/verify_models.py), [tests/test_ci.py](../tests/test_ci.py), [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md), [docs/design/MODELS.md](../docs/design/MODELS.md), [docs/testing/MODELS.md](../docs/testing/MODELS.md).

## Treatment lifecycle and operator interface

### M5-REQ-001

Implement guarded authoritative lifecycle states

**Acceptance:** All required normal and forbidden transitions tested; safe startup/end and requested versus effective state.

**Trace:** needs M5-NEED-001; risks HAZ-002, HAZ-004, HAZ-005; design M5-DES-001; verification M5-TEST-001.

**Implementation locations:** [src/machine.hpp](../src/machine.hpp), [src/plant.cpp](../src/plant.cpp), [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md), [docs/design/TREATMENT.md](../docs/design/TREATMENT.md), [docs/testing/WORKFLOW.md](../docs/testing/WORKFLOW.md).

### M5-REQ-002

Conserve external priming and cleaning transfers

**Acceptance:** Independent water/six-species source/waste balances <=1e-6 mL/mmol; patient isolated during flush.

**Trace:** needs M5-NEED-001; risks HAZ-003, HAZ-006; design M5-DES-002; verification M5-TEST-002.

**Implementation locations:** [python/dialysislab/compartments.py](../python/dialysislab/compartments.py), [python/dialysislab/patient.py](../python/dialysislab/patient.py), [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md), [docs/design/TREATMENT.md](../docs/design/TREATMENT.md), [docs/testing/WORKFLOW.md](../docs/testing/WORKFLOW.md).

### M5-REQ-003

Enforce aggregate hazard-specific protective constraints

**Acceptance:** Pressure/flow/air/leak/quality/balance/validity/comms actions immediate before commit within declared virtual/wall budgets.

**Trace:** needs M5-NEED-001; risks HAZ-002, HAZ-003, HAZ-004, HAZ-006; design M5-DES-003; verification M5-TEST-003.

**Implementation locations:** [src/protection.cpp](../src/protection.cpp), [src/plant.cpp](../src/plant.cpp), [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md), [docs/design/TREATMENT.md](../docs/design/TREATMENT.md), [docs/testing/WORKFLOW.md](../docs/testing/WORKFLOW.md).

### M5-REQ-004

Separate alarm acknowledgment, silence, reset and restart

**Acceptance:** No override; three safe observations in recovery for reset; failures/restarts cannot auto-resume.

**Trace:** needs M5-NEED-001; risks HAZ-002, HAZ-004, HAZ-005; design M5-DES-004; verification M5-TEST-004.

**Implementation locations:** [src/machine.hpp](../src/machine.hpp), [src/protection.cpp](../src/protection.cpp), [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md), [docs/design/TREATMENT.md](../docs/design/TREATMENT.md), [docs/testing/WORKFLOW.md](../docs/testing/WORKFLOW.md).

### M5-REQ-005

Provide isolated device-facing authoritative interfaces

**Acceptance:** Validated requests/confirmations and modeled observations; no UI mount/access to administration or patient truth.

**Trace:** needs M5-NEED-001; risks HAZ-001, HAZ-004, HAZ-005; design M5-DES-005; verification M5-TEST-005.

**Implementation locations:** [src/control.cpp](../src/control.cpp), [python/dialysislab/machine.py](../python/dialysislab/machine.py), [compose.yaml](../compose.yaml), [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md), [docs/design/TREATMENT.md](../docs/design/TREATMENT.md), [docs/testing/WORKFLOW.md](../docs/testing/WORKFLOW.md).

### M5-REQ-006

Verify integrated lifecycle and failure evidence

**Acceptance:** Real native/Compose workflows/faults/restarts/replay, numerical balances and all affected regressions.

**Trace:** needs M5-NEED-001; risks HAZ-001, HAZ-002, HAZ-003, HAZ-004, HAZ-005, HAZ-006; design M5-DES-006; verification M5-TEST-006.

**Implementation locations:** [tests/test_machine.py](../tests/test_machine.py), [tools/verify_models.py](../tools/verify_models.py), [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md), [docs/design/TREATMENT.md](../docs/design/TREATMENT.md), [docs/testing/WORKFLOW.md](../docs/testing/WORKFLOW.md).

### M6-REQ-001

Build the real LVGL device application

**Acceptance:** Native/Compose headless and available graphical rendering against actual services.

**Trace:** needs M6-NEED-001; risks HAZ-004, HAZ-005; design M6-DES-001; verification M6-TEST-001.

**Implementation locations:** [src/ui/device_ui.cpp](../src/ui/device_ui.cpp), [src/ui/client.hpp](../src/ui/client.hpp), [src/device_session.hpp](../src/device_session.hpp), [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md), [docs/design/INTERACTION.md](../docs/design/INTERACTION.md), [docs/testing/WORKFLOW.md](../docs/testing/WORKFLOW.md).

### M6-REQ-002

Validate and confirm simulated prescriptions

**Acceptance:** HD/pre/post setup, visible units/bounds, actual server completion and rejection handling.

**Trace:** needs M6-NEED-001; risks HAZ-002, HAZ-003, HAZ-005; design M6-DES-002; verification M6-TEST-002.

**Implementation locations:** [src/ui/device_ui.cpp](../src/ui/device_ui.cpp), [src/ui/client.hpp](../src/ui/client.hpp), [src/device_session.hpp](../src/device_session.hpp), [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md), [docs/design/INTERACTION.md](../docs/design/INTERACTION.md), [docs/testing/WORKFLOW.md](../docs/testing/WORKFLOW.md).

### M6-REQ-003

Display measured authoritative telemetry and trends

**Acceptance:** Distinct intent/state, UF/sub/net counters, timestamps, invalid/stale/disconnected data; no invented zeros.

**Trace:** needs M6-NEED-001; risks HAZ-003, HAZ-004, HAZ-005; design M6-DES-003; verification M6-TEST-003.

**Implementation locations:** [src/ui/device_ui.cpp](../src/ui/device_ui.cpp), [src/ui/client.hpp](../src/ui/client.hpp), [src/device_session.hpp](../src/device_session.hpp), [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md), [docs/design/INTERACTION.md](../docs/design/INTERACTION.md), [docs/testing/WORKFLOW.md](../docs/testing/WORKFLOW.md).

### M6-REQ-004

Present alarms without bypassing protection

**Acceptance:** Separate ACK/silence/reset, no overrides/admin endpoints, actual device-only mount denial tests.

**Trace:** needs M6-NEED-001; risks HAZ-001, HAZ-002, HAZ-005; design M6-DES-004; verification M6-TEST-004.

**Implementation locations:** [src/ui/device_ui.cpp](../src/ui/device_ui.cpp), [src/ui/client.hpp](../src/ui/client.hpp), [src/device_session.hpp](../src/device_session.hpp), [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md), [docs/design/INTERACTION.md](../docs/design/INTERACTION.md), [docs/testing/WORKFLOW.md](../docs/testing/WORKFLOW.md).

### M6-REQ-005

Make device reconnect and confirmation semantics explicit

**Acceptance:** New session clears pending/trends, rejects old confirmations, no automatic retry of ambiguous critical requests.

**Trace:** needs M6-NEED-001; risks HAZ-001, HAZ-004, HAZ-005; design M6-DES-005; verification M6-TEST-005.

**Implementation locations:** [src/ui/device_ui.cpp](../src/ui/device_ui.cpp), [src/ui/client.hpp](../src/ui/client.hpp), [src/device_session.hpp](../src/device_session.hpp), [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md), [docs/design/INTERACTION.md](../docs/design/INTERACTION.md), [docs/testing/WORKFLOW.md](../docs/testing/WORKFLOW.md).

### M6-REQ-006

Verify actual UI integration and capture evidence

**Acceptance:** Real widgets/RPCs/screenshots, exact build/dependencies/configuration and affected regressions; no mocked integration.

**Trace:** needs M6-NEED-001; risks HAZ-001, HAZ-002, HAZ-003, HAZ-004, HAZ-005; design M6-DES-006; verification M6-TEST-006.

**Implementation locations:** [src/ui/device_ui.cpp](../src/ui/device_ui.cpp), [src/ui/client.hpp](../src/ui/client.hpp), [src/device_session.hpp](../src/device_session.hpp), [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md), [docs/design/INTERACTION.md](../docs/design/INTERACTION.md), [docs/testing/WORKFLOW.md](../docs/testing/WORKFLOW.md).

### UI-REQ-001

Provide circuit visualization and bounded inspection without crossing device/experiment authority boundaries

**Acceptance:** Observe fluid circuits and selectable time-based values; missing/stale data distinguishable; recorded input cannot submit commands; live integration must pass on a socket-capable host.

**Trace:** needs M7-NEED-001; risks HAZ-001, HAZ-003, HAZ-004; design UI-DES-001; verification UI-TEST-001, UI-TEST-002.

**Implementation locations:** [src/console/telemetry.hpp](../src/console/telemetry.hpp), [src/console/inspector.hpp](../src/console/inspector.hpp), [src/console/sim_console.cpp](../src/console/sim_console.cpp), [src/ui/synoptic.hpp](../src/ui/synoptic.hpp), [src/ui/device_ui.cpp](../src/ui/device_ui.cpp), [tests/test_inspection.py](../tests/test_inspection.py), [docs/UI_INSPECTION.md](../docs/UI_INSPECTION.md), [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md), [docs/design/INTERACTION.md](../docs/design/INTERACTION.md), [docs/testing/WORKFLOW.md](../docs/testing/WORKFLOW.md).

### UI-REQ-002

Guide the simulated treatment from initial checks through disinfection with state-dependent actions and truthful progress

**Acceptance:** Explicit patient connection and disconnection, automatic bounded-phase completion, no automatic recovery restart, isolated flush/return water and solute conservation, dedicated circuit tabs and unavailable ETA during waits/stale data. During treatment, confirmed edits change blood and active HDF substitution flow without pausing or resetting progress; mode and net UF remain locked. Range violations, unsafe states and stale confirmations cannot release protection.

**Trace:** needs M7-NEED-001; risks HAZ-001, HAZ-003, HAZ-004; design UI-DES-002; verification UI-TEST-003, UI-TEST-004.

**Implementation locations:** [src/machine.hpp](../src/machine.hpp), [src/plant.cpp](../src/plant.cpp), [src/control.cpp](../src/control.cpp), [src/ui/client.hpp](../src/ui/client.hpp), [src/ui/device_ui.cpp](../src/ui/device_ui.cpp), [src/ui/guided.hpp](../src/ui/guided.hpp), [src/ui/synoptic.hpp](../src/ui/synoptic.hpp), [python/dialysislab/machine.py](../python/dialysislab/machine.py), [python/dialysislab/runner.py](../python/dialysislab/runner.py), [python/dialysislab/compartments.py](../python/dialysislab/compartments.py), [tools/verify_models.py](../tools/verify_models.py), [tests/test_guided.py](../tests/test_guided.py), [tests/guided_view.cpp](../tests/guided_view.cpp), [tests/guided_plant.cpp](../tests/guided_plant.cpp), [scenarios/device_guided.json](../scenarios/device_guided.json), [docs/GUIDED_TREATMENT.md](../docs/GUIDED_TREATMENT.md), [tests/ui_regressions.py](../tests/ui_regressions.py), [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md), [docs/design/TREATMENT.md](../docs/design/TREATMENT.md), [docs/testing/WORKFLOW.md](../docs/testing/WORKFLOW.md).

## Experiments and inspection

### M7-REQ-001

Run a separate real experiment console

**Acceptance:** Actual native/headless/X11/Compose services and widgets

**Trace:** needs M7-NEED-001; risks HAZ-001, HAZ-003, HAZ-004; design M7-DES-001; verification M7-TEST-001.

**Implementation locations:** [python/dialysislab/experiments.py](../python/dialysislab/experiments.py), [python/dialysislab/experiment_rpc.py](../python/dialysislab/experiment_rpc.py), [python/dialysislab/role_supervisor.py](../python/dialysislab/role_supervisor.py), [src/console/sim_console.cpp](../src/console/sim_console.cpp), [src/console/client.hpp](../src/console/client.hpp), [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md), [docs/design/INTERACTION.md](../docs/design/INTERACTION.md), [docs/testing/WORKFLOW.md](../docs/testing/WORKFLOW.md).

### M7-REQ-002

Validate immutable complete experiment configurations

**Acceptance:** Patient/circuit/dialyzer/mode/workflow/fault edits validated; live configuration unchanged

**Trace:** needs M7-NEED-001; risks HAZ-001, HAZ-003, HAZ-004; design M7-DES-002; verification M7-TEST-002.

**Implementation locations:** [python/dialysislab/experiments.py](../python/dialysislab/experiments.py), [python/dialysislab/experiment_rpc.py](../python/dialysislab/experiment_rpc.py), [python/dialysislab/role_supervisor.py](../python/dialysislab/role_supervisor.py), [src/console/sim_console.cpp](../src/console/sim_console.cpp), [src/console/client.hpp](../src/console/client.hpp), [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md), [docs/design/INTERACTION.md](../docs/design/INTERACTION.md), [docs/testing/WORKFLOW.md](../docs/testing/WORKFLOW.md).

### M7-REQ-003

Pause resume and stop virtual experiments safely

**Acceptance:** Pause >2 wall seconds preserves sequence/liveness; stop records actual HALT observation

**Trace:** needs M7-NEED-001; risks HAZ-001, HAZ-003, HAZ-004; design M7-DES-003; verification M7-TEST-003.

**Implementation locations:** [python/dialysislab/experiments.py](../python/dialysislab/experiments.py), [python/dialysislab/experiment_rpc.py](../python/dialysislab/experiment_rpc.py), [python/dialysislab/role_supervisor.py](../python/dialysislab/role_supervisor.py), [src/console/sim_console.cpp](../src/console/sim_console.cpp), [src/console/client.hpp](../src/console/client.hpp), [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md), [docs/design/INTERACTION.md](../docs/design/INTERACTION.md), [docs/testing/WORKFLOW.md](../docs/testing/WORKFLOW.md).

### M7-REQ-004

Replay compare and export trustworthy results

**Acceptance:** Fresh services reproduce exact bytes; streaming comparison/export rejects corrupt evidence

**Trace:** needs M7-NEED-001; risks HAZ-001, HAZ-003, HAZ-004; design M7-DES-004; verification M7-TEST-004.

**Implementation locations:** [python/dialysislab/experiments.py](../python/dialysislab/experiments.py), [python/dialysislab/experiment_rpc.py](../python/dialysislab/experiment_rpc.py), [python/dialysislab/role_supervisor.py](../python/dialysislab/role_supervisor.py), [src/console/sim_console.cpp](../src/console/sim_console.cpp), [src/console/client.hpp](../src/console/client.hpp), [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md), [docs/design/INTERACTION.md](../docs/design/INTERACTION.md), [docs/testing/WORKFLOW.md](../docs/testing/WORKFLOW.md).

### M7-REQ-005

Isolate administrative identity and interfaces

**Acceptance:** Bad token/revision/run/path/size rejected; device has no truth administration

**Trace:** needs M7-NEED-001; risks HAZ-001, HAZ-003, HAZ-004; design M7-DES-005; verification M7-TEST-005.

**Implementation locations:** [python/dialysislab/experiments.py](../python/dialysislab/experiments.py), [python/dialysislab/experiment_rpc.py](../python/dialysislab/experiment_rpc.py), [python/dialysislab/role_supervisor.py](../python/dialysislab/role_supervisor.py), [src/console/sim_console.cpp](../src/console/sim_console.cpp), [src/console/client.hpp](../src/console/client.hpp), [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md), [docs/design/INTERACTION.md](../docs/design/INTERACTION.md), [docs/testing/WORKFLOW.md](../docs/testing/WORKFLOW.md).

### M7-REQ-006

Preserve failure evidence and fresh lifecycle

**Acceptance:** Multiple Compose/native runs without Docker socket; interrupted artifacts retained, no implicit resume

**Trace:** needs M7-NEED-001; risks HAZ-001, HAZ-003, HAZ-004; design M7-DES-006; verification M7-TEST-006.

**Implementation locations:** [python/dialysislab/experiments.py](../python/dialysislab/experiments.py), [python/dialysislab/experiment_rpc.py](../python/dialysislab/experiment_rpc.py), [python/dialysislab/role_supervisor.py](../python/dialysislab/role_supervisor.py), [src/console/sim_console.cpp](../src/console/sim_console.cpp), [src/console/client.hpp](../src/console/client.hpp), [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md), [docs/design/INTERACTION.md](../docs/design/INTERACTION.md), [docs/testing/WORKFLOW.md](../docs/testing/WORKFLOW.md).

## Security, dependencies and integration

### M8-REQ-001

Isolate writable device producers

**Acceptance:** Actual role spoofing denied; device clients retain authorized access

**Trace:** needs M8-NEED-001; risks HAZ-001, HAZ-004, HAZ-005; design M8-DES-001; verification M8-TEST-001.

**Implementation locations:** [src/control.cpp](../src/control.cpp), [src/protection.cpp](../src/protection.cpp), [compose.yaml](../compose.yaml), [compose.experiments.yaml](../compose.experiments.yaml), [python/dialysislab/role_supervisor.py](../python/dialysislab/role_supervisor.py), [tools/verify_compose.py](../tools/verify_compose.py), [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md), [docs/design/INTERFACES.md](../docs/design/INTERFACES.md), [docs/testing/FAILURES.md](../docs/testing/FAILURES.md).

### M8-REQ-002

Clean up native children after owner death

**Acceptance:** Real owner SIGKILL ends children, preserves partial records and does not invent observed zero

**Trace:** needs M8-NEED-001; risks HAZ-002, HAZ-003, HAZ-004; design M8-DES-002; verification M8-TEST-002.

**Implementation locations:** [src/child_guard.cpp](../src/child_guard.cpp), [python/dialysislab/runner.py](../python/dialysislab/runner.py), [python/dialysislab/role_supervisor.py](../python/dialysislab/role_supervisor.py), [tests/test_security.py](../tests/test_security.py), [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md), [docs/design/INTERFACES.md](../docs/design/INTERFACES.md), [docs/testing/FAILURES.md](../docs/testing/FAILURES.md).

### M8-REQ-003

Bound and validate untrusted inputs

**Acceptance:** Duplicate/deep/oversized/trickle inputs rejected; watchdog/protection remain effective

**Trace:** needs M8-NEED-001; risks HAZ-001, HAZ-002, HAZ-003, HAZ-004, HAZ-005, HAZ-006; design M8-DES-003; verification M8-TEST-003.

**Implementation locations:** [python/dialysislab/trajectory.py](../python/dialysislab/trajectory.py), [python/dialysislab/patient.py](../python/dialysislab/patient.py), [python/dialysislab/experiment_rpc.py](../python/dialysislab/experiment_rpc.py), [src/plant.cpp](../src/plant.cpp), [tests/test_security.py](../tests/test_security.py), [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md), [docs/design/INTERFACES.md](../docs/design/INTERFACES.md), [docs/testing/FAILURES.md](../docs/testing/FAILURES.md).

### M8-REQ-004

Inventory selected dependencies and artifacts

**Acceptance:** Reproducible versioned SBOM, license/pin/notice checks and identified platform packages; actual image application hashes and stale-image rejection

**Trace:** needs M8-NEED-001; risks HAZ-001, HAZ-004; design M8-DES-004; verification M8-TEST-004.

**Implementation locations:** [dependency_inventory.json](../dependency_inventory.json), [tools/dependency_report.py](../tools/dependency_report.py), [tools/platform_inventory.py](../tools/platform_inventory.py), [tests/test_dependencies.py](../tests/test_dependencies.py), [docs/dependencies/M8.md](../docs/dependencies/M8.md), [tools/image_application.py](../tools/image_application.py), [tools/build_identity.py](../tools/build_identity.py), [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md), [docs/design/INTERFACES.md](../docs/design/INTERFACES.md), [docs/testing/FAILURES.md](../docs/testing/FAILURES.md).

### M8-REQ-005

Execute and disposition available analyses

**Acceptance:** Actual static/advisory reports identify commands, findings, coverage and blocks

**Trace:** needs M8-NEED-001; risks HAZ-001, HAZ-002, HAZ-003, HAZ-004, HAZ-005, HAZ-006; design M8-DES-005; verification M8-TEST-005.

**Implementation locations:** [tools/security_scan.py](../tools/security_scan.py), [assurance/DEPENDENCY_FINDINGS.json](../assurance/DEPENDENCY_FINDINGS.json), [tests/test_dependencies.py](../tests/test_dependencies.py), [assurance/THREATS.json](../assurance/THREATS.json), [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md), [docs/design/INTERFACES.md](../docs/design/INTERFACES.md), [docs/testing/FAILURES.md](../docs/testing/FAILURES.md).

### M8-REQ-006

Continuously verify builds integration and publication

**Acceptance:** Real builds/processes/widgets/Compose and assurance/publication CI with retained outcomes; exact recoverable bytes and checker execution failures propagated

**Trace:** needs M8-NEED-001; risks HAZ-001, HAZ-002, HAZ-003, HAZ-004, HAZ-005, HAZ-006; design M8-DES-006; verification M8-TEST-006.

**Implementation locations:** [.github/workflows/verify.yaml](../.github/workflows/verify.yaml), [tools/ci_verify.py](../tools/ci_verify.py), [tools/check_publication.py](../tools/check_publication.py), [publication_manifest.json](../publication_manifest.json), [docs/dependencies/CI_NOTICES.md](../docs/dependencies/CI_NOTICES.md), [tools/ci_artifacts.py](../tools/ci_artifacts.py), [tests/test_ci.py](../tests/test_ci.py), [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md), [docs/design/INTERFACES.md](../docs/design/INTERFACES.md), [docs/testing/FAILURES.md](../docs/testing/FAILURES.md), [tools/documentation.py](../tools/documentation.py), [tests/test_documentation.py](../tests/test_documentation.py), [docs/DOCUMENT_CONTROL.md](../docs/DOCUMENT_CONTROL.md).

### M9-REQ-001

Integrate all treatment/patient/dialyzer combinations

**Acceptance:** 18 configurations twice natively/twice Compose; exact replay, complete lifecycle and independent water/species conservation <=1e-6

**Trace:** needs M9-NEED-001; risks HAZ-002, HAZ-003, HAZ-004, HAZ-006; design M9-DES-001; verification M9-TEST-001.

**Implementation locations:** [tools/verify_integrated.py](../tools/verify_integrated.py), [tools/verify_models.py](../tools/verify_models.py), [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md), [docs/design/INTERFACES.md](../docs/design/INTERFACES.md), [docs/testing/FAILURES.md](../docs/testing/FAILURES.md).

### M9-REQ-002

Verify sustained treatment and resource bounds

**Acceptance:** Two native/two Compose100000-tick HDF runs; >99000 treatment ticks, grossUF>100000mL, RSS<=64MiB/no OOM at128MiB

**Trace:** needs M9-NEED-001; risks HAZ-003, HAZ-004; design M9-DES-002; verification M9-TEST-002.

**Implementation locations:** [tools/verify_integrated.py](../tools/verify_integrated.py), [tests/test_integration.py](../tests/test_integration.py), [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md), [docs/design/INTERFACES.md](../docs/design/INTERFACES.md), [docs/testing/FAILURES.md](../docs/testing/FAILURES.md).

### M9-REQ-003

Integrate simultaneous real device and experiment applications

**Acceptance:** Actual widget pause/replay/STOP/cancellation/state/epoch/isolation tests, headless and WSLg

**Trace:** needs M9-NEED-001; risks HAZ-001, HAZ-002, HAZ-004, HAZ-005; design M9-DES-003; verification M9-TEST-003.

**Implementation locations:** [python/dialysislab/experiments.py](../python/dialysislab/experiments.py), [tests/test_experiments.py](../tests/test_experiments.py), [tools/verify_experiments_compose.py](../tools/verify_experiments_compose.py), [compose.experiments-x11.yaml](../compose.experiments-x11.yaml), [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md), [docs/design/INTERFACES.md](../docs/design/INTERFACES.md), [docs/testing/FAILURES.md](../docs/testing/FAILURES.md).

### M9-REQ-004

Verify the reproducible source package

**Acceptance:** Identical allowlisted archives and real build/tests/widgets from extracted sources

**Trace:** needs M9-NEED-001; risks HAZ-001, HAZ-004; design M9-DES-004; verification M9-TEST-004.

**Implementation locations:** [tools/verify_package.py](../tools/verify_package.py), [tools/package_release.py](../tools/package_release.py), [publication_manifest.json](../publication_manifest.json), [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md), [docs/design/INTERFACES.md](../docs/design/INTERFACES.md), [docs/testing/FAILURES.md](../docs/testing/FAILURES.md).

### M9-REQ-005

Deliver complete supported technical evidence and operations

**Acceptance:** Identified actual CI recovery, commands, model limits, trace links and unchanged open release obligations

**Trace:** needs M9-NEED-001; risks HAZ-001, HAZ-002, HAZ-003, HAZ-004, HAZ-005, HAZ-006; design M9-DES-005; verification M9-TEST-005.

**Implementation locations:** [tools/ci_verify.py](../tools/ci_verify.py), [docs/QUICKSTART.md](../docs/QUICKSTART.md), [README.md](../README.md), [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md), [docs/SIMULATION.md](../docs/SIMULATION.md), [docs/README.md](../docs/README.md), [docs/DEVELOPMENT.md](../docs/DEVELOPMENT.md), [docs/diagrams/README.md](../docs/diagrams/README.md), [docs/diagrams/hydraulic-equivalent.svg](../docs/diagrams/hydraulic-equivalent.svg), [docs/diagrams/dialyzer-transport.svg](../docs/diagrams/dialyzer-transport.svg), [docs/diagrams/extracorporeal-reference.svg](../docs/diagrams/extracorporeal-reference.svg), [docs/diagrams/fluid-preparation.svg](../docs/diagrams/fluid-preparation.svg), [tools/render_hydraulic_diagrams.py](../tools/render_hydraulic_diagrams.py), [docs/design/INTERFACES.md](../docs/design/INTERFACES.md), [docs/testing/FAILURES.md](../docs/testing/FAILURES.md).

## Change control

Edit the register, review requirement changes, then run `python3 tools/documentation.py --write`.
Historical result fields in the compatibility register are not evidence of current approval.
See [Document control](DOCUMENT_CONTROL.md) and [current verification status](testing/STATUS.md).
