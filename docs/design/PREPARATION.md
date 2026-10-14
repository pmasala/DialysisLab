# Concentrate preparation design

Document ID SDD-MIX-01; CR-MIX-001 first increment; independent review pending.
Read [requirements](DIALYSATE_PREPARATION_CHANGE.md), then this design, the
[prospective protocol](../testing/PREPARATION.md) and current results in
[verification status](../testing/STATUS.md). This is a synthetic teaching model.

## Boundary and activation

`src/preparation.hpp` contains the source/line/cartridge/mixer model, sensor frames,
two PI trims and qualification supervisor. `Online::advance_physical` couples its
composition to the existing heater and patient/circuit model. The default legacy
physical scenarios retain their original initialization; the new model is explicit
in `scenarios/preparation_hd.json`, `preparation_hdf_pre.json` and
`preparation_hdf_post.json`. Launch the guided UI with one of these configurations
using the existing `tools/run_device_demo.py --config` option. These examples include
a one-minute treatment; the component endurance witness lasts eight simulated hours.

The new `physical.preparation` object and `PREPARATION11` admin command require the
dynamic physical profile, before machine initialization or arming. Invalid values
are rejected before replacing state. Published examples use 5 mL per line, a rigid
120 mL accessible cartridge cavity with a 100 mL liquid target, 600 mL/min fill,
50 ms maximum internal step, 200 ms sensor transport delay and 3 s qualification.
Initial line occupancy codes are air (0), water (1) or nominal concentrate (2).
Cold start refers to concentrate preparation; the existing heater temperature
initialization is retained (37 C in the examples). The cartridge starts dry; the
10 mL intermediate and 50 mL final tanks start with
water, not nominal dialysate. A 1 mL acid connector air pocket precedes bag liquid.

No solid-volume/porosity change is modeled: the configured accessible cavity excludes
solid displacement. Partial molar volume, acid neutralization, gas dissolution,
CO2 evolution, chemical speciation, wetting/channeling, sterility, leakage and thermal
gradients inside the cartridge are outside this increment. These omissions require
calibration/model development before claiming physical fidelity outside the fixture.

## D1: lines and pumps (MIX-REQ-001, 002, 007)

Each `PrepLine` is an exact volume FIFO. Incoming plugs displace equal volumes at
the outlet, retaining air/liquid identity and six species inventories. Known residual
water or concentrate is distinct from a dry line. There is no spatial mesh and no
artificial mixing between adjacent plugs. Temporal input averaging remains; step
refinement tests its effect. Liquid presence does not establish cleanliness.

The two `PrepPump` objects represent averaged positive-displacement actuators.
Drive approaches bounded command with a 0.2 s exponential time constant. Actual
displacement is drive times `max(0,1-max(0,p_out-p_in)/300)`, with pressures in mmHg,
and an additional efficiency of 0.5 during gas aspiration. Command is limited to
0–60 mL/min. These are declared synthetic curves, not a manufacturer's pump model.
Acid stock concentration is a source boundary condition separate from remaining
bag volume. Empty/disconnected sources admit gas. The `acid_scale` fault changes
incoming concentration; it does not rewrite fluid already retained in the line.

## D2: cartridge (MIX-REQ-003–006)

`PrepCartridge` retains liquid mL, gas in atmosphere-equivalent mL, solid grams and
dissolved mmol. Sodium and bicarbonate receive equal mmol; molar mass is 84.0066 g/mol.
At the fixed cartridge temperature of 25 C, gauge pressure is
`760 * (gas / (capacity - liquid) - 1)` mmHg. Absolute pressure is therefore positive
whenever gas inventory is positive. Reported pressure is never clipped to a limit.

Water admission fills toward the target and replaces withdrawn liquid. A bidirectional
atmospheric vent relaxes gas inventory toward geometric headspace with a 0.05 s time
constant, recording inlet/outlet gas separately. `vent_blocked` removes that path.
Dry withdrawal removes atmosphere-equivalent gas. A pressure excursion beyond
±100 mmHg latches a preparation fault; inlet and pump displacement are inhibited on
the next internal substep, at most 50 ms. The minimum 1 mL geometric headspace is
an admission constraint, not a pressure clamp. No automatic fault reset is provided.

For a step h seconds, dissolved transfer is the minimum of available solid mmol,
the configured g/min dissolution capacity converted to mmol, and
`max(0, Csat*liquid/1000 - dissolved) * (1-exp(-h/2))`.
The configured saturation reference is multiplied by `max(0,1+0.015*(T-25))` when
the component temperature is varied. This local relation and the 2 s kinetic time
constant are synthetic parameters, not measured bicarbonate solubility data.
Enough solid does not guarantee saturation at high withdrawal. Exhausting solid
leaves dissolved inventory intact; subsequent throughput washes it out.

## D3: mixers and ledgers (MIX-REQ-008, 015)

Main water and the bicarbonate outlet enter a 10 mL ideal mixed volume. Its effluent
then joins the acid outlet in the final tank. Ideal gas separators reject outlet gas;
their rejection volume is recorded. Carrier water completes the requested flow
after actual concentrate delivery, so an unavailable concentrate produces dilution.
With incoming liquid v, tank volume V and incoming concentration Cin, the exact
constant-input update is `Cnew = Cin + (Cold-Cin)*exp(-v/V)`. Effluent species mass
is computed as previous inventory plus incoming mass minus new inventory.

Boundary ledgers distinguish supplied liquid/species, retained line and tank
inventories, solid/dissolved bicarbonate, cartridge gas exchange, rejected line gas,
unqualified waste and qualified preparation outlet. Long-double boundary totals
avoid accumulation error over eight hours. The latter outlet is a preparation
manifold boundary, not patient delivery: surplus is available to the downstream
bypass. Actual filter/substitution/flush delivery is separately verified through
Plant and the existing patient transaction ledgers. Qualification on a partial
external tick cannot authorize that entire tick; Plant requires every substep ready.
Actual available liquid must also cover requested flow on each substep. This physical
availability check blocks delivery immediately after water loss, including a 25 ms
step before a delayed water-switch observation arrives. Permits cannot create volume.

## D4: observations and control (MIX-REQ-009–011)

The controller accepts only `PrepFrame`: wet outlets, connection/water switches,
cartridge level and pressure, acid/bicarbonate outlet conductivity and liquid flow,
intermediate/final conductivity, temperature, validity and sampling timestamp.
The generic linear ionic conductivity proxy is inherited from the physical profile.
Raw conductivities use the frame's temperature and coefficient; control compensates
them back to 25 C. This is a synthetic common-temperature measurement convention,
not a claim of resolved source/heater thermal transport.

Conductivity/flow channels have 0.2 s first-order lag; the full sampled frame has the
configured transport delay. Age above 0.5 s, future/absent timestamp or invalidity
rejects the frame. `sensor_stale` stops observation updates; `sensor_invalid` clears
validity immediately. Discrete wet/pressure/level channels share frame latency.
The direct cartridge pressure interlock is a separate modeled local switch.

Nominal flow times the prescribed concentrate fraction supplies each feedforward.
Measured source conductivity times measured liquid flow divided by total flow
estimates that source's conductivity contribution. Each loop uses normalized error
from its nominal contribution, proportional gain 0.7 and integral gain 0.04 /s,
scaled by nominal metering flow. Integral accumulation freezes on invalid/dry frames
and when saturation would deepen; reverse error may unwind it. Its range is ±60
mL/min. Configured concentration/fractions are nominal parameters; true remaining
bag volume, powder mass and dissolved inventory cannot enter controller decisions.

Final conductivity alone cannot identify the two doses. Qualification requires both
contributions within 3%, intermediate conductivity within 4%, final within 2%, and
each observed dose between 0.5 and 1.5 times nominal. Conductivity still cannot
uniquely identify individual ions or distinguish all wrong-stock mixtures. Those
detection gaps remain open and are not hidden by passing the compensation witness.

## D5: states, guards and final authority (MIX-REQ-012–014)

| Sequence | Codes and observable transitions |
| --- | --- |
| Acid | 0 disconnected; 1 line filling while outlet dry; 3 liquid but not qualified; 2 own dose stable for dwell; 4 latched fault |
| Bicarbonate | 0 disconnected; 1 filling below 95% target; 2 stabilizing liquid/contribution; 3 own dose stable for dwell; 4 latched fault |
| Supervisor | 0 preparing/unqualified; 1 all guards continuously stable but dwell incomplete; 2 available; 3 latched pressure/startup fault |

Both sources progress independently using their observed conditions. The supervisor
also requires valid wet outlets, both connections, water, acceptable pressure and
95% cartridge target level. Any failed guard resets dwell; one fresh sample cannot
qualify output. Failure to qualify within 600 s from startup latches a timeout.
After first qualification, loss of guards withdraws availability and diverts fluid;
requalification repeats dwell. It never clears a machine protection latch.
No hot replacement, isolation/relief/reconnect/reset procedure is supplied here;
MIX-REQ-017 remains explicitly deferred.

`OBS11` extends the existing dynamic observation with preparation-ready/fault bits.
During cold SELF_TEST/PREPARATION only, expected low conductivity and unavailable
supply do not create permanent composition/supply alarms. Other protective checks
remain active. Self-test cannot complete before actual qualified flush flow is
observed. Flow-response cycle counts start only when flushing is authorized.

`Plant::handle(COMMIT5)` rechecks preparation after all internal substeps. Unqualified
fluid forces dialysate and substitution off and prevents circuit flushing. A loss
during treatment latches the machine supply alarm even if both external decision
roles send forged permits. Pressure/startup faults likewise latch machine protection.
Prepared replacement capacity is included during startup, avoiding an artificial
mixing-flow change at the treatment transition. Requested live flow changes can
disturb qualification and require the existing explicit recovery workflow.

Telemetry `PREPARATION11` follows `DYNAMICS10` in physical state. It exposes states,
truth inventories, separate pump commands/actual displacement, sampling age inputs
and conservation residuals to the experiment observer. Hidden inventory is for
inspection and verification, not a prescription or controller input.

## Verification and limits

`tests/preparation_model.cpp` contains analytic FIFO/CSTR/ideal-gas references,
bounded pump and PI cases, 50/25/12.5 ms refinement, faults and eight-hour depletion.
`tests/test_preparation.py` additionally drives the production Plant and patient
through all three modalities and challenges the final actuator authority.
`tools/verify_preparation.py` records test identities, commands, exact input hashes,
configuration and failure history; `--check` rejects stale input applicability.
These are executed software/numerical checks. Independent physical calibration,
human review, clinical suitability and replacement procedures remain outstanding.
