# M2 circuit model and interface contract

Frozen before implementation, phase base `1999741`. All parameters and thresholds
are synthetic; no commercial dialyzer, physiological calibration or experimental
validation is represented. DL1 and `m1-hd-1` remain compatible.

## Requirements and predeclared acceptance

| ID | Requirement / acceptance | Hazard / design / test |
| --- | --- | --- |
| M2-REQ-001 | Configure 1–16 compliant nodes and 1–32 tube/resistor/clamp/dialyzer edges, a finite-head pump and independent sensor channels. Compare steady states with independent resistor calculations and transient solutions to 1e-6 relative at converged steps. | HAZ-002,004 / M2-DES-001 / M2-TEST-001 |
| M2-REQ-002 | Track pumped, returned, stored and membrane water independently. Each step satisfies drawn − returned − UF − storage change <=1e-8 mL absolute; long-run balance <=1e-6 mL. Positivity and finite inputs enforced. | HAZ-003 / M2-DES-002 / M2-TEST-002 |
| M2-REQ-003 | Implement mixed-cell diffusion, sieved convection and pressure-limited UF for at least two explicitly synthetic dialyzer profiles; verify zero flow, equal concentrations, membrane coefficients and sign of transfer independently. | HAZ-003 / M2-DES-003 / M2-TEST-003 |
| M2-REQ-004 | Run through real plant/control/protection/patient processes and Compose with streaming records. Component and sensor faults cannot bypass plant arbitration; invalid config fails before actuation. Repeat identical runs/hash. | HAZ-001,002,004 / M2-DES-004 / M2-TEST-004 |

## Hydraulic equations and solver

Node 0 is the zero-pressure patient reservoir. Other nodes have constant positive
compliance C [mL/mmHg], pressure P [mmHg], and excess stored volume C P [mL].
Edges carry Q_ab = (P_a − P_b)/R [mL/min], with R [mmHg min/mL]; a closed clamp
has zero conductance. Tube/resistor labels share this linear constitutive law.
One dialyzer edge uses its profile's R. This is an arbitrary resistive graph with
lumped compliance, not a spatial Navier–Stokes or blood-rheology solver.

The pump feeds a configured node: Q_p = D max(0, 1 − P/H), D <=500 mL/min,
H <=600 mmHg. Each node obeys C dP/dt = incoming − outgoing − local UF.
Backward Euler solves the conductance/compliance system using pivoted Gaussian
elimination (at most 16 unknowns). Time is converted from integer milliseconds
to minutes. The diode pump uses a zero-source solve if reverse flow would occur.
Positive compliance makes disconnected/clamped nodes well-defined. Stored water
is never silently discarded when a clamp closes.

UF is an explicit start-of-step prescription limit:
U = min(U_demand, KUF max(0,(P_a+P_b)/2), D), at the upstream dialyzer node.
KUF [mL/min/mmHg] includes no oncotic term and dialysate pressure is zero.
If this would create negative pressure, bisection reduces U to the feasible
nonnegative value. The result is actual UF, not an assertion that demand was met.
No adaptive wall-clock stepping. Numerical convergence is first order in virtual
dt; step-halving must reduce error against an independent analytic RC case.

Terminal HALT/protective isolation freezes circuit storage and closes modeled
boundaries: pump/return/UF flows zero. It does not empty or depressurize the
circuit. Actual internal pressures remain visible only as modeled sensors or
authorized truth. Subsequent normal ticks may record a protective latch, but
terminal HALT still invalidates the prepared tick and disallows later commit.

## Dialyzer transport

For each solute, K = (1/KoA + 1/Q_b + 1/Q_d)^−1 [mL/min], or zero if any factor
is zero. This comes from two perfectly mixed flow streams joined by a linear
membrane conductance. It is deliberately not a countercurrent fiber model.
J_diff = K (C_b − C_d)/1000 and J_conv = U S C_b/1000 [mmol/min], concentrations
in mmol/L and sieving S in [0,1]. Positive J removes solute from blood; negative
diffusion adds it. `urea, sodium, potassium, chloride, bicarbonate, calcium` is the
fixed order. M2 exposes transfer rates with prescribed concentration boundaries;
the conservative dynamic compartment coupling follows in M3. Neither osmotic
water shifts, electroneutrality, binding, hematocrit nor fouling is resolved here.

Profiles `synthetic-small` and `synthetic-large` are project-authored test fixtures,
not catalog specifications. Valid input ranges are operational/numerical bounds,
not biological validity: C 0.001–10, R 0.01–100, KoA 0–2000, KUF 0–1,
Q_d 0–1000, C_solute 0–1000, dt 1–1000 ms. Sensitivity to steps/parameters must
be considered before interpreting a result; no prediction validity is claimed.

## Versioned configuration and messages

Scenario schema 2, model `m2-circuit-1`, adds `circuit` and `transport` to M1
fields; retains `resistance_mmHg_min_mL` only for M1 compatibility and rejects
the old resistance fault in M2. `circuit` contains node compliance, edge tuples
`[from,to,R,kind,closed]`, pump/sensor/dialyzer indices, pump head and profile.
`transport` contains blood/dialysate concentrations and dialysate flow. Edge fault
target `edge:<index>` has value `{resistance, closed}`. Sensor fault semantics
are unchanged. All configurations, including resolved profile parameters, are
embedded and hashed in the manifest.

The DL1 bounded transport carries these explicitly suffixed v2 payloads on the
**admin plant listener only**, before first PREPARE unless noted:

- `CONFIG2 N E pump_node head sensor_node sensor_edge dialyzer_edge R KUF`
  followed by N compliances, then E edge tuples. One configuration per process.
- `TRANSPORT2 Qd` then six KoA, six sieving, six blood and six dialysate values.
  Boundary concentrations may be updated only between ticks. Returns `OK`.
- `EDGE2 index R closed`: between-tick physical fault/component change.
- `CSTATE2`: `CIRCUIT2 n end_ms N E pump return UF stored delta draw_tick`
  `return_tick uf_tick` then N pressures, E signed edge flows, six diffusive
  and six convective mmol/min rates. Status does not advance time.

Existing PREPARE freezes both modeled observations; sensor flow is the magnitude
of the selected edge, pressure the configured node. Control/protection receive
only OBS, never CONFIG2/CSTATE2/patient data. Measurements retain exact n,t,
validity, startup invalid/stale behavior and 500 ms deadline. A component change
affects the next implicit step and subsequent sampled pressure, not a fabricated
instantaneous pressure jump. Synthetic fault-response tests specify onset and
observed-threshold crossing separately.

For the committed `circuit_occlusion` fixture, the return clamp closes at 2000 ms;
the predeclared acceptance is a latched zero-flow response by 3000 ms. On any
sampled pressure >=250 mmHg, arbitration acts before that tick integrates. These
are test-fixture thresholds/budgets, not clinical pressure or timing limits.

Patient `FLUID2 n start_ms dt_ms net_loss_mL` advances its water ledger by actual
pump draw minus return (= UF + circuit storage change); permits negative net
loss on drainage, rejects depletion/overfill and sequence errors. M1 ADVANCE is
unchanged. Schema-2 manifests/JSONL v1 persist; extended records add `circuit`
with units in field names. Readers that consume only M1 fields remain usable.
Startup is zero pressure/excess storage, zero actuators; full restart starts a
new run, never silently restores a partial treatment. Failed RPC policy remains
terminal HALT with separate acknowledged and observed stop evidence.
