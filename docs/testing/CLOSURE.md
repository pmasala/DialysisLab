# Coverage closure, boundary cases and approval protocol

Document ID STP-CLOSE; proposed procedures, not execution results. This document
makes remaining work executable: it states setup, stimulus, observable decision and
required evidence. Read [master plan](PLAN.md) and [coverage matrix](COVERAGE.md).
No named person, due date or approval is invented here.

## Guided state/action matrix

Use a fresh configured guided machine per row, safe=3, mask=0 and the stated
connection/primed flags. Capture complete pre/post machine state and effective
outputs. The source is `Machine::guided_transition` and `advance_guided`; this is
the **server contract**, not a claim that all accepted actions are shown by the UI.

| Current state | Permitted phase actions / extra guards | Automatic endpoint |
| --- | --- | --- |
| self_test | STOP | All seven test bits, three safe observations, no alarm and elapsed test duration → preparation |
| preparation | PRIME with ready>=3; STOP | None |
| priming | STOP | Flush>=prime and safety guard → configuration; sets primed |
| configuration | CONNECT with primed; STOP | None |
| connected | START with primed, connected flag and remaining duration; STOP | None |
| treatment | PAUSE; FINISH; STOP | Delivered duration reached with safety guard → finished |
| paused | START with primed, connected flag and remaining duration; FINISH; STOP | No treatment-time advancement |
| stopped | RECOVER resets safe count; STOP | None |
| recovery | STOP; protective RESET is separate | RESET requires safe>=3, then recovery_ready |
| recovery_ready | RESUME saved stage, remaining duration if therapy; STOP | None |
| finished | RETURN with connected flag; STOP | None; never automatic return |
| returning | STOP | Returned volume>=target with safety guard → disconnecting |
| disconnecting | DISCONNECT clears connected flag; STOP | None |
| disconnected | CLEAN with connected flag false; STOP | None |
| cleaning | STOP | Both elapsed disinfection duration and flush>=prime → cleaned |
| cleaned | STOP accepted at server; no new treatment session | None |

All phase actions other than STOP and RECOVER require mask=0 and safe>=3. Terminal
HALT rejects every transition including STOP/RECOVER. ACK and SILENCE annotate
alarms through protection; they do not clear restrictions. Prescription has separate
rules: full edits in configuration/paused/connected; safe therapy permits blood and
active substitution flow edits while mode and net UF remain unchanged.

For each of 16 rows try every phase action
`PRIME CONNECT START PAUSE FINISH RETURN DISCONNECT CLEAN RESUME RECOVER STOP`,
and legacy `CONFIGURE COMPLETE`. Unlisted phase actions must reject with no state
mutation. Test terminal state separately. The oracle must be this reviewed table,
not another call to the implementation's transition function. Existing guided tests
sample this matrix; the full generated cross-product is still a planned campaign.

## Prospective cases with closure criteria

| Case / allocation | Procedure | Pass decision / evidence |
| --- | --- | --- |
| CLOSE-WF-01 / SWF-01 | Independently fail each of seven self-test bits, restore it; test elapsed duration below/equal/above and safe count 2/3 | No early exit; correct bit and endpoint. Retain observations, state and exact duration |
| CLOSE-WF-02 / SWF-02/05/06/07 | For priming/therapy/return/cleaning set counters just below/equal/above target; repeat safety guard false/true; for cleaning cross time complete/incomplete with volume complete/incomplete | Transition only under both phase and safety conditions; target overshoot <= actual crossing-tick transfer/time; no patient draw during isolated flush |
| CLOSE-WF-03 / SWF-08 | Run complete state/action matrix above, including saved recovery stages and terminal shutdown | Accepted/rejected set matches table; rejection preserves state; recovery alone never restarts outputs |
| CLOSE-FAULT-01 / SIF-02/03 | For active guided phases inject each observable hazard alone; then all hazard pairs where one blocks blood and another only prepared fluid; inject stale/missing/future/replay/invalid samples independently for each service | Effective restrictions are the union; no automatic restart; immutable before/after evidence and expected per-phase outputs. Hidden contamination is assessed separately from sensor observability |
| CLOSE-WIRE-01 / DOC-12/13 | Exercise below/at/above every documented numeric bound and one missing/surplus field per message. Compare C++ and Python where both decode that message | Common accepted domain and rejection effects agree, or approved compatibility exception identifies exact difference. Current selected serializer witnesses are not this exhaustive campaign |
| CLOSE-NUM-01 / MOD-10 | Freeze HD/PRE/POST configurations with flow/concentration/UF steps and chamber transients; repeat dt=500/250/125 ms, then refine further if error is unresolved | Compare aligned times, peak/settling pressure, levels, local concentrations and integrated transfer. Numerical error fits the output budget approved under STP-CAL; mass conservation alone is insufficient |
| CLOSE-RES-01 / FAIL resource scope | Execute 100000-tick current distributed configuration under actual Compose runner memory limit with telemetry/artifact capture | No OOM; completed/aborted artifacts readable with valid hashes; report peak RSS and disk usage. Long runs of a legacy configuration cannot close distributed resource scope |
| CLOSE-UI-01 / DOC-09 | Representative intended simulator users explain phase/remaining time, prime, connect, edit allowed flows, react to stale data/alarm, return, disconnect and recover | Record task success, assistance, errors and unintended actions. Preapprove critical-task/error definitions and population/sample rationale; every critical error gets disposition before validation acceptance |
| CLOSE-SEC-01 / DOC-10 | Map each entry point to role/session/input/resource tests; review shared host, parser, plant, sensors and writable artifacts as common causes | Each threat has prevention/detection/recovery evidence or explicit residual-risk disposition; container separation alone does not close independence |

Numerical/resource campaigns must record actual failures, timeout and collection
results. If maximum-size runs exceed the supported clock envelope, the acceptance
specification must first reconcile duration, ticks and step size; do not quietly
increase parser bounds or container limits solely to pass a test.

## Independent technical review package

Before requesting approval, the author supplies the exact candidate commit/tree,
change impact, requirements and atomic allocations, architecture/interface/model
changes, all executed result locations/hashes, missing cases, measurement uncertainty,
known anomalies and proposed residual limitations. Reproducing a tool-generated
report does not itself supply an independent scientific judgment.

| Review record | Required entry / closure |
| --- | --- |
| Scope and identity | Commit/tree, model variants, document revisions, intended use |
| Reviewer | Named person, competence for the subject, independence/conflict statement, date |
| Requirements | Each obligation has an unambiguous decision rule; exclusions retain rationale |
| Design and interfaces | Components/state ownership, ordering, units, numeric domains, failures and common causes match source |
| Verification | Map obligation → procedure → actual result; justify partial coverage and evidence reuse; no hidden skips |
| Scientific validity | Independent validation data, uncertainty and accepted operating envelope |
| Safety/security decisions | Normative applicability, classification, essential performance/risk criteria and residual risk approved by responsible roles |
| Finding disposition | ID, severity rationale, corrective action, owner/date, evidence and reviewer closure |
| Decision | Accept specified scope, accept with explicit limitations, or reject; signature/approved electronic record |

The maintainer assigns people and dates. The software/document author can prepare
this package and correct technical defects; they cannot fabricate independent
signatures, full-text standard access, measured data or an organization's risk
acceptance. Those are the concrete remaining external inputs, not a reason to leave
requirements, specifications or procedures unwritten.
