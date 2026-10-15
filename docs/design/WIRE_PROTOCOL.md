# Wire protocol: current end-to-end contract

Document ID ICD-01; revision controlled by Git; proposed technical baseline.
This document and the generated [field dictionary](WIRE_FIELDS.md) define current
DL1 guided/physical/dynamic interfaces. [wire-contract.json](../wire-contract.json)
is the machine-readable fixed-field source. Units and parser bounds are explicit;
physical acceptance is stricter than the broad diagnostic decoder ranges.

## Envelope, time and errors

DL1 is an ASCII line `DL1 OP fields...` terminated by LF. Exactly one exchange uses
one Unix stream connection. Core outgoing frames including LF are <=4096 bytes;
patient distributed responses explicitly allow 32768. Tokens cannot contain spaces.
JSON payloads therefore use compact serialization. Numbers must be finite decimal
values; integer clocks are nonnegative. One exchange has a 500 ms wall deadline.
Malformed protocol returns `ERR protocol`; semantic refusal returns `REJECT reason`.
Successful requests generally return `OK`. A transport failure is neither of these
and must be handled as an ambiguous failed exchange, without retrying a tick.

`sequence` identifies a tick, `start_ms` its virtual start, and `end_ms` its completed
time. Requests must use the exact next/prepared clock specified for their role.
Reported machine time can be at tick end while the retained sample is from PREPARE;
those timestamps are not interchangeable. A single-process atomic snapshot is not a
cross-process transaction: patient failure after COMMIT leaves an aborted partial run.

## Configuration order and remaining base messages

The current configuration sequence is CONFIG2 → TRANSPORT3 → ONLINE4 → PHYSICAL9 →
FLUID9 → optional DYNAMICS10 → MACHINE5 → GUIDED8. Patient INIT5 receives the expanded
patient configuration before advancement. Physical/dynamic setup changes internal
plant geometry; the legacy graph remains the initialization contract. Exact fixed
extension fields are in the dictionary; the variable-size base contracts follow.

| Operation | Ordered payload after operation | Constraints / result |
| --- | --- | --- |
| CONFIG2 | N E pump_node head sensor_node sensor_edge dialyzer_edge dialyzer_R KUF; N compliances; E groups of (from,to,R,kind,closed) | N 1..16, E 1..32; non-ground pump/sensor 1..N; edge indices 0..E-1; head 1..600 mmHg; R .01..100 mmHg min/mL; KUF 0..1 mL/min/mmHg; compliance .001..10 mL/mmHg. Node ends 0..N distinct; exactly one kind=3 dialyzer at specified index with nonzero inlet. Other kinds tube=0/resistor=1/clamp=2; closed integer 0/1. OK |
| TRANSPORT3 | Qd; six KoA; six sieving; six blood concentrations; six dialysate concentrations | Qd 0..1000 mL/min; KoA 0..3000 mL/min; sieving 0..1; blood 0..1000+1e-9 mmol/L for coupling; dialysate 0..1000. Between ticks; enables patient coupling. TRANSPORT2 uses blood <=1000 and uncoupled variant |
| ONLINE4 request | mode reservoir_volume ratio inlet_temperature setpoint heater_rate initial_temperature head R1 R2 line_R penetration1 penetration2 source_contaminant; six concentrate concentrations | Mode 0..2; reservoir 1..1000 mL; ratio 0..1; temperatures 0..90 C; legacy heater rate 0..100 /min; head 1..600 mmHg; resistances .01..100; penetrations 0..1; contaminant 0..1e6 arbitrary units; concentrate 0..1000/max(ratio,.04) mmol/L. Once after coupled circuit; OK |
| EDGE2 | edge_index resistance closed | Legacy-only between ticks; physical model rejects physical_geometry. Bounds follow CONFIG2 |
| FAULT4 | name value | Between ticks. ratio 0..1 and mixed concentrations <=1000; temperature 0..90; supply/integrity/breach1/breach2 integer 0/1; route integer 0..3; contaminant 0..1e6; filter1 .01..100. Unknown name rejected |
| FAULT5 | name value | Between ticks. air/leak 0..1, meter_bias 0..1000 mL; air_stuck/leak_stuck/supply_stuck/pump_stalled integer 0/1. Unknown name rejected |
| PING | none | OK; appropriate plant-role heartbeat refreshed. No virtual advancement |
| HALT | none | Admin: terminal cancellation of prepared tick and decisions, zero modeled outputs, process remains inspectable; OK |
| STOP | none | Private service/admin shutdown, distinct from operator STOP5; OK |
| STATUS / CSTATE3 / STATUS4 / META5 | none | Observer-only state families described below; no physics advancement |

Six-element order is always urea, sodium, potassium, chloride, bicarbonate, calcium.
Mode is HD=0, HDF PRE=1, HDF POST=2; preparation route 3 means isolated delivery.
Malformed admin/decision messages may latch protocol shutdown, so testing invalid
configuration must use fresh processes rather than reusing a terminal plant.

## Composite responses

Tags below appear inside a single DL1 envelope; do not insert additional DL1 tokens.

| Payload | Ordered fields after its tag |
| --- | --- |
| STATE4 | sequence end_ms blood_flow pressure gross_UF removed_total removed_tick latched clamp_closed reason |
| CIRCUIT3 | sequence end_ms N E pump_flow return_flow UF stored_volume storage_delta draw_tick return_tick UF_tick; N node pressures; E signed edge flows; six diffusive rates; six convective rates; six clearances |
| ONLINE4 state | sequence end_ms mode route temperature conductivity substitution_flow pre_tick post_tick substitution_total quality_latched reason filter1_pressure filter2_pressure tank_contaminant delivered_contaminant mixing_flow; six concentrations |
| COMMITTED5 | STATE4 + CIRCUIT3 + ONLINE4 + MACHINE5 or MACHINE8 + optional PHYSICS9 + optional DYNAMICS10 state trailer |
| LIVE4 | STATE4 + ONLINE4 state; live diagnostic, not a reconstructed committed transaction |
| VIEW5 | MACHINE5 or MACHINE8 + OBS5/8/9/10 + INTENT5 on service-produced device reply |
| INTENT5 | confirmation_id state result; state none/confirmation/queued; result none/applied/expired/cancelled or rejection reason |

Flow fields are mL/min; volume and tick transfers are mL; pressure mmHg;
diffusive/convective rates mmol/min; clearances mL/min; temperature C; conductivity
mS/cm. Node 0 ground is omitted from the N pressures. Flags are 0/1. Circuit storage
may be signed relative to prime volume. State reasons are machine tokens, not free
text. CSTATE3 is live; the atomic COMMITTED5 must be used for conservation records.
The CIRCUIT2 variant omits the six clearances; it is compatibility-only, not the
current coupled transaction. Broad state-decoder numeric bounds never replace the
source/target conservation and physical-domain checks.

Stage indices: 0 preparation, 1 priming, 2 configuration/connection, 3 treatment,
4 paused, 5 stopped, 6 recovery, 7 finished, 8 cleaning, 9 cleaned, 10 self_test,
11 connected, 12 returning, 13 disconnecting, 14 disconnected, 15 recovery_ready.
Hazard bit positions 0..12: pressure, flow, air, leak, measurement, temperature,
composition, filter, integrity, route, supply, balance, communication.

## Device epoch and scheduled operations

HELLO6 returns `SESSION6 epoch`, where epoch is 32 lowercase hex characters from a
fresh 16-byte process identifier. STATUS6, REQUEST6, PRESCRIBE6, CONFIRM6, STOP6,
ACK6 and SILENCE6 prepend that epoch to the corresponding v5 arguments. Wrong epoch
returns `REJECT session`; it is freshness protection, not an authentication token.
STATUS6 returns `VIEW6 epoch` followed by the VIEW5 body. A versioned request retains
the same role checks and confirmation lifetime as v5.

Private service `SCHEDULE7` takes no fields, is accepted before the first step and
permanently locks ordinary device mutations for that process. `OPERATOR7` on the
private service socket prefixes a normal operator operation for the trusted runner.
Device STOP remains immediate; `CHECK7` on control returns OK or REJECT external_stop.
Acknowledged or queued intent is not proof that the plant has applied it.

## Patient INIT5 and ADVANCE5

INIT5 carries one compact JSON object. Required scalar/string fields are `id`,
`provenance`, `refill_mL_min`, `prime_mL`, `initial_weight_kg`, `pco2_mmHg`,
`external_in_mL_min`, `external_out_mL_min`. Arrays are `volume_mL[2]`,
`concentration_mmol_L[2][6]`, `exchange_mL_min[6]`, `partition[6]`,
`external_mmol_L[6]`, `generation_mmol_min[6]`. Identity is one of the synthetic
profiles and provenance is synthetic. Body volume sum must match the scenario;
initial body blood concentrations must match initial transport input.

Optional hemodynamics contains `initial_hematocrit` .1.. .6, `vascular_mL` 1000..10000,
`protein_g_dL` 1..15, `temperature_C` 30..42, `refill_mL_min` 0..2000.
Optional extracorporeal contains `volumes_mL[16]` .001..1000 each, `koa_mL_min[6]`
0..3000, `dialysate_volume_mL` 1..1000, `dialysate_mmol_L[6]` 0..1000. Its summed
blood volumes equal prime within 1e-7 mL and it requires hemodynamics. The runner
expands this object from geometry; it is not a device UI parameter.

ADVANCE5 has exactly these fields (optional flags explicitly noted):

| JSON field | Type / unit / rule |
| --- | --- |
| sequence, time_ms, dt_ms | Integers; exact next sequence/start time; dt 1..1000; at most 100000 ticks |
| draw_mL, return_mL, uf_mL | Nonnegative water transfers; draw <=1000*dt_minutes for distributed or 500*dt_minutes otherwise; return <=100000; UF <=140*dt_minutes |
| stored_mL | Circuit excess over configured prime; with hemodynamics may be as low as -prime+1, upper 96000 |
| clearance_mL_min[6] | 0..2000; compatibility exchange coefficients, not effective local KoA |
| sieving[6] | 0..1 |
| dialysate_mmol_L[6], substitution_mmol_L[6], flush_mmol_L[6] | 0..1000+1e-9; slack is a bounded numeric allowance, not permission to create mass |
| pre_mL, post_mL | Each 0..120*dt_minutes; cannot both be positive |
| flush_in_mL, flush_out_mL | Nonnegative source/waste transfers; inlet capped like draw, outlet <=100000 |
| rinseback | Optional boolean, default false; when true requires draw, UF, waste flush and clearances zero |
| distributed | Required when network configured; keys below |

Distributed keys are `volumes_mL[16]`, `filtration_mL[12]`, `dialysate_mL_min`,
`dialysate_storage_mL`, `dialysate_drain_mL_min`, `membrane_open` boolean. Volumes
come from the committed hydraulic chambers/geometry; filtration is per-segment UF
times dt; flow/storage/drain and bypass are the committed dynamic state. The network
solver checks continuity, finite values, positive retained inventories and actual
effluent consistency. Isolated flushing cannot coincide with patient connection or
replacement; rinseback permits saline inlet and patient return only. Rejection
leaves the accepted patient state unchanged.

Response is `PATIENT5 json`; STATUS5 returns the same snapshot without advancing.
Base fields: sequence/time, volume[3], mass[3][6], concentration[3][6], gross_UF,
external in/out, net patient loss, weight, illustrative pH, residuals, and cumulative
diffusive/convective/input/output solutes. Online adds substitution water/solutes;
lifecycle adds flush in/out water/solutes. Hemodynamics adds vascular/circuit/lost
red cells and proteins, Hct/Cp, temperature, refill and residuals. Distributed adds
16 named compartment inventories, 12 dialysate concentration vectors, dialysate
volume and cumulative input/output/transfer/residual solute vectors. Exact JSON
keys and shape enforcement are in `compartments.validate_snapshot`; authoritative
current field inventory is maintained in [JSON fields](JSON_FIELDS.md).

## DX1 experiment administration

Request: `DX1 credential OP hex_json` plus LF. Credential is 64 lowercase hex digits;
JSON is ASCII-serialized then hex-encoded, at most 262144 decoded bytes. Frame limit
is `2*262144+256` bytes; full-frame deadline is 2 wall seconds. Duplicate/deep/nonfinite
JSON is rejected by the shared strict parser. Unauthorized replies disclose no active
run metadata.

Response: `DX1 OK|ERROR revision run_id state sequence virtual_time_ms hex_json`.
On error JSON contains `error`. Revision is an opaque potentially >64-bit integer;
clients must preserve exact digits. Run ID is `r` plus 16 hex digits, request ID 32
hex digits. A START retry can identify an earlier run, and the reply must retain that
run's identity rather than attaching an unrelated active run.

| OP | Exact request JSON keys | Result / semantic rule |
| --- | --- | --- |
| STATUS, DRAFT, PRESETS, RUNS | none | Status, current draft, available names, or at most 100 recent identified runs |
| LOAD | name, revision | Exact current revision, known preset; replace draft and increment revision |
| VALIDATE | configuration, revision | Validate complete schema-5 scenario; replace draft and increment revision |
| START | revision, request_id, wall_speed | Freeze accepted configuration; duplicate request ID must have same fingerprint; returns identified run |
| PAUSE, RESUME, STOP | run_id | Exact active run; reply is requested/observed broker state, not a fake actuator observation |
| REPLAY | run_id, request_id, wall_speed | Completed source run and matching frozen configuration hash; fresh services |
| COMPARE | left, right | Identified non-active runs; starts bounded artifact job |
| EXPORT | run_id | Identified non-active run; starts bounded artifact job |

STATUS includes current job completion/result. Active configuration never changes
because DRAFT changes. Artifact paths are not arbitrary client file paths. Token,
ID, revision, state and configured-size checks belong to the broker boundary.

## Current compatibility decision

Current MACHINE5/8 and OBS5/8/9/10 numeric domains agree between the C++ and Python
decoders. Actual parser tests exercise inclusive endpoints, just-outside values,
nonfinite numbers, and missing/surplus fields. Configuration rejection tests use the
actual plant for PHYSICAL9, FLUID9, DYNAMICS10, MACHINE5 and GUIDED8. The controlled
field dictionary specifies each tested position; these tests do not constitute
exhaustive fuzzing of every legacy message or semantic combination.

The initial dynamic dialysate inventory is now 50..1000 mL at both outer
configuration and plant initialization. The patient initializer accepts that whole
range. Runtime inventory has a different permitted domain because compliance and
flow change stored volume after initialization. Rejecting configurations above
1000 mL prevents late failure during patient INIT; it does not raise a model limit.

## Cold-start preparation extension

`PREPARATION11` configures the optional preparation model after DYNAMICS10 and
before MACHINE5/arming. `PREPFAULT11` injects explicit source/sensor faults outside
a prepared tick. Both are admin-only. OBS11 extends OBS10 with two boolean fields;
legacy observations retain their lengths. PREPARATION11 state appends 31 fields after
DYNAMICS10 in PHYSICS9, parsed by the Python physical-state decoder.
The [field dictionary](WIRE_FIELDS.md) fixes positions and bounds; the
[preparation design](PREPARATION.md) defines authority and startup semantics.

## Concentrate activity observation

OBS12 preserves OBS11 and adds modeled concentrate drives, sensed liquid outlet
flows and their freshness flag. [The field dictionary](WIRE_FIELDS.md) fixes bounds
and order. Prior observation versions remain accepted; new fields are unavailable
when absent. This adds presentation telemetry, not command authority.
