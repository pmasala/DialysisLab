# Concentrate preparation: controlled change proposal

Document ID CR-MIX-001; requested 2026-10-14; revision controlled by Git.
Status: first increment implemented; current execution is recorded separately; independent review pending.
Source: maintainer conversation on concentrate preparation, pumps and educational auditability.

## Purpose and existing baseline

The educational purpose is to make the path from a user need to physical assumptions,
software design, verification and recorded limitations understandable and inspectable.
Audit-oriented development is a process objective, not certification or clinical validation.

The inspected baseline is commit `c89e2d9`. [Online](../../src/online.hpp) models finite
acid volume, finite bicarbonate mass, a dissolution-rate cap, a mixed tank and temperature.
[Plant configuration](../../src/plant.cpp) initializes physical tank composition to nominal
values. It does not implement the source-line air displacement, cartridge gas/liquid storage,
pressure-controlled filling or separate concentration feedback requested here. Existing
physical-model tests do not verify those new behaviors.

First increment: cold startup, source transport, cartridge dissolution, mixing, pump control,
stabilization, source depletion and protective response. Cartridge/bag replacement procedures
are a separately deferred increment; do not silently discard that request.

## Trace and status conventions

MIX-REQ-001–016 are implemented candidates; MIX-REQ-017 remains deferred.
Stable IDs are promoted to the maintained requirement and test registers. Actual
symbols/equations are in [SDD-MIX-01](PREPARATION.md); numerical decisions are in
[STP-MIX-01](../testing/PREPARATION.md). This table preserves the requested scope.
Current execution evidence and applicability are separate from independent acceptance.

Parent requirements in [the maintained register](../../assurance/traceability.json) are
REQ-003 (accounting), REQ-004 (measurement validity), REQ-006 (prepared-fluid integrity),
M4-REQ-001 (preparation), PHY-REQ-001 (physical model), DYN-REQ-001 (dynamic model).
Existing hazard links must be assessed for this change; the hazards below are candidate
failure sequences, not completed risk evaluations.

The maintained executable-obligation matrix allocates MIX-REQ-001–016 to actual
test methods. MIX-REQ-017 has no executable allocation or claimed pass. The original
request and design rationale below remain linked from those allocations.

| ID | Verifiable requirement | Design | Planned test and expected result |
| --- | --- | --- | --- |
| MIX-REQ-001 | Each source line shall retain its configured internal volume and initial air, water or concentrate occupancy up to the mixing junction. | D1 | MIX-TEST-001: Exercise dry, wetted and residual-liquid starts; downstream arrival follows displaced volume and conserves inventories. |
| MIX-REQ-002 | Acid and bicarbonate shall have distinct metering pumps with command and actual transfer represented separately. | D1 | MIX-TEST-002: Exercise zero command, pressure load, air aspiration and actuator saturation; actual liquid delivery follows the declared pump law, not commanded displacement alone. |
| MIX-REQ-003 | The cartridge shall separately account for liquid volume, gas inventory, solid bicarbonate and dissolved bicarbonate. | D2 | MIX-TEST-003: Fill and withdraw from known initial inventories; storage changes match all boundary transfers and inventories remain nonnegative. |
| MIX-REQ-004 | Cartridge pressure shall respond to gas compression, liquid transfer and declared vent paths. | D2 | MIX-TEST-004: Block vent, restrict inlet and increase withdrawal; pressure follows the declared law and limit violations inhibit the conflicting actuator before the allocated deadline. |
| MIX-REQ-005 | Dissolution shall depend on the declared saturation relation, available solid and finite dissolution kinetics. | D2 | MIX-TEST-005: At adequate residence time approach saturation; under dissolution-limited withdrawal remain below saturation despite remaining solid. |
| MIX-REQ-006 | Solid exhaustion shall not erase remaining dissolved bicarbonate. | D2 | MIX-TEST-006: Exhaust solid and continue water throughput; dissolved inventory washes out conservatively rather than disappearing or remaining indefinitely constant. |
| MIX-REQ-007 | Acid concentration shall be a configurable source property, distinct from remaining bag volume. | D1 | MIX-TEST-007: Apply nominal, diluted and exhausted-source cases; concentration and delivered mass change consistently, including configured air ingress after depletion. |
| MIX-REQ-008 | Downstream mixing shall conserve species and liquid storage and represent declared transport delays. | D3 | MIX-TEST-008: Compare a well-mixed tank with its analytic step response and transport with volume/flow delay; verify independent inventory residuals. |
| MIX-REQ-009 | Control shall use simulated sensor outputs with timestamps, temperature compensation, latency and validity rather than hidden source inventory. | D4 | MIX-TEST-009: Inject delayed, stale, invalid and air-exposed measurements; invalid signals cannot authorize readiness. Changing hidden inventory alone cannot directly change a control decision with identical sensor history. |
| MIX-REQ-010 | Each metering command shall combine declared feedforward with bounded PI correction and defined anti-windup/invalid-measurement behavior. | D4 | MIX-TEST-010: Apply flow/concentration steps, saturation and invalidity; commands remain bounded, integrator behavior matches the specified policy and recovery meets prospective response criteria. |
| MIX-REQ-011 | Composition qualification shall include intermediate observations and ratio checks rather than final conductivity alone. | D4 | MIX-TEST-011: Construct compensating acid/bicarbonate errors with similar final conductivity; documented intermediate checks detect the observable cases and remaining detection gaps are reported. |
| MIX-REQ-012 | Acid and bicarbonate startup sequences shall progress independently with observable guards and bounded failure timeouts. | D5 | MIX-TEST-012: Hold each prerequisite false in turn; reject premature dosing qualification and enter the declared failure response on timeout. |
| MIX-REQ-013 | The preparation supervisor shall divert unqualified fluid to waste and prevent its delivery to the dialyzer/substitution paths. | D5 | MIX-TEST-013: Challenge every startup phase, each invalid guard and loss of qualification; verify actual routed volumes, not just displayed state. |
| MIX-REQ-014 | Readiness shall require valid liquid-presence evidence, acceptable pressure/composition and continuous stability for a configured dwell interval. | D5 | MIX-TEST-014: Test just below/at/above the dwell boundary and an intervening invalid sample; interruptions reset qualification and a single valid sample cannot authorize delivery. |
| MIX-REQ-015 | The model shall provide separate boundary ledgers for source supply, stored liquid/species, gas exchange, waste and usable output. | D1-D3 | MIX-TEST-015: Independently reconstruct balances across startup, zero flow, partial steps and exhaustion; refinements of timestep and transport discretization satisfy predeclared error budgets. |
| MIX-REQ-016 | Preparation evidence shall identify requirements, implementation revision, parameters, test oracle and execution outcome. | D1-D5 | MIX-TEST-016: Reproduce a fixed scenario and verify complete trace in both directions; changed source/configuration invalidates prior applicability. |
| MIX-REQ-017 | A later replacement procedure shall address isolation, pressure relief, reconnection, re-priming and requalification. | Deferred | MIX-TEST-017: Deferred protocol; blocked pending replacement design. No replacement implementation or successful test is claimed. |

## Design rationale and original allocation

### D1: source lines and metering actuators

Track acid and bicarbonate separately. Pump displacement is an actuator property; delivered
liquid depends on suction/discharge pressures, air and the selected pump mechanism. Choose and
document the pump type before assigning its law; two separate pumps do not imply identical laws.
Line initialization supports air and known residual fluid. Filling and rinsing are distinct:
liquid presence alone does not establish rinse completion or cleanliness.

### D2: cartridge storage and dissolution

Use explicit solid mass, dissolved mass, accessible liquid capacity, gas amount and temperature.
Specify porosity/solid displacement and rigid versus compliant enclosure assumptions. Gas pressure
uses absolute units internally; protective limits refer to the declared internal/external pressure
difference. Venting and leakage transfer gas inventory rather than deleting pressure numerically.
Water inlet and concentrate withdrawal both act on liquid storage and pressure.

Dissolution approaches a temperature-dependent saturation relation with finite kinetics. Solid
presence alone does not guarantee saturation. When solid is exhausted, dissolved mass persists
until removed. Chemistry/speciation and conductivity approximations must state their limits;
conductivity is not a unique reconstruction of all electrolyte concentrations.

### D3: mixing and transport

Carry species inventories through lines, cartridge and final mixing volume. Record incoming and
outgoing fluxes, including priming waste. Select a transport model and quantify its numerical
dispersion. Validate the well-mixed limiting case independently from the production integrator.

### D4: sensing, dosage and protection

Separate physical truth from sensor frames, controller state and independent protective decisions.
Proposed measurements: liquid/air presence, source and cartridge pressures, intermediate and final
conductivity with temperature, and the selected pump/flow feedback. The selected placement and detection
coverage are defined in SDD-MIX-01; empirical coverage remains unvalidated. Do not let the controller read exact remaining powder mass.

Start with ratio-based feedforward plus PI trim. State gains, units, sampling periods, bounds,
anti-windup and bumpless transfer explicitly. Do not integrate invalid conductivity errors during
air transit. Tune only against a declared envelope and test coupled-loop interactions. Keep a
separate protective check at the final actuator/routing authority.

### D5: state sequences and observable guards

| Sequence | State transition | Required observable guard | Action / abnormal case |
| --- | --- | --- | --- |
| Acid | Disconnected → connected | Connection evidence | Enable only the defined priming request; absent supply remains unavailable. |
| Acid | Connected → filling line | Valid pressure and priming request | Run bounded priming flow to waste; reject pressure/air faults. |
| Acid | Filling → dose available | Liquid arrival and valid source/pressure evidence | Permit bounded dosage; timeout stays unqualified. |
| Bicarbonate | Connected → cartridge filling | Valid connection, inlet/vent configuration and pressure | Coordinate water admission, gas discharge and withdrawal; pressure fault constrains actuators. |
| Bicarbonate | Filling → stabilizing | Observable fill completion and valid liquid path | Continue dissolution and monitored priming; never use elapsed time alone as proof of fill. |
| Bicarbonate | Stabilizing → dose available | Valid concentration/temperature and pressure evidence for configured dwell | Permit bounded dosage; disturbance resets dwell. |
| Either source | Dose available → unavailable/fault | Observed loss of liquid, pressure fault, invalid composition or measurement | Withdraw qualification and apply the defined protective response; truth depletion is logged separately. |
| Supervisor | Preparing → stabilizing → available | Both source qualifications plus valid final composition and continuous dwell | Divert to waste until all guards hold; route usable fluid only after qualification. |
| Supervisor | Available → unqualified/fault | Any failed required guard | Divert and inhibit delivery within the allocated timing budget; no automatic safety reset implied. |

Every state needs explicit entry/exit actions, permitted requests, timeout behavior and reset
conditions before implementation. Existing treatment states must not be renamed to disguise a
change in their guards; document compatibility and the new readiness interface separately.

## Risk and verification impact

Candidate failure sequences: trapped gas corrupts dosing; inadequate venting drives excessive
pressure difference; depletion or wrong stock causes wrong composition; compensating errors
escape final conductivity; invalid sensors authorize delivery; controller saturation delays recovery;
software bypasses waste diversion; altered startup deadlocks existing lifecycle checks.
Assess these against HAZ-002, HAZ-004 and HAZ-006 and add hazards if the existing scope is insufficient.
Risk acceptance and independent review are not supplied by this proposal.

Before execution, fix the synthetic operating envelope, pressure limits, sensor error/latency,
stability band/dwell, actuator response deadline, maximum overshoot, settling time and integral
recovery budget. Declare units and absolute/relative tolerances for each balance, including an
absolute criterion near zero. Justify values from model scale, analytic references and numerical
error analysis; do not use clinical-sounding numbers without a source and applicability rationale.

Verification levels: component analytic references; controller/plant integration; complete startup
through depletion; malformed/stale sensor and actuator fault injection; regression of HD/HDF and
guided treatment; timestep and spatial refinement; repeatability with retained provenance.
Analytic checks and numerical convergence do not establish physical/clinical validation. Empirical
calibration, parameter identifiability and independent review remain explicit open work.

## Change completion and didactic acceptance

For every row record requirement → design → actual source symbol → executable test → retained
result, with reverse links. Each result identifies commit/tree, configuration, tools, seed where
applicable, command, timestamps, failures/skips and reviewer disposition. A passing structural
checker establishes only link/document consistency, not behavioral coverage.

The reader should be able to answer: why is this required; what failure does it address; what
equation or state rule implements it; what challenges it; what result exists; what remains unknown?
Keep specified, implemented, executed, passed and independently reviewed states separate.
