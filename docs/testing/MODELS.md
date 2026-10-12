# Test protocol: model equations and credibility

Document ID STP-MOD; revision 1; proposed protocol. Requirements: REQ-003/006,
M2-REQ-001…004, M3-REQ-001…004, M4-REQ-001…004, PHY-REQ-001, DYN-REQ-001.
Apply [master evidence rules](PLAN.md); no new execution is claimed here.

## Setup and oracles

Identify model variant, geometry, all coefficients and initial inventories. Preserve
`dt_ms`, number of cells, modality, input fluid composition, temperature and source
uncertainty. Use separate HD/PRE/POST cases with zero, nominal and boundary demands.
Analytic conservation is checked independently in [verify_models.py](../../tools/verify_models.py).
A test using the same equation implementation for both expected and actual values
is a consistency test, not independent physical validation.

| Case | Procedure and expected result | Executable basis / remaining work |
| --- | --- | --- |
| MOD-01 Hydraulic limiting cases | Exercise resistor/RC analytic cases, clamp and zero-flow states. Halve time step and require decreasing error against analytic solution. | `tests/test_circuit.py`; legacy graph scope, not all dynamic physics |
| MOD-02 Geometry/rheology | Vary needle diameter with other inputs fixed; resistance follows inverse fourth power. Check finite pressure, allowable Hct and pump-head limitations. | `tests/physical_model.cpp`, `test_equations_and_limits` |
| MOD-03 Independent ledgers | Run HD/PRE/POST through complete guided phases. Reconstruct body/circuit/source/waste/UF/substitution balances from retained records; integrated residual <=1e-6 mL and mmol. Check red-cell/protein inventory and local sums separately. | Physical process suite and independent model verifier |
| MOD-04 Chamber dynamics | Apply flow steps and gas-actuator bounds; compare gas law and liquid continuity. Isolate and confirm retained storage and zero boundaries. Trigger low/high-level protection. | `tests/dynamic_model.cpp`, dynamic gas/pump test |
| MOD-05 Dialysate control | Apply UF/pump steps and valve changeovers, including dt smaller than 30 ms. Reconstruct feed + filtration − drain − storage change; compare with declared solver tolerances and settle-window response. | Dynamic C++ fixture; independent measured controller response remains open |
| MOD-06 Local transport | Introduce a concentration step. Verify progressive transit, no negative accepted inventories, PRE/POST insertion at their distinct nodes and dialysate counterflow conservation. Reject malformed transactions without state mutation. | `test_distributed_transit_delay_conservation_and_atomic_rejection` |
| MOD-07 Numerical failure | Force hydraulic nonconvergence with a bounded iteration budget. Require stopped outputs and explicit limitation, never a nominal successful treatment transaction. | `tests/dynamic_model.cpp` |
| MOD-08 Reference fit | Fit urea using 300 mL/min point only; evaluate 400 mL/min holdout for each public profile. Engineering comparison threshold is 5% absolute relative clearance error. Record mesh sensitivity and leave other coefficients uncalibrated. | `test_reference_holdout_and_discretization_are_reported`, reference-fit tool |
| MOD-09 Preparation | Check reservoir transient, finite stocks, heater power limit, unit-consistent energy balance and temperature-corrected conductivity. Observable quality failures inhibit fluid delivery; hidden contaminant does not create a sensor. | `tests/test_treatment.py`, physical equation fixture; bench calibration remains open |
| MOD-10 Full dynamic convergence | Repeat transient coupled hydraulic/patient cases with successively halved steps; compare pressures, levels, local concentrations and total exchanges using preapproved metrics. Study partitioned coupling error separately from mass residual. | Prospective: no approved global error budget or complete envelope evidence yet |

Never infer physiological accuracy from a small mass residual or from MOD-08 alone.
The reference clearance measurements do not fully specify fluid composition and
uncertainty. All reuse must retain source conditions and redistribution assessment.

## Measurement-based validation still required

Collect pressure/flow curves at controlled geometry, Hct, protein and temperature;
chamber pressure-volume/gas-actuator transients; pump/sensor/valve response; thermal
and concentrate mass balances; conductivity versus actual electrolyte composition;
and paired dialyzer inlet/outlet concentrations with measured UF. Identify instrument
calibration, repeatability, sampling time and uncertainty. Reserve independent data
for validation. Patient refill and electrolyte dynamics require a separately approved
patient-model validation protocol. No measurements have been invented to close this
work, and the planned Excel import pipeline is not an existing verification tool.

The controlled [measurement protocol](MEASUREMENTS.md) supplies per-model conditions,
required channels, acquisition metadata, uncertainty and holdout rules.
[CLOSE-NUM-01](CLOSURE.md) defines the global convergence campaign and its
preapproved error-budget gate.
