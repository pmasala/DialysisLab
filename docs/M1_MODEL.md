# Synthetic HD model, m1-hd-1

This is an algebraic, uncalibrated demonstration of transport, conservation and
protective authority. It is not physiology or a clinically usable dialysis model.
Only synthetic patient/equipment configurations are supported.

## Equations and units

For pump demand D [mL/min], resistance R [mmHg min/mL], and synthetic maximum pump
head H=600 mmHg, delivered blood flow is Q=min(D,H/R) and circuit gauge pressure
P=R*Q. These are an ideal flow source with a pressure cap and a resistive return
path to zero gauge pressure. R is positive (0.01..100); D is 0..500. There is no
compliance, inertance, suction, blood viscosity model, or transient pressure solver.

If unlatched and Q>0, ultrafiltration U=min(U_demand,Q), with U_demand 0..20 mL/min;
otherwise U=0. For interval dt [ms], removed volume dV=U*dt/60000 [mL]. Patient
volume V_next=V-dV; effluent E_next=E+dV. Blood recirculates, so Q does not directly
subtract from V. Circuit storage is fixed and its change is zero. Substitution,
other intake/output and solute fluxes are explicitly zero in M1. Thus V+E=V_initial
and net patient loss equals gross UF. No conversion to body weight is implemented.

Nominal acceptance settings: D=300, U_demand=10, R=0.5, V_initial=40000, dt=100 ms,
20 ticks. Occlusion at tick 5 changes R to 4: measured P=600 and Q=150 before
protection. Threshold 250 trips before tick 5's fluid integration. Expected removed
volume is 5*10*100/60000=1/12 mL. Without fault, 20 ticks remove 1/3 mL. All these
settings, including the threshold, are synthetic demonstrations, not safety limits.

## Solver and observation timing

The algebraic model is exact for a constant command/resistance within each tick;
fluid integration is exact rectangular integration of the piecewise constant UF.
PREPARE computes observations using held actuators and the new physical fault;
COMMIT applies decisions before integrating. Initial observations are zero, followed
by the first demand. A command-induced pressure increase is visible on the next
tick, so the declared general detection bound is one dt. Faults at tick boundaries
are visible in that same tick. Separate sensor channels share the equations but
have independent validity/time fault settings; neither decision service sees R,
fault instructions, patient truth or effluent truth.

## Numerical and validity limits

IEEE binary64, C++17 without fast-math, Python float, integer virtual clock.
Independent tests use Decimal arithmetic from configuration and expected active
interval counts, rather than trusting the plant's accumulated removal as an oracle.
Balance tolerance: absolute 1e-8 mL over <=100000 ticks; compare cross-build physical
values with abs/rel 1e-9. Same-build deterministic records must be byte-identical.
Seed is required and recorded; M1 has no random terms, so changing seed changes
configuration identity but not the physical equations. Wall timestamps and build
metadata live outside deterministic trajectory records.

There is no dialysate composition/temperature, membrane transport, solute/electrolyte
clearance, patient pressure, compartment/refill physiology, air/blood-leak detection,
HDF or substitution integrity. Pump-off/clamp-closed/UF-off is chosen only for this
closed synthetic circuit's pressure/data-loss cases; it is not a general clinical
protective-state prescription. Calibration, parameter provenance, realistic models,
uncertainty budgets and approved hazard-specific recovery remain roadmap work.
