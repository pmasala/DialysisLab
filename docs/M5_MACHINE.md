# M5 lifecycle, protection and alarm contract

Phase base `e1c8ae2c28cea14ac195e62cfb87ac9a8bb02e6e`, fixed before implementation.
The machine treats simulated patients only. Thresholds, readiness counters and
cleaning criteria are synthetic software parameters; they are not clinical limits,
air-clearance/disinfection validation or hardware independence evidence.

## Requirements and acceptance

| Requirement | Acceptance fixed before implementation | Links |
| --- | --- | --- |
| M5-REQ-001 | Preparation, priming, configuration, treatment, pause, stop, recovery, finished and cleaning states have guarded transitions, authoritative observed state and safe startup/end. Every legal/illegal transition tested. | HAZ-002,004,005 / M5-DES-001 / M5-TEST-001 |
| M5-REQ-002 | Priming/cleaning flush circuit from external source to waste with patient isolated; all water and six species conserved within 1e-6 mL/mmol including source/waste ledgers. | HAZ-003,006 / M5-DES-002 / M5-TEST-002 |
| M5-REQ-003 | Pressure, low flow, air, blood leak, quality, balance and validity/comms impose hazard-specific latched plant constraints immediately, without control cooperation. Aggregate simultaneous hazards. | HAZ-002,003,004,006 / M5-DES-003 / M5-TEST-003 |
| M5-REQ-004 | Acknowledgment/silence cannot release constraints; overrides rejected. Reset requires recovery plus three consecutive safe observations. Ambiguous failure/restart never auto-resumes. | HAZ-002,004,005 / M5-DES-004 / M5-TEST-004 |
| M5-REQ-005 | Device-facing bounded contracts expose modeled observations/authoritative machine state and validated requests, never patient/fault/clock/truth administration. | HAZ-001,004,005 / M5-DES-005 / M5-TEST-005 |
| M5-REQ-006 | Actual process/Compose workflow/fault/restart/replay tests, numerical balances and previous regressions identify build/configuration/evidence. | HAZ-001–006 / M5-DES-006 / M5-TEST-006 |

## Lifecycle and boundaries

The plant enforces the state and permitted actuator classes; control validates and
requests transitions. Device clients see requested/pending state separately from
the effective plant state. A request acknowledgment is not evidence of completion.
The normal path is PREPARATION -> PRIMING -> CONFIGURATION -> TREATMENT -> FINISHED
-> CLEANING -> CLEANED. Treatment can pause/resume, or stop -> RECOVERY -> PAUSED
before an explicit restart of treatment. STOP is available from active states;
terminal communication/protocol HALT requires a new run. No automatic restart.

Preparation requires three valid in-range observation cycles. Priming and cleaning
use the configured prime volume as a **synthetic flushed-volume criterion**, plus
valid quality observations. This is one modeled mixing-volume exchange, not proof
of removing all air/solute or achieving disinfection. A short demonstration may
choose a smaller, explicitly configured synthetic circuit prime. Prescription
changes are permitted only in CONFIGURATION/PAUSED. FINISHED disconnects the body;
CLEANED leaves outputs stopped. Illegal domain transitions return rejection without
corrupting state; malformed plant frames retain terminal protocol-failure policy.

During PRIMING/CLEANING, circuit pump draw comes from the prepared external source
and return drains to waste. Patient E draw/return are zero. The conservative C
matrix receives source concentration times actual draw and loses end-state C
concentration times actual return. New cumulative external flush-in/out water and
solute ledgers close the body+circuit accounting boundary. Body exchange/generation
continue. UF, replacement and membrane exchange are off during these flushes.
All other non-treatment states isolate the patient circuit and freeze its storage.
Priming pressure is retained; it must never be silently reset to pass a recovery test.

During treatment, control requests gross UF = net UF prescription + previous
measured replacement flow, bounded by 140 mL/min. Actual membrane hydraulics remain
a constraint: a physically unachievable net prescription can cause a balance alarm.
Device net balance is measured UF minus measured replacement; body-volume loss
additionally includes circuit storage and external patient contributions. The
UI must label these separately and cannot access hidden body volume or weight.

## Detection and actuator policy

All detection uses frozen sensor observations with sequence, virtual timestamp and
validity. A measured threshold crossing must impose its constraint before COMMIT
of that observation cycle (<=one dt virtual time). A physical change arising during
a committed tick may await the next observation (<=one further dt). Wall liveness
remains a separate 2 s plant watchdog; bounded RPC deadlines remain 500 ms.

| Hazard | Synthetic detector / rationale | Action and latch |
| --- | --- | --- |
| Pressure | Configured positive pressure ceiling, same origin as prior demo; monitor modeled upstream/downstream pressure. | Stop circuit pump, clamp patient, stop UF/substitution/exchange. |
| Low blood flow | Measured pump flow <1 mL/min with prescribed >10, after two treatment cycles; demonstrates stalled delivery. | Same blood isolation. |
| Air / blood leak | Dimensionless modeled detector signal >=0.5; no bubble/optical calibration. | Same blood isolation. |
| Temperature/composition/filter/integrity/route/supply | M4 observed quality thresholds, with state-aware supply expectation. | In treatment retain blood circulation; stop UF/substitution/exchange. In external flushing also stop flush pump. |
| Fluid balance | Absolute difference between measured net cumulative removal and integrated net prescription >5 mL; demonstrates metering/achievability faults. | Fluid-only isolation during treatment. |
| Invalid/stale/missing observation | Existing sequence/time/validity rules. | Blood and fluid isolation. |
| Process/communications failure | Missing STEP result, missing decision or wall heartbeat. | Terminal HALT; pending decisions invalidated, actual stop observed separately. |

Alarm masks accumulate constraints; clearing one condition cannot release another.
ACK changes acknowledgment only. SILENCE has a bounded virtual duration (maximum
120000 ms), affects annunciation only and expires deterministically. New alarms
annunciate despite older acknowledgments/silence. All protective OVERRIDE requests
are explicitly rejected in this simulator. A failed protection process is a fault,
not permission to continue; its latched constraints live at plant arbitration.

Recovery requires stopped patient outputs, explicit RECOVERY state and at least
three consecutive valid observations with all relevant measured conditions safe.
Reset is performed by protection, not control/UI. High retained pressure that
cannot meet the safe observation condition remains blocked; use a new run rather
than inventing a pressure reset. A supply functional test, if required for reset,
must deliver to waste while the patient is isolated and report waste separately.
Restarted services cannot clear plant latches, epochs or terminal status. New
processes use fresh sockets/runtime/run identity; stale sockets are not deleted
implicitly. Native same-UID operation remains a trusted development fixture.

The current version has no pump/filter functional recovery test: low-flow and
filter-pressure latches require a new run. Removing their driving command would
hide a continuing obstruction; zero stopped-flow pressure is insufficient reset
evidence. A modeled supply-pressure switch supports supply recovery, separately
from the flow monitor and its explicitly injectable stuck-high failure. Starting
treatment requires completed priming even after STOP/RECOVER/RESET. Stopping before
priming completes, or during cleaning, requires a fresh run before treatment.

## Version-5 contracts before implementation

Scenario schema 5 / `m5-device-1` extends schema 4 with a bounded workflow schedule
and protection/lifecycle settings. Schemas 1–4 remain compatible. Initialization
selects version 5 before arming. Sequence order, integer time, bounded frame sizes,
strict finite numbers and atomic commits remain unchanged.

Control/protection get SENSE5 observations, including modeled pressure/flow/quality,
air/leak detector signals and fluid counters; no patient inventories, injected
fault flags or hidden detector truth. A separate machine metadata view exposes
prescription/state/constraints (not physical truth). STEP5 uses the configured
prescription/state rather than trusting new runner setpoints every tick. The
atomic COMMIT5 reply binds physical, circuit, online and machine/flush snapshots.
INIT5/ADVANCE5/STATUS5/PATIENT5 add explicit external flush ledgers to the Python
patient. The ordered fields below are implemented by `machine.hpp`/`machine.py`.

A new `device` socket volume contains `control.sock` and `protection.sock` device
service endpoints. UI gets only this volume. Control/protection retain their own
plant-role volume and publish their device endpoints; neither gains patient/admin
mounts. The existing control volume contains a plant actuator endpoint and must
not be mounted into device UI. Compose checks must verify this precise new boundary,
not merely remove the old allowlist assertion.

Critical start/prescription/reset requests use a bounded pending confirmation.
Successful confirmation queues a request for a coherent control boundary; effective
state remains separately observed. STOP acts immediately. Only one pending request
is allowed, expiration uses wall time, and confirmation identifiers never establish
security authentication. Applied virtual-time events are recorded for replay.
UI receives no fault injection, patient configuration or clock controls.

## Wire fields and persistence

All frames retain the `DL1` prefix, ASCII/newline delimiter, 4096-byte cap and
500 ms deadline. Numbers are finite decimal values; sequences are 0..99999,
timestamps 0..100000000 integer virtual milliseconds. No clock is read from UI.

- Admin `MACHINE5 blood net_uf replacement pressure_limit prime` initializes
  version 5 once after ONLINE4 and before PREPARE. Flows are mL/min, pressure
  mmHg, prime mL. Schema 5 retains M4 ranges; workflow/fault lists are <=1000.
- `STEP5 n t` on each decision service consumes `SENSE5 n t`. `OBS5` contains
  all 12 OBS4 fields, followed by downstream pressure (mmHg), air/leak signals
  (dimensionless 0..1), metered cumulative UF/substitution (mL), and supply
  pressure-switch readiness (0/1). Pump flow is measured before pre-injection.
  These are ideal transducers except scheduled instrumentation faults; no
  claim of calibrated detector physics. Stale/invalid semantics apply to the
  entire frame. `device:meter_bias` adds a nonnegative UF-meter bias in mL.
- `DEMAND5 n t blood gross_uf replacement` is control-only, with gross UF
  0..140 mL/min. `PROTECT5 n t mask valid` is protection-only. Bits 0..12 are
  pressure, low flow, air, blood leak, measurement, temperature, composition,
  filter pressure, integrity, route, supply, balance, communications. The plant
  combines masks and gates outputs immediately; legacy PERMIT/TRIP/QUALITY4
  are invalid after MACHINE5. Missing decisions make COMMIT5 terminally fail.
- `META5` returns `MACHINE5 n t stage mode blood net_uf replacement
  pressure_limit prime mask acknowledged silence_until safe ready cycles
  revision action terminal phase_flush flush_in flush_out expected_net
  measured_net flush_in_tick flush_out_tick`. Stage indexes follow the lifecycle
  order in `machine.py`; mode is HD=0, pre=1, post=2. Counters are mL, flows
  mL/min, silence deadline ms. Flush counters are ideal circuit flowmeter
  totals, not body-volume estimates. No patient inventory or contaminant truth
  appears in this device metadata. `revision/action` records applied changes.
- `COMMIT5 n t` returns atomic `COMMITTED5 STATE4 ... CIRCUIT3 ... ONLINE4 ...
  MACHINE5 ...`. ADVANCE5 extends ADVANCE4 JSON with `flush_in_mL`,
  `flush_out_mL`, `flush_mmol_L` (six species). During flush, body draw/return
  are zero; simultaneous body flow/replacement/exchange and flush is rejected.
  PATIENT5 adds cumulative flush water and six-species input/output ledgers.
- Device `STATUS5` returns `VIEW5 MACHINE5 ... OBS5 ... INTENT5 id state result`.
  Authoritative machine state and the last frozen sensor observation have
  distinct timestamps. A STOP acknowledgment or terminal state does not turn
  old flow samples into freshly observed zero outputs. Clients must display
  age/disconnection. Before initialization the response is `REJECT uninitialized`.
- Device control `REQUEST5 action` or `PRESCRIBE5 mode blood net_uf replacement`
  returns `CONFIRM5 id`. `CONFIRM5 id` returns `QUEUED5 id`; the single pending
  request expires after 10 wall seconds. It applies at the next control STEP5
  before its demand. Applied/rejected/expired status is observable. `STOP5`
  acts immediately and cancels pending control intent. Prescription changes
  require CONFIGURATION/PAUSED. Route mismatch is assessed during active flow,
  avoiding an invented mismatch between a stopped routing change and its next
  sensor update.
- Device protection accepts ACK5, SILENCE5 duration (0..120000 virtual ms),
  REQUEST5 RESET and confirmation. Reset applies after protection has assessed
  that tick. ACK/silence never release constraints; new bits clear both
  annotations. OVERRIDE and administration/actuator/service-STOP operations
  are rejected. IDs are bounded transaction identifiers, not authentication.

Flowmeter balance integrates the net prescription only while fluid therapy is
enabled, so a protective pause does not itself manufacture a balance alarm.
RESET reconciles its reference to the latest metered net counter. Actual gross
UF, replacement, body changes and circuit storage remain separate conserved
ledgers. Confirmation delivery and the applied machine revision are both retained
in trajectory records; rejected scheduled actions abort with the normal confirmed/
unconfirmed HALT evidence policy.

Body volume in version 5 is reconstructed from compensated **body-boundary**
draw/return/post-substitution plus generic external transfers. Isolated flush
contributes exactly zero to this balance; subtracting accumulated source/waste
counters must not perturb a patient at the 100000 mL ceiling. An additional
whole-system water residual still checks UF/replacement/storage/flush ledgers
within 1e-6 mL. Nothing is clipped and the accepted physical volume bound is
unchanged. Evidence verification derives blood/fluid constraints from each M5
alarm mask and checks actual outputs, clamp and redundant latch fields together.
The prolonged real-process flush additionally exercises concentrations below the
smallest normal double: decimal parsing accepts representable finite subnormals,
but rejects overflow, unrepresentable underflow, NaN/infinity and hex spellings.
The physical model and mass tolerances are unchanged.

The shared device volume presently lets control/protection reach each other's
device-facing annotation/request endpoints. Neither can reach the other's plant
role, patient or admin volume; every reset still crosses protection's safe-state
guard. Producer endpoint ownership and denial-of-service/common-cause risks remain
part of M8 hardening, not implied solved by the device menu or socket names.

## Verification and limitations

Exercise normal HD/pre/post workflows, each protective action, simultaneous hazards,
latent/stuck detector cases, invalid data, conflicting demands, reset/ack/silence,
control/protection loss/restart and observation failures. Compare external flush,
body/circuit/UF/substitution water and solute ledgers independently. Verify real
native/Compose endpoints and denied administration access. Inspect changed code
once after the candidate commit; fix findings and regress without another review.

The detector channels are declared synthetic instrumentation models, not calibrated
bubble transport or blood-leak optics. Common sensor/plant/runner/host causes remain;
wall watchdog tests do not prove hard real time. Calibration, clinical/quality
validation, independent risk acceptance and standards applicability remain open.

### M7 scheduled experiment extension

On private control/protection service sockets, `SCHEDULE7` before the first STEP
locks the session into scheduled mode; no runtime unlock exists. `OPERATOR7`
prefixes the existing device request/confirmation/status operations for the trusted
runner. Device endpoints still expose observations and session6 freshness, but
reject ordinary mutations with `REJECT scheduled`. Control's device STOP remains
immediate, cancels intent and records external interruption; further STEP5 and
`CHECK7` reject it so the runner aborts without normal COMMIT. This does not alter
the default M5/M6 interactive mode. See [experiment contract](M7_EXPERIMENTS.md).
