# Detailed design: a treatment from start to finish

Document ID SDD-01; revision 1; review candidate. Requirements: UI-REQ-002,
M5-REQ-001…006, M4-REQ-001…004, PHY-REQ-001, DYN-REQ-001.
Previous: [Architecture](../ARCHITECTURE.md). Next: [Models](MODELS.md).

The guided sequence is enabled by the scenario's `guided` object. The plant's
`Machine` owns the phase; the screen only displays it. The same server guards apply
to hidden UI buttons, scripted requests and direct protocol calls. Legacy scenarios
without `guided` retain the earlier M5 state sequence for reproducible tests.

## State, ownership and entry

[Machine::guided_transition / advance_guided](../../src/machine.hpp) implement
operator guards and automatic endpoints. [Control](../../src/control.cpp) queues
confirmed requests; [plant](../../src/plant.cpp) applies them at the coherent tick
boundary. [Python configuration](../../python/dialysislab/machine.py) validates and
serializes the scenario. `patient_connected`, `primed`, alarm mask, safe-sample
count and terminal-stop flag are authoritative plant state, not UI assumptions.

For ordinary transitions the machine must not be terminal, its alarm mask must be
zero and it must have three consecutive safe observations. STOP and the entry into
recovery are explicit exceptions; neither permits treatment outputs.

| Phase (internal name) | Entry and operation | Exit criterion / next state |
| --- | --- | --- |
| Initial tests (`self_test`) | Guided initialization; isolated flushing and dialysate preparation | All seven check bits set, safe-state guard, and `test_ms` elapsed → preparation |
| Preparation (`preparation`) | Tests completed; wait for operator while fluid preparation continues | Confirm PRIME with `ready >= 3` → priming; reset phase flush counter |
| Priming (`priming`) | Circulate external fluid through the isolated circuit; patient draw/return zero | `phase_flush >= prime` with safe-state guard → configuration; set `primed` |
| Connection (`configuration`) | Circuit remains isolated; review prescription | Confirm CONNECT when primed → connected; set patient connection flag |
| Connected (`connected`) | Patient connection acknowledged, outputs stopped | Confirm START, primed and connected, time remaining → treatment |
| Therapy (`treatment`) | Demand blood flow, substitution and gross UF; record actual outputs | PAUSE → paused; FINISH or delivered treatment duration reached → finished |
| Paused (`paused`) | Treatment outputs stopped; treatment elapsed time held | Confirm START after guard checks → treatment, preserving accumulated treatment time |
| Treatment ended (`finished`) | No automatic saline return | Confirm RETURN while connected → returning; reset return counter |
| Blood return (`returning`) | Saline enters circuit, return enters patient; UF/substitution off | `rinse_volume >= rinse_target` with guard → disconnecting |
| Disconnection (`disconnecting`) | Circulation stopped; wait for operator | Confirm DISCONNECT → disconnected; clear connection flag |
| Disconnected (`disconnected`) | Patient isolated | Confirm CLEAN → cleaning; clear primed state and flush counter |
| Disinfection (`cleaning`) | Isolated simulated flush cycle | Both `disinfection_ms` elapsed and `phase_flush >= prime` → cleaned |
| Ready (`cleaned`) | No automatic reuse of the patient/run | External tool starts a fresh simulation |

Connections are acknowledged simulation events, not needle/line position sensors.
The initial checks cover observation validity, temperature, conductivity, air/leak
signals, filter integrity/pressure, supply readiness and blood-pump response. They
do not implement a manufacturer's full functional self-test sequence.

## What progress means

The UI computes progress from authoritative counters in
[guided_ui::progress](../../src/ui/guided.hpp). It never increments a cosmetic timer
independently of the plant. If data are stale, protection is active or a stop is
terminal, the remaining-time estimate is unavailable.

| Phase | Percentage | Remaining virtual time |
| --- | --- | --- |
| Tests | Minimum of passed-check fraction and elapsed/duration | Nonnegative duration minus elapsed; checks may still prevent completion |
| Priming | Delivered flush / prime target, capped at 100% | Remaining volume / observed pump flow; unavailable at zero flow |
| Therapy | Delivered treatment time / prescription duration | Duration minus delivered time; paused time does not count |
| Return | Delivered return / return target, capped at 100% | Remaining volume / observed flow |
| Disinfection | Minimum of time fraction and flush-volume fraction | Maximum of time and volume estimates when flow is available |
| Manual confirmation | Waiting state, not an invented physical percentage | No ETA; elapsed waiting time remains visible |

The default [interactive scenario](../../scenarios/device_guided.json) uses 10 s
for initial tests, 4 h of delivered therapy, 60 s for disinfection, approximately
150.1593 mL prime volume and 200 mL return volume. At 300 mL/min the ideal priming
estimate is 30.03 s and return 40 s. Pump dynamics and protective interruptions can
extend these times. Endpoint detection is tick-based: crossing a target can overshoot
by a step's transfer. These values exercise software, not a clinically validated
priming volume or disinfection exposure.

## Treatment control and live edits

Requested gross UF is net prescription plus observed substitution, limited to
140 mL/min by control. Actual membrane filtration comes from the physical solve;
actual supply and pump limits can prevent meeting the request. The net meter and
patient weight must therefore remain separate quantities.

During therapy, confirmed prescriptions may change blood flow (0–500 mL/min) and
the active HDF substitution flow (2–120 mL/min), with blood plus substitution at
most 500. HD requires substitution zero. Modality and net UF cannot change until
paused. Net UF input is 0–20 mL/min. These are simulator bounds. A live edit does
not reset treatment time or clear protection. Restart from blood flow <=10 mL/min
uses the existing short pump-response grace, not a bypass of pressure or air checks.

## Stop, alarms and recovery

`Machine::protect` latches the union of active hazards. Pressure, low flow, air,
blood leak, invalid measurement and communications hazards inhibit blood outputs.
Any alarm inhibits fluid therapy. During priming, tests, return and cleaning, any
alarm also blocks the external flushing/return pump. ACK and silence only annotate
alarms. Reset is a separate confirmed protective request after recovery checks;
RESUME is another explicit operation in guided mode.

STOP remembers the interrupted phase. Recoverable checks can lead to recovery-ready,
not automatic circulation. Flow/filter alarms that cannot be demonstrated clear
remain latched. Terminal communication/HALT failures require fresh processes. Freeze
of chamber storage on isolation is a model decision, not physical depressurization.

## Conservation and failure seams

In priming/cleaning the patient is isolated and all source/waste transfers have
separate ledgers. In return, saline source and patient return replace ordinary blood
draw; returned sodium/chloride use the saline concentration of 154 mmol/L. Residual
red cells remain explicit in the circuit inventory. A 200 mL target is not a claim
that all blood has been recovered. Disinfection models circulation and endpoints,
not microbial kill or chemical clearance.

Verification: [workflow protocol](../testing/WORKFLOW.md),
[guided tests](../../tests/test_guided.py), [actual LVGL/state fixture](../../tests/guided_view.cpp),
[machine fault tests](../../tests/test_machine.py). Open issues include independent
user validation, validated phase thresholds and complete guided guard-boundary
coverage; see the audit rather than inferring those from the table.
