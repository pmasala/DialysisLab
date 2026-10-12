# Test protocol: treatment workflow and operator actions

Document ID STP-WF; revision 1; proposed current-baseline protocol. No result is
assigned by this document. Apply the [master evidence rules](PLAN.md). Requirements:
UI-REQ-002, M5-REQ-001…006, M6-REQ-001…006, M7-REQ-003, PHY-REQ-001, DYN-REQ-001.

## Fixture and observations

Use `device_guided.json` for operator tests, `dt_ms=500` and HD/HDF PRE/HDF POST
variants. Keep target values in the captured configuration; shorten time/volume
only in a separately identified test scenario. Observe phase, alarm mask, safe count,
connection/primed flags, phase/treatment time, flush/return counters, actual outputs,
UI state and patient ledgers. Record sensor and machine timestamps separately.

The automated [guided fixture](../../tests/test_guided.py) includes actual LVGL
rendering and a complete C++ plant-driven cycle. Its `GuidedProcessTests` exercises
real services; the in-process fixture does not establish socket isolation. The
[machine suite](../../tests/test_machine.py) covers older M5 guards and faults;
those results alone do not cover every new guided-state combination.

| Case | Stimulus and exact decision rule | Existing evidence route / coverage status |
| --- | --- | --- |
| WF-01 Initial tests | Start fresh; withhold an integrity signal. No preparation transition while checks are incomplete. Restore valid safe observations; transition only after all seven bits and configured duration. | `guided_view.cpp`, guided configuration/render test; complete check-by-check boundary matrix remains prospective |
| WF-02 Priming endpoint | Confirm PRIME from ready preparation. Accumulate measured flush; body draw/return stay zero. No completion below configured prime volume. At/above target with safe observations transition to configuration and set primed. | Guided state fixture checks below/equal target; process cycles check transactions; above-target/time-boundary coverage must be reported explicitly |
| WF-03 Connection | Attempt START before CONNECT; reject with unchanged state. Confirm CONNECT only after priming, then confirm START. Outputs stay stopped while connected but not started. | Guided state fixture and complete cycles |
| WF-04 Progress | At half target volume/time expect 50%; compare with authoritative counters, not wall time. Manual phases and stale/zero-flow ETA show unavailable. Paused treatment time must not increase. | `guided_view.cpp`; representative-user comprehension still open |
| WF-05 Live changes | During safe HDF therapy confirm a valid blood/active-substitution edit. New effective values appear without resetting treatment time. Reject mode/net-UF edits in therapy, out-of-range values and stale confirmations. HD substitution remains zero. | `tests/ui_regressions.py`, guided view fixture; actual UI verification required |
| WF-06 Treatment endpoint | Advance to just below and then across configured duration; automatic finished state only at endpoint. FINISH may stop early. No automatic RETURN. | Guided fixture/process cycles; record any tick quantization |
| WF-07 Return | Confirm RETURN while connected. Accumulate saline input and patient return, with UF/substitution zero. At target enter disconnecting and stop circulation. Residual cells remain in explicit inventories. | `test_return_salinity_body_gain_and_all_solute_balances`, physical full cycles |
| WF-08 Disconnect/clean | Reject CLEAN before disconnection. Confirm DISCONNECT; connection flag clears. Confirm CLEAN and require both time and flush target before cleaned. | Guided state and full-cycle fixtures |
| WF-09 Alarm/recovery | Inject an observed alarm during each active phase. Verify specified outputs before commit, ACK/silence do not clear, recovery does not restart. Require explicit RESUME. Terminal HALT cannot resume. | Machine fault suites plus guided fixture; exhaustive guided cross-product remains open |
| WF-10 Session and experiment pause | Change session with a pending request; old confirmation must fail. Pause experiment for >2 wall seconds: virtual time fixed, watchdog live. Device STOP must work while paused. | Device verification and `test_external_stop_while_paused_aborts_without_resume_or_another_tick` |

For volume phases the maximum target-crossing overshoot is the actual delivered
transfer of the crossing tick; inspect that quantity rather than assuming a nominal
flow. A UI screenshot alone cannot demonstrate server rejection or conservation.
Retain before/after captures together with transaction and state evidence.

## Human validation to commission

Ask representative intended simulator users to start the guided profile, explain the
priming endpoint, connect, adjust permitted flows, recognize a stale signal, return,
disconnect and recover without unintended restart. Define recruitment, critical-task
success and error criteria **before** collecting results. Do not convert software
widget tests into human usability approval. Responsible usability reviewer: unassigned.
