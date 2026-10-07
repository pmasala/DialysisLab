# Architecture baseline

Status: functional scope and UI separation agreed. M1 now implements the limited
headless HD slice described in [M1_PLAN.md](M1_PLAN.md), with versioned
[interfaces](M1_INTERFACES.md), [model equations](M1_MODEL.md) and
[risk boundaries](M1_RISKS.md). The broader architecture below remains the required
roadmap; UI, HDF, fluid preparation and calibrated physiology are not implemented.

M2 adds an opt-in synthetic compliant circuit and multiple dialyzer profiles in
the same plant process. [M2_MODEL_INTERFACES.md](M2_MODEL_INTERFACES.md) defines
the node/edge solver, water accounting and prescribed-boundary membrane transport.
The M1 path remains compatible; neither decision service receives circuit truth.

M3 couples the Python patient to actual hydraulic transfers and membrane
coefficients in atomic COMMIT3 replies. A three-compartment implicit mass solve
includes the extracorporeal mixing volume, while plant/control/protection remain
separate processes. Applied solute transfers and body truth stay on simulation
administration channels. [M3_PATIENT.md](M3_PATIENT.md) defines the deliberately
limited physiology, conservative ledgers and failure semantics.

## Deployment boundaries

| Container/application | Language | Responsibility |
| --- | --- | --- |
| device-ui | C++ with LVGL's C API | Medical-device-style operator interaction. |
| control | C/C++ | Treatment state machine and regulation. |
| protection | C/C++ | Independent monitoring decisions, alarms, watchdogs, and protective-action requests. |
| plant | C++ | Circuit, dialysate/substitution preparation, dialyzer, actuators, sensor channels, and actuator arbitration. |
| patient | Python | Patient compartments, fluid/solute dynamics, and configurable physiology. |
| scenario-runner | Python | Simulation time, scenario execution, faults, recording, and evaluation. |
| sim-console | C++ proposed | External experiment application, separate window/process/container from device-ui. Dear ImGui/ImPlot are candidates. |

The earlier combined operator/experiment UI is superseded by two separate applications. The original requirement for separate control, protection, and UI containers is retained. Headless execution excludes both graphical applications.

## Device UI contract

Present treatment setup, HD/HDF mode, operator-entered treatment parameters, preparation and treatment progress, measured values, permitted estimates, alarms, and operator actions. Develop a coherent touchscreen layout with clear units, status, priorities, confirmation flows, and trend presentation.

Device UI is a client of machine command/status APIs. It cannot publish raw actuator commands or create clinical alarm state. Control validates treatment commands. Protective monitoring continues independently of UI availability. Acknowledgment or permitted silencing does not by itself clear a continuing fault or release a protective action.

Do not include patient-model editing, hidden physiological truth, injected faults, simulation-speed controls, or model calibration in device-ui. Operator-entered patient/treatment context is allowed where relevant to the simulated machine workflow; it is distinct from access to the physiology engine's state.

Keep a visible simulation indication. Realistic appearance does not establish usability validation or standards conformity.

## External simulation console contract

The separate console configures patient models, initial conditions, circuit/dialyzer profiles, timed events, and faults; compares true and measured values; manages recording/replay and accelerated runs; and reviews conservation and validation results.

It accesses scenario-runner administration APIs and observer telemetry. Pausing or losing the console must not reset the simulation. Scenario-runner owns simulation progression and model updates.

Patient parameter changes at runtime must be explicit events with defined physical semantics, recorded in the trace. Configuration is validated before a run; configuration snapshots and seeds travel with results.

## Data and authority boundaries

- Plant produces measurements for control and protection through separately modeled sensor channels. Both channels may share underlying physics, but their measurement faults can differ.
- Protection does not depend on control's interpretation of sensor data and can request action directly from the plant's modeled actuator arbitration interface.
- Control cannot override a latched protective constraint. Hazard-specific recovery rules govern release.
- Only simulation services and external observers see hidden physical/patient truth. Device-facing interfaces expose only modeled measurements and explicitly implemented estimates.
- Scenario-admin endpoints must not be reachable by the device UI, control, or protection. Enforce endpoint authorization and deployment/network boundaries; a hidden menu is insufficient.
- Preserve distinct physical-state and instrumentation-fault injection paths. An injected occlusion changes the circuit; an injected sensor bias changes its reported value.
- Containers on one host do not establish hardware safety independence. Shared host/kernel/resource/transport failures remain in the simulation architecture's limitations.

## Physical and numerical scope

Use configurable hydraulic components and a mass-conserving dialyzer/patient interface. Couple pressure losses, pump/valve characteristics, compliant volumes, diffusion, convection, and membrane water transport. Validate physical parameters and transport equations against declared reference ranges.

Implement HD, HDF predilution, and HDF postdilution through explicit circuit topology and fluid injection points. Track gross membrane fluid transfer, substitution, other inputs/outputs, circuit storage, net patient fluid balance, and predicted weight change separately.

Online preparation includes composition/mixing, heating, flow distribution, filtration-stage resistance, and substitution delivery. Initially represent contamination/filter-integrity conditions as declared surrogate states and test scenarios. Hydraulic behavior does not prove sterility, and protection can only respond to evidence available through modeled sensors/tests.

Patient modeling includes fluid compartments and configurable electrolyte/solute imbalance. Select physiological equations and validation datasets before claiming predictive accuracy. Acid-base behavior and electrolyte coupling must have explicit model assumptions rather than independent arbitrary concentration curves.

## Execution and UI backend

Use Linux containers under WSL2 and native Linux, with headless, desktop-wsl, and desktop-linux launch profiles. Plan deterministic tick ordering, bounded message semantics, explicit units, sequence numbers, timestamps, and data validity. Use numerical tolerances for cross-platform reproducibility; do not promise bitwise identity across arbitrary platforms.

Separate the virtual simulation clock from wall-clock process liveness. Paused or accelerated simulation must have defined watchdog behavior. Physics libraries remain independent of transport and containers.

Use LVGL's documented SDL desktop integration initially, with software rendering to limit graphics dependencies. The documentation inspected on 2026-10-07 uses SDL2; verify compatibility when pinning LVGL. WSLg/native Linux display sockets and permissions require platform-specific launch configuration. Containers should run without blanket privileged access.

## Initial acceptance targets

1. Device UI cannot access patient administration or simulation-truth APIs.
2. External console can configure a synthetic patient and launch a recorded scenario.
3. Control/protection behavior can be evaluated without either GUI running.
4. An occlusion changes physical flow/pressure; protection sees only its sensor data and can request a protective action without control cooperation.
5. The device UI displays machine measurements and treatment data, while the external console can compare them with model truth.
6. A headless scenario produces a configuration snapshot, event trace, and conservation diagnostics.
7. Both WSL2 and native Linux can launch the device UI with the selected backend.

These are planned verification targets, not passed tests.

## Sources

Official sources checked 2026-10-07:

- LVGL licensing and separate commercial editor: https://lvgl.io/docs/open/introduction/license
- LVGL SDL desktop integration: https://lvgl.io/docs/open/integration/pc/sdl
- Dear ImGui: https://github.com/ocornut/imgui
- ImPlot: https://github.com/epezent/implot
- SDL licensing: https://www.libsdl.org/license.php
- WSL graphical applications: https://learn.microsoft.com/en-us/windows/wsl/tutorials/gui-apps
- Docker WSL backend: https://docs.docker.com/desktop/features/wsl/
- IEC 62304 scope: https://webstore.iec.ch/en/publication/22794
- IEC 60601-1 scope: https://webstore.iec.ch/en/publication/67497
- IEC 60601-2-16 scope: https://webstore.iec.ch/en/publication/68379
- ISO 14971 scope: https://www.iso.org/standard/72704.html
