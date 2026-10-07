# M4 treatment and online preparation contract

Phase base `47ffc5efa5ca1cd2878a2924b182d1bb72a7a8e3`, frozen before code.
All profiles, thresholds, chemistry and quality barriers below are synthetic.
Neither sterility, microbiological quality nor clinical performance is established.

## Requirements and acceptance

| Requirement | Predeclared acceptance | Links |
| --- | --- | --- |
| M4-REQ-001 | HD, HDF pre and HDF post use explicit delivery points; water and each solute conserved within 1e-6 mL/mmol. Gross UF, substitution, storage and net body loss remain separate. | HAZ-003 / M4-DES-001 / M4-TEST-001 |
| M4-REQ-002 | Online reservoir mixing/heating, two filter pressure losses and pressure-limited delivery evolve from equations. Analytic equilibrium/transient and step-halving tests, multiple dialyzers/patients. | HAZ-003,006 / M4-DES-002 / M4-TEST-002 |
| M4-REQ-003 | Modeled temperature/composition/route/integrity/supply signals cause direct plant arbitration. Quality latch blocks substitution, UF and dialysate exchange while retaining blood circulation unless a separate blood hazard trips. | HAZ-002,004,006 / M4-DES-003 / M4-TEST-003 |
| M4-REQ-004 | Repeated native/Compose scenarios, fault and conflicting-command tests, exact config/build identity, unchanged M1–M3 regressions. No protection access to hidden contaminant truth. | HAZ-001,003,004,006 / M4-DES-004 / M4-TEST-004 |

Quality faults latch at the next PREPARE observation (<=one dt after crossing a
measured threshold); fixture ratio/thermal faults must become observable within
10 virtual seconds. Supply interruption is detected after at most one completed
zero-delivery tick (startup grace: first two ticks). dt remains 1–1000 ms. These
are software demonstration bounds, not clinical safety limits.

## Physical equations and scope

A constant-volume, well-mixed preparation reservoir has volume V [mL]. Inflow
Q [mL/min] equals the configured dialysate circulation plus requested replacement;
its concentration is ratio times concentrate concentration. Backward Euler gives
`Cnew=(V Cold + dt Q Cin)/(V+dt Q)`. A heating regulator is a first-order energy
source: `Tnew=(V Told + dt Q Tin + dt V k Tset)/(V+dt Q+dt V k)`.
Temperatures are degrees C; k is min^-1, representing a synthetic heater gain,
not a real device controller/power specification. Initial equilibrium is explicitly
configured; preparation transients may be explored with faults.

Two filters and a delivery line add resistances R1+R2+Rl [mmHg min/mL]. A delivery
pump with head H [mmHg] and command D [mL/min] supplies
`Qsub=D (1-P/H)/(1+D R/H)` with a nonnegative diode. Filter drops are Qsub Ri.
In predilution this source enters the dialyzer upstream compliant node and is
included implicitly in the graph solve. In postdilution it enters the zero-pressure
patient return reservoir after the dialyzer; no separate post-line storage is
modeled. HD requests no replacement. Actual delivery can differ from its command.
The gross UF demand is net UF command + replacement command, subject to membrane
hydraulics; this does not promise the requested net balance is achieved.

Pre replacement adds volume/solute to the conservative extracorporeal compartment;
post replacement adds directly to body E. The extracorporeal chemical compartment
is well mixed, not an axial dialyzer model. Patient + circuit + effluent − external
inputs − replacement conserves water/mass. The preparation reservoir and supply
are external to this accounting boundary. Its tank exchange ledger is reported
separately, so reservoir dynamics are independently checkable. Blood heat exchange,
protein binding, viscosity/hemoconcentration and microbiology are outside scope.

A dimensionless contaminant surrogate passes each intact filter with a configured
penetration fraction (0–1), or without attenuation if a hidden breach is injected.
No microbial units, kill kinetics or sterility inference are attached to this state.
A separately modeled integrity-test signal can reveal a breach; an unobserved breach
or contaminant increase remains undetected. Conductivity surrogate is 0.05 times
the sum of the five ionic concentrations; it cannot identify individual species or
isoconductive composition errors. These are explicit common-cause/latent hazards.

## Versioned interfaces and arbitration

Scenario schema 4 / `m4-treatment-1` adds `treatment` (mode, replacement command,
reservoir/heater/source/filter parameters) to schema 3. Old contracts are unchanged.
Admin `ONLINE4` configures once before arming; `FAULT4 name value` changes only
bounded authorized preparation truth/instrument faults between ticks.
`TRANSPORT3` still updates coupled blood concentrations. `COMMIT4` returns one
atomic `COMMITTED4 STATE4 ... CIRCUIT3 ... ONLINE4 ...` snapshot, including actual
replacement volumes/composition and quality latch. Never reconstruct a committed
transaction from later status reads. `STATUS4` exposes live actuator state to the
runner; HALT invalidates pending decisions and zeros replacement as well as UF/blood.

Control/protection use `SENSE4 n t` -> `OBS4 n t valid blood pressure gross_uf
T conductivity replacement_flow filter_pressure integrity route`. Units are
mL/min, mmHg, C, synthetic mS/cm; route enum 0=HD,1=pre,2=post,3=waste. Sensors
are frozen at PREPARE, with the same sequence/time/validity faults as M1. No solute
inventories, hidden breaches or contaminant are in OBS4. STEP4 accepts requested
blood/net UF/replacement/mode (control) or pressure limit/mode (protection).
DEMAND4 and QUALITY4 are role-limited; an active quality latch cannot be overridden
by any DEMAND4. Existing hard TRIP/HALT dominates all outputs.

Synthetic quality limits: 35–39 C, conductivity 12–16, filter pressure <=300 mmHg,
intact integrity-test signal, matching route, replacement flow >=1 mL/min after
startup in HDF. QUALITY4 zeros live UF, replacement and membrane coefficients immediately on
acceptance, before any later COMMIT; circulating blood, stored volume and
cumulative accounting remain intact. A quality fault latches until a new run in M4; reset/recovery is
reserved for M5. Acknowledgment cannot alter arbitration. Invalid observations
and communication failures retain terminal/fail-safe M1 policies. Wall-clock
watchdog remains separate from virtual-time quality detection.

INIT4/ADVANCE4/STATUS4 and PATIENT4 version the Python patient transaction.
ADVANCE4 extends ADVANCE3 by pre_mL, post_mL and substitution_mmol_L; gross UF
numerical bound is 140 mL/min, replacement command <=120 mL/min and blood + replacement commands <=500 mL/min
to stay within the modeled blood-flow sensor range. Patient responses
add substitution_mL and substitution_mmol. STATE4 cumulative gross UF is bounded by 140 * 100000 / 60 mL plus 1e-6
roundoff, independently of body volume: replacement permits gross removal above
100000 mL. The hydraulic pressure envelope includes both configured pump heads,
even while a source is disabled. Computed ADVANCE4 dialysate concentrations admit
the existing 1e-9 mmol/L slack; initial/configured concentrations remain strictly
bounded, without clipping. Initial patient configuration remains schema-3 compatible. JSONL v1 streaming and 4096-byte bounded frames remain in use;
no silent format reinterpretation. Restart is a new run, no ambiguous transaction retry.

## Verification and limitations

Tests compare actual body/circuit/effluent inventories against independent input
integration, check pre/post dilution and HD, observe fault detection timelines,
challenge conflicting control commands and compare exact repeat hashes. Tank
mixing/thermal equations and filter pressure losses have separate numerical oracles.
Hidden contamination tests must show the absence of an invented sensor alarm.
Actual commands/build/configurations/results belong in `assurance/evidence/m4/`.

No third-party application dependency is added; M1–M3 pinned toolchain/licenses
remain applicable. Standards and private sources remain outside all build contexts
and public artifacts. M5–M9, physiological calibration, bench validation, quality
barrier validation and human risk acceptance remain required work/gaps.

## Review correction protocol

The sole M4 review found delayed live quality isolation, three numerical/version
boundary defects and two missing evidence cross-checks. Regressions observe plant
STATUS4/CSTATE3 after QUALITY4 without COMMIT, challenge late demands, exercise
computed concentration ceilings and unequal pump heads, and reject rehashed forged
actuator rates/substitution-solute ledgers. Evidence checks compare actual rates
with tick volumes and enforce zero replacement under either protective latch.
`treatment_100000` tests gross UF above 100000 mL with positive body water, native
confirmed HALT decoding, streaming output, independent conservation, exact replay
and the unchanged 128 MiB Compose limit. Long trajectories remain in ignored build
outputs; committed reports identify hashes/counts/RSS and all configurations.
