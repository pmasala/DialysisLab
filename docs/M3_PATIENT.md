# M3 conservative synthetic patient

Phase base `40533e4d09643d8913ecc4795757362e034cbb20`, fixed before implementation.
This adds configurable body compartments and conservative circuit coupling, not
patient-specific physiological prediction. M1/M2 compatibility remains required.

## Requirements, hazards and acceptance

| Requirement | Acceptance fixed before code | Links |
| --- | --- | --- |
| M3-REQ-001 | Two body compartments plus an extracorporeal mixing volume; water, urea, sodium, potassium, chloride, bicarbonate and calcium. Nonnegative concentrations/masses; finite bounded inputs and ordered transactions. | HAZ-003,004 / M3-DES-001 / M3-TEST-001 |
| M3-REQ-002 | Independent whole-system water and each-solute balances, absolute error <=1e-6 mL/mmol over supported synthetic runs; equal/opposite internal transfers. Analytic equilibrium, zero transport and step-halving tests. | HAZ-003 / M3-DES-002 / M3-TEST-002 |
| M3-REQ-003 | Distinct gross UF, external inputs/outputs, circuit storage, net patient loss and water-only weight estimate; configurable generation and infusion/excretion. Synthetic overload/imbalance scenarios with recorded parameters. | HAZ-003 / M3-DES-003 / M3-TEST-003 |
| M3-REQ-004 | Actual Python patient service coupled to C++ circuit coefficients through atomic committed snapshots; native/Compose repeated runs, failures, source/configuration identity, all affected regressions. | HAZ-001,003,004 / M3-DES-004 / M3-TEST-004 |

## Model and numerical method

Body compartments E and I are well mixed extracellular/intracellular **surrogates**.
An extracorporeal compartment C starts with a declared prime volume and E's initial
concentrations; this prime is external to the initial body volume. Its volume is
prime + the plant's excess compliant storage. No actual blood or patient is used.
Solutes are ordered `urea, sodium, potassium, chloride, bicarbonate, calcium`.
Volumes are mL, masses mmol, concentrations mmol/L, time minutes.

For each step, use actual committed pump draw, return, UF and membrane clearance
from the plant. Body E water changes by −draw + return + external_in − external_out.
Water redistribution I→E is a declared linear refill surrogate:

`J dt = k dt (Vi/Ti − Ve/Te) / (1 + k dt (1/Ti + 1/Te))`.

Here Ve,Vi are the post-external-flow provisional volumes and Te,Ti their initial
targets. k is in mL/min; this is volume-fraction relaxation, not an oncotic,
osmotic, cardiovascular or autoregulatory calculation. Final volumes must stay
positive and within the documented service bounds, otherwise the run aborts.

For each solute, intercompartment diffusion is
`K_e (Ce − Ci/rho)`; rho is a synthetic partition ratio representing a maintained
gradient, not an explicit Na/K ATPase or membrane-potential model. Refill water
carries donor solute. Draw carries Ce into C; return carries Cc into E. Membrane
diffusion is `K_d (Cc − Cd)`, convection `UF S Cc`, using M2 clearance/sieving.
All flow-concentration products convert mL to L with a factor of 1/1000.

A three-by-three backward-Euler balance solves **end-of-step concentrations**
together. Diagonal terms are new volume plus outgoing transfer volumes; off-diagonal
terms are negative incoming transfer volumes. Right-hand sides contain previous
mass and declared external/dialysate inputs. Positive new volumes give a strictly
column-diagonally-dominant transfer matrix with nonnegative inverse. This avoids
clipping away removed mass or creating solute at depletion. Check finite,
nonnegative results and conservation before accepting a transaction. Cumulative
external/diffusive/convective ledgers use compensated sums. Patient transaction
failure leaves the patient's previously accepted state intact.

The 1000 mmol/L numerical ceiling admits up to 1e-9 mmol/L floating-point slack
in computed states only, consistently in the solver, response validator and
TRANSPORT3 boundary. Values/masses are retained without clipping. At the largest
allowed compartment this slack represents at most 1e-7 mmol; the original 1e-6
mmol whole-system conservation limit remains unchanged. Initial concentrations
and deliberate excess beyond this slack are still rejected.

The plant supplies hydraulic state and membrane coefficients; M3's patient service
owns the conservative coupled mass solve. M2's prescribed-boundary rates are
retained only as explicitly named boundary estimates in M3 records; the patient's
applied diffusive/convective mass ledger is authoritative for M3 solute accounting.
Control/protection never receive patient or circuit truth.

## Electrolyte and acid-base limits

Urea and the five ions are transported mass inventories. The model does not enforce
electroneutrality, protein binding, membrane voltage, osmotic pressure, metabolism
other than declared generation, renal regulation or active ion pumps. Consequently
large/long electrolyte changes are synthetic numerical experiments.

Bicarbonate also feeds an **illustrative equilibrium pH indicator**:
`pH = 6.1 + log10([HCO3]/(0.03 pCO2))`, with fixed user-configured pCO2 and null
when bicarbonate is zero. These apparent constants are illustrative, not calibrated.
There is no dynamic CO2, ventilation, non-carbonic buffer, ionized calcium or
acid-production chemistry. The indicator cannot assess clinical acid-base status.
It is explicitly distinct from a validated acid-base model.

The implementation subtracts logarithms instead of dividing subnormal values
before taking a logarithm. The complete proposed snapshot, including this indicator,
is constructed and validated before accepting any time, sequence or inventory update.

Research context (read 2026-10-08):
[Pietribiasi et al., 2018](https://doi.org/10.1371/journal.pone.0209553) models
separate fluid spaces and ion transport, including active transport absent here.
[Pietribiasi et al., 2023](https://doi.org/10.1371/journal.pone.0282104) treats
buffer chemistry and respiratory regulation, illustrating major missing mechanisms
in the limited fixed-pCO2 indicator. These are conceptual references, not reproduced
implementations or calibration data. No clinical datasets, text, figures or fitted
parameters from these papers are distributed. Calibration and independent validation
datasets remain separate, unavailable project inputs; synthetic fixtures serve only
software/numerical verification.

## Versioned interfaces and configuration

Scenario schema 3, model `m3-patient-1`, adds `patient` to M2. It records initial
body volumes/concentrations, circuit prime, partition/exchange/refill parameters,
external input/output rates/composition, generation, initial weight and pCO2.
Initial body volumes must sum to `patient_volume_mL`; initial E concentration must
match the transport boundary vector, which is updated from C each later tick.

Admin-only `TRANSPORT3` uses TRANSPORT2 fields but fixes coupled mode before the
first tick. `COMMIT3 n t` atomically returns `COMMITTED3 STATE ... CIRCUIT3 ...`;
CIRCUIT3 appends six actual clearances [mL/min] to CIRCUIT2. Status/fault/terminal
arbitration policies remain as in M2; no split status read reconstructs a commit.

Patient service `INIT3 <compact-json>` validates an initial parameter object once.
`ADVANCE3 <compact-json>` accepts n,start_ms,dt_ms, committed draw/return/UF/storage,
six clearances/sieving/dialysate concentrations. `STATUS3` returns the last accepted
state; responses are `PATIENT3 <compact-json>` with n/time, all volumes/masses,
concentrations and conservation ledgers. JSON must be finite, exact-key bounded
objects; the existing 4096-byte frame/deadline limit still applies. Restart creates
a new run; no implicit restoration or retries of ambiguous ADVANCE are permitted.
Plant commit followed by patient loss is an aborted partial transaction, not rollback.

Oversized JSON integers are range-checked before conversion to floating point;
malformed requests return ERR and leave the patient service/state available.
Evidence readers reject NaN/Infinity and overflowing float literals. Verification
cross-checks the two body volumes and the circuit volume (including prime) against
their summaries and physical storage; a matching hash is insufficient by itself.

JSONL v1 remains streaming; records add `patient` with explicit units and separate
gross/net/circuit ledgers. A water-only weight estimate assumes density 1 kg/L and
constant nonwater body mass. Input ranges are numerical limits, never clinical
prescription limits. Every scenario remains marked synthetic and simulation-only.

Configuration bounds: each initial body compartment 100–100000 mL, their sum
1000–100000 mL, prime 10–1000 mL, concentrations 0–1000 mmol/L, exchange 0–2000
mL/min, partition 0.001–1000, refill 0–5000 mL/min, external water rates 0–100
mL/min, generation 0–10 mmol/min per species and pCO2 10–100 mmHg. Weight must
exceed initial water mass. During evolution each compartment must remain >=1 mL,
total body volume <=100000 mL and concentrations within the same numerical bounds.
Leaving these bounds aborts; accepting initial input does not promise that every
combination can sustain an arbitrary duration. A 100000-step fresh-process probe
requires peak RSS <64 MiB, leaving at least half the 128 MiB Compose budget for
process/runtime overhead; it does not replace a full long-run deployment test.
