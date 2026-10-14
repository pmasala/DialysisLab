# Preparation verification protocol

STP-MIX-01; prospective acceptance fixed before implementation/testing, 2026-10-14.
Synthetic teaching model only; no empirical or clinical validation.

Implementation allocation: [SDD-MIX-01](../design/PREPARATION.md). MIX-REQ-001–016
and executable methods are in the maintained requirement/obligation registers;
MIX-REQ-017 remains deferred. Run `python3 tools/verify_preparation.py --output <new.json>`;
check later applicability with `--check <report.json>`. Reports retain exact input
hashes, compiler, configurations, method results and numeric witness output.

The selected transport law is exact plug displacement, so there is no spatial mesh
to refine. Analytic front-arrival tests cover air, water and concentrate starts;
50/25/12.5 ms runs test temporal input resolution. The intermediate mixed volume
is 10 mL. Intermediate conductivity must be within 4% of nominal, in addition to
the tighter contribution/final guards below. The first-order dissolution time
constant is 2 s, vent time constant 0.05 s, PI normalized proportional gain 0.7
and integral gain 0.04 /s. These synthetic selections are not calibrated values.

Nominal fixture: 5 mL per source line, 120 mL rigid accessible cartridge cavity
(100 mL regulated liquid plus headspace), 600 mL/min water fill capacity, 50 mL final
mixed tank, 500 mL/min preparation, 550 g solid, 3 g/min dissolution cap. Cartridge
is isothermal at 25 C. Partial molar volume of dissolution is neglected. Pumps are
averaged positive displacement pumps, maximum 60 mL/min, 0.2 s drive time constant,
300 mmHg stall head; entrained-gas volumetric efficiency is 0.5 (synthetic).
The vent is bidirectional to atmosphere; a blocked vent is an injected fault.

Internal maximum step is 50 ms, with 25 and 12.5 ms refinement witnesses. Cartridge
pressure bounds are -100/+100 mmHg gauge; these are synthetic operating limits,
not structural or clinical ratings. A violated bound inhibits inlet and metering
on the next internal step (<=50 ms). Pressure beyond the validated gas-volume
range must never be hidden by clipping a reported sensor value.

Sensor lag is 0.2 s; freshness budget 0.5 s. Qualification requires both wet source
outlets, cartridge level >=95% of target, pressures in range, intermediate bicarbonate
and inferred acid contribution each within 3% of nominal, final within 2%, and pump
ratios between 0.5 and 1.5 times nominal. All conditions persist for 3 s. Startup
timeout is 600 s. Invalidity resets dwell immediately; a fresh sample alone is not
sufficient. Controller integrators freeze on invalid measurements and use conditional
integration at actuator saturation. Readiness is a preparation permission, never a
reset of existing machine protection latches.

Acceptance before execution:
- All liquid/species inventories remain nonnegative (roundoff <=1e-10).
- Global source/storage/output balances: absolute residual <=1e-6 mL and mmol
  for startup, step changes, exhaustion, stopped supply and the eight-hour witness.
- Cartridge gas balance: residual <=1e-6 atmosphere-equivalent mL.
- Analytic plug displacement and constant-input mixed-tank references: <=1e-9.
- Nominal startup qualifies within 600 s, with zero usable output before qualification.
- A 10% acid-stock reduction after qualification requalifies within 180 s; commands
  stay within 0..60 mL/min. No clinical performance claim follows from this fixture.
- For 50/25/12.5 ms inner steps, final tank concentration at common 400 s differs
  by <=0.5 mmol/L between successive refinements; the smaller-step difference
  does not exceed the larger-step difference plus 1e-8. Report all values.
- Component gas compression/vent tests follow the isothermal ideal-gas equation.
- Source depletion cannot increase solid mass or remove dissolved mass instantaneously.
- Invalid/stale sensors, blocked vent and absent water cannot qualify output; abnormal
  pressure latches a fault and prevents conflicting actuation on the next substep.
- Integration: HD, HDF PRE and HDF POST startup and treatment through actual Plant
  commands; no unqualified preparation enters circuit flush, dialysate or replacement.
  Following source fault, control permits cannot defeat the final delivery guard.
- Source/configuration/procedure hashes and exact commands identify retained evidence.
  Test existence, execution and independent acceptance are separate statuses.

Pump equations, chemistry, sensor coverage and parameter calibration remain model
limitations. Replacement sequencing is deferred (MIX-REQ-017). Individual ions are
not identifiable from conductivity; this protocol does not claim otherwise.
