# Test protocol: faults, security, resources and deployment

Document ID STP-FAIL; revision 1; proposed protocol. Requirements: REQ-001/002/004/005,
M1-REQ-005…009, M5-REQ-003…006, M7-REQ-003…006, M8-REQ-001…006, M9-REQ-001…005.
Use the [master plan](PLAN.md) and retain the original failure plus recovery evidence.

## Real-process and container matrix

| Case | Setup / stimulus | Acceptance and retained proof |
| --- | --- | --- |
| FAIL-01 Lost decision reply | In turn, allow control/protection command acceptance at plant, then lose STEP reply | Other role attempted; no COMMIT/ADVANCE; HALT cancels pending tick; requested, acknowledged and observed stop facts distinct. `test_lost_step_each_role_stops_and_invalidates_pending_m5_decisions` |
| FAIL-02 Missing/old measurements | Invalid, missing, stale, future and replayed samples on each role channel | Unusable protection data restrict outputs before that tick commits; control-only fault cannot rewrite the other sample. Preserve sequence and onset/observation/action times |
| FAIL-03 Hostile demand/reset | Submit positive demand with latched alarm; ACK/silence/reset outside allowed recovery | Active restrictions survive. Three safe samples alone do not auto-restart; terminal and unproven faults stay stopped. Machine arbitration suites |
| FAIL-04 Process death | Kill each decision process, runner owner and patient at pre/post-commit boundaries | No implicit restart/resume; watchdog acts within declared wall bound; partial artifacts retained; unknown outputs never called observed zero |
| FAIL-05 Authority and parsing | Actual device container probes admin/patient/other-role paths; spoof producer; send duplicate/deep/oversized/trickle frames | Denials occur at real boundaries; bounded parser/deadline, no silent approval of malformed data. Security tests and Compose probes |
| FAIL-06 Failed collection | Runner abort, pre-start failure and artifact extraction failure | Original failure survives; available logs/manifests retained; failed extraction keeps volumes/recovery commands. `tests/test_compose_collection.py` |
| FAIL-07 Long run | 100000 ticks in identified 128 MiB runner container; retain RSS and all ordered records, repeat hash checks | Existing acceptance <=64 MiB RSS, no OOM, streaming integrity. Legacy long-run evidence does not prove all maximum-size dynamic scenarios; that envelope needs separate execution |
| FAIL-08 Simultaneous GUIs | Actual LVGL and ImGui on services; pause/replay/STOP, session replacement and denied admin access | Observed state, real widget input and captures agree. Run headless and actual WSLg/native graphical profile separately |
| FAIL-09 Package/replay | Extract allowlisted archive into fresh directory, build and run; replay exact frozen configuration | Source/build/config/trajectory identities agree; stale image and tampered artifact rejected; failure cannot disappear from exported evidence |
| FAIL-10 CI/tool failures | Make a checker crash, timeout, emit malformed report or omit required evidence | Software verification fails; only structurally valid open release obligations are classified BLOCKED. `tests/test_ci.py` |

The application sources, native platform packages and container platform packages
have distinct inventories. Record actual image identity, dependency notices and
advisory coverage. Scanner unavailable means BLOCKED, not no vulnerabilities. Existing
advisory findings need explicit applicability and residual-risk decisions.

## Practical execution

Full execution uses `python3 tools/ci_verify.py --output build/ci-new` on a host with
Docker, compiler and graphical prerequisites. See [Development](../DEVELOPMENT.md)
for targeted commands. Socket-free tests do not establish IPC isolation; containers
are required for mount authority; headless captures do not establish display or
human usability. Do not silently substitute one environment for another.

Record unsupported environments, skipped tests, timing interference and maximum
observed resources. Coverage of fault combinations must be justified against the
risk analysis; a list of injected faults is not a complete safety argument.
