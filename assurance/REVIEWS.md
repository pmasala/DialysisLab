# Automatic review register

Exactly one automatic review per phase; no review-fix-review cycle. AI review is
not independent human assurance, clinical review, risk acceptance or approval.
`codex review --help` was executed successfully on 2026-10-08: `--base <BRANCH>`
and a positional instructions prompt are supported by the installed CLI. A
read-only review must cover all commits since the fixed phase base.

## M1 — supplied review, consumed

The repository owner's supplied review is the M1 review. Original CLI command,
reviewer identity and reviewed SHA were not supplied; do not invent them. The
review identified three concrete P2 defects in the original M1 implementation.

| Finding | Manifestation | Disposition / correction | Verification / evidence |
| --- | --- | --- | --- |
| M1-R1, P2 | Lost control or protection STEP response after its decision reached the plant allowed a normal COMMIT. | Fixed `da5ccc2`: no COMMIT/ADVANCE on failed STEP; terminal HALT discards pending decisions; separately record requested/acknowledged/observed stop. | `test_rpc_abort.py`: six real-process cases including both lost replies, failed HALT, failed observation and watchdog. `evidence/m1-review/native-tests.json`. |
| M1-R2, P2 | Trajectory accumulation and full serialization copies exceeded 128 MiB. | Fixed `da5ccc2`: JSONL v1 incremental writer/hash, recoverable completed prefix and versioned manifest. | `test_trajectory.py`; two real 100000-tick Compose runs, RSS max 22.50 MiB, cgroup max 71.14 MiB. `evidence/m1-review/review-docker.json`. |
| M1-R3, P2 | Failed Compose up skipped evidence collection then deleted volumes. | Fixed `da5ccc2`: unconditional collection, preserve original code, distinct collection errors, retain results on extraction failure with recovery instructions. | Five unit cases and three actual Docker failures/recovery. `evidence/m1-review/review-docker.json`. |

Evidence checkpoint `1999741`; native and sanitizer suites each 47/47; actual
Compose and repeatability checks passed. Release gaps remain open.

## M2 — single review completed; corrections verified

Base `1999741a63c57ed25b236c8739bfd4408a5cbd7f`; candidate
`9aeee604b7c63d7a607786340a00a477721cbae8`. One invocation of `codex review --base
1999741`, with read-only sandbox, no approvals, and explicit defect-review
instructions. CLI 0.161.0 returned zero and **three applicable P2 findings**.
Exact argv, timestamps and final output: [review.json](evidence/m2/review.json).
Full local transcript: `build/reviews/m2-output.txt`, hash retained in the report.
No second review will be invoked.

| Finding | Scenario | Correction | Regression |
| --- | --- | --- | --- |
| M2-R1, P2 | Watchdog between COMMIT and CSTATE2 loses the just-committed draw/return ledger. | Atomic COMMIT2 reply includes physical and circuit states; end-of-run observed failure is recorded. | Real watchdog after commit; preserve water/storage, observe stopped outputs and abort. |
| M2-R2, P2 | Stale Compose image/nominal artifacts can satisfy a requested occlusion run. | Compare full canonical configuration/digest and source hash map; require actual named occlusion timing. | Reject wrong config, forged digest and stale source hashes. |
| M2-R3, P2 | Drainage toward initial 100000 mL fails on a 1.65e-18 mL overshoot. | Bounded explicit FLUID2 roundoff (1e-9 per correction, 1e-8 absolute run budget), reported separately. | Real 300-tick drainage, genuine overfill rejection and exhausted correction budget. |

Corrections committed as `2108e55`. Final native and sanitizer suites passed
58/58 each; six M2 Compose runs, four M1 Compose runs and two isolation probes
passed. Native/container trajectories match. [Final evidence](evidence/m2/README.md)
identifies each build/configuration. Independent model calibration and risk
acceptance remain open.

## M3 — single review completed; corrections verified

Base `40533e4d09643d8913ecc4795757362e034cbb20`; candidate
`ec832d00b6d6ba42aff8591778f2fb50ffd8b348`. One read-only invocation returned
zero and five applicable findings. Exact command/output: [review.json](evidence/m3/review.json).
No second review will run. All 14 targeted patient tests pass after corrections.

| Finding | Scenario / correction | Regression |
| --- | --- | --- |
| M3-R1 P2 | Equilibrium at 1000 mmol/L rejected roundoff; retain bounded computed slack without clipping mass. | Concentration ceiling numerical and real transport tests. |
| M3-R2 P2 | JSON integer 10**400 terminated patient; bound integers before float conversion. | Actual INIT3/ADVANCE3 rejection, service survival and unchanged state. |
| M3-R3 P2 | Forged compartment volumes passed evidence checks; cross-check all three volumes with prime/storage and totals. | Rehashed corrupt body/circuit volume evidence rejected. |
| M3-R4 P2 | NaN/overflowing JSON numbers passed residual comparisons; strict finite JSON and residual checks. | Rehashed NaN/1e999 evidence rejected. |
| M3-R5 P3 | Indicator error after commit advanced rejected transaction; validate complete proposed state before accepting, subtract logarithms. | Subnormal bicarbonate and forced response validation failure leave state atomic. |

Corrections: `64645fd`. Final native/sanitizer 72/72 each; eight native/eight
Compose M3 runs, six M2/four M1 Compose runs and two isolation probes passed.
[Evidence](evidence/m3/README.md) records exact identities and limits.
Automatic review is not independent physiological or regulatory approval.

## M4 — single review completed; corrections verified

Base `47ffc5efa5ca1cd2878a2924b182d1bb72a7a8e3`; candidate
`9a2d2df97eeb8cfa1784d6300a3d516f39d8ad51`. One read-only invocation returned
zero and **one P1 plus five P2 findings**. Exact argv/output: [review.json](evidence/m4/review.json).
No second review will run. All 15 targeted treatment regressions pass after fixes.

| Finding | Scenario / correction | Regression |
| --- | --- | --- |
| M4-R1 P1 | QUALITY4 delayed UF/exchange isolation until COMMIT; immediately zero live fluid actuators/coefficients, preserving blood and ledgers. | Real STATUS4/CSTATE3 without COMMIT, then conflicting demand and commit. |
| M4-R2 P2 | Computed mixture 1000.0000000000001 rejected by ADVANCE4; preserve bounded computed slack through the dialysate boundary. | Actual 1 ms run at concentration ceiling; strict initial limit retained. |
| M4-R3 P2 | Higher substitution head violates blood-only ceiling; use the envelope of configured pressure sources. | Real one-node unequal-head pre-HDF, no invented pressure clipping. |
| M4-R4 P2 | Gross UF above 100000 mL inherits v1 volume limit; STATE4 has duration/rate-derived gross limit. | Decoder/stop boundary test and full treatment_100000 native/Compose acceptance. |
| M4-R5 P2 | Forged replacement rate passes evidence safety checks; require zero under both latches and consistency with tick volumes. | Rehashed hard/quality latch and nominal rate corruption rejected. |
| M4-R6 P2 | Forged substitution-solute totals pass; compare every species with independent integration. | Rehashed ledger corruption rejected for both latch types. |

Corrections `cca9ce6`: 87/87 native/sanitizer tests each, 24 native/24 Compose
treatment runs, 14 M2/M3 plus four M1 Compose regressions and two isolation probes.
Two native/two Compose 100000-tick runs pass, including large cumulative UF,
confirmed native HALT, exact hashes and unchanged RSS limits. [Evidence](evidence/m4/README.md).

## M6–M9

Not yet invoked. Freeze phase base/candidate and retain one command/output per phase.

## M5 — single review completed; findings fixed and verified

- Base: `e1c8ae2c28cea14ac195e62cfb87ac9a8bb02e6e`.
- Candidate: `a490984dbcf807cd08a0ce1a1a1702f95c6db613`.
- Command: `codex -c sandbox_mode="read-only" -c approval_policy="never" -c developer_instructions=... review --base e1c8ae2c28cea14ac195e62cfb87ac9a8bb02e6e`.
- Exact argv/timestamps/exit and full local transcript: `build/reviews/m5.json`,
  `build/reviews/m5-output.txt`; invocation count **1**, exit 0 with two findings.
- M5-R1 (P2): accumulated flush source/waste cancellation perturbs an isolated
  100000 mL body at tick 12713. Fix: compensated body-boundary transfers, plus
  unchanged independent 1e-6 mL whole-system check; no clipping or wider bounds.
  Regression: `test_isolated_100000_tick_flush_keeps_body_ceiling_and_conserves_mass`
  and real `machine_priming_100000` native/Compose runs.
- M5-R2 (P2): a rehashed air-alarm record with active outputs passes the evidence
  checker. Fix: derive hazard-specific actuator constraints from the M5 mask and
  cross-check actual rates/volumes, clamp, quality/blood latches and alarm names.
  Regression: `test_evidence_cross_checks_alarm_mask_latches_and_every_actuator_class`.

Both findings are applicable; correction commits and actual final evidence are
recorded below. No second review is authorized or planned.
The AI review is not human, clinical or regulatory approval.

M5-R1/R2 corrections: `c54422c`, 20/20 targeted regressions passed. The first
real 100000-tick native and Compose attempts then both aborted after 4662
completed ticks: `std::stod` rejected representable subnormal concentration
`2.110269719209234e-308` during TRANSPORT3. This is integration finding M5-V1
(P2), not another review. Native/Compose failed manifests and partial trajectories
remain in `build/m5-final-long-{native,compose}`; Compose retained artifacts before
cleanup and propagated the failure. Fix: decimal `from_chars` parsing that accepts
finite representable subnormals while rejecting overflow/unrepresentable underflow,
hex and nonfinite values. The actual transport-boundary regression passes. Repeat
all pertinent verification against the final clean correction build; preliminary
runs concurrent with follow-up edits are diagnostic, not final evidence.

M5 final disposition: implementation `443f73f` passes 108/108 native and sanitizer
tests, 22 native/22 Compose short runs, 12 compatibility plus four M1 Compose runs,
three isolation probes and two native/two Compose 100000-tick priming runs. Both
review findings and M5-V1 are fixed. See `evidence/m5/review.json`,
`evidence/m5/summary.json` and `evidence/m5/README.md` for commits, commands, actual
results, retained failures and limitations. No second review was performed.


## M6 — candidate prepared; one review pending

Base `445c667939d1fcdf37e46dea697f3c881dfbadca` was fixed before implementation.
`codex review --help` was checked; the CLI supports `review --base` and read-only
configuration overrides. Candidate verification: 114/114 native regressions,
5/5 actual-widget headless/native WSLg/sanitizer tests, and successful headless
and graphical separate-container widget workflows. These working-tree results
are preliminary. Record the exact candidate/argv/time/output before invoking the
single phase review; then dispositions, regression evidence and correction commits.
No review of M6 has yet been invoked at this checkpoint. AI review is not clinical,
regulatory, hardware-independence or human approval.


### M6 single review result and disposition

Candidate `00baa5805f9f9408ef0648ec64e065d67a2cc9c8`; fixed base
`445c667939d1fcdf37e46dea697f3c881dfbadca`. One invocation from
2026-10-08T01:58:14Z to 02:09:25Z returned exit 0 **with six P2 findings**.
Exact argv and raw output: `build/reviews/m6.json`, `build/reviews/m6-output.txt`.
Review is consumed; no second invocation is authorized. All six are applicable.

| ID / severity | Scenario and correction | Targeted regression |
| --- | --- | --- |
| M6-R1 P2 | Same-session reconnect falsely refreshes a frozen sample. Preserve sample age separately from confirmation/trend generation. | `test_same_session_reconnections_do_not_refresh_frozen_samples` |
| M6-R2 P2 | Batched SDL down/up loses clicks including STOP. Queue bounded pointer transitions for LVGL consumption. | `test_coalesced_sdl_clicks_and_exact_prescription_confirmation` |
| M6-R3 P2 | Fractional prescription is rounded in the confirmation. Share exact round-trip decimal text between confirmation and request. | Same real SDL prescription test; `0.04 mL/min` remains nonzero and exact. |
| M6-R4 P2 | Maximum hazards plus disconnect overlap delivery/ACK text. Reserve adequate regions and check actual LVGL bounds. | `test_all_latched_alarms_and_disconnect_fit_without_overlapping_intent` |
| M6-R5 P2 | Unexpected demo abort returns zero after HALT. Return failure unless completed or explicitly observed normal window closure. | `test_unexpected_workflow_abort_returns_failure_despite_confirmed_halt` |
| M6-R6 P2 | Slow pacing delays window-close HALT by 100 seconds. Add bounded cancellation checks during paced waits without repeating tick actions. | `test_window_closure_interrupts_100_second_pacing_wait` |

Corrections and final evidence are in progress; no final PASS is inferred from
review exit zero. Preserve preliminary failures/results and record the correction
commit plus clean-build regressions before advancing M7.


M6 review corrections are committed as `5552622`; all ten targeted tests pass in
headless, actual WSLg and instrumented builds, and native/Compose regressions pass.
Final visual inspection then found **M6-V1 (P2)**: theme-default dark dialog text
has insufficient contrast on its dark background. This is an integration finding,
not a second review. Explicitly set a light dialog foreground and check at least
7:1 luminance contrast in the actual rendered confirmation-detail pixels. This
software display criterion is not clinical usability or accessibility conformity.
The complete `5552622` results remain in `build/m6-verified-*`; the unpublished
evidence draft is retained in `build/m6-5552622-evidence-draft`. Refresh GUI evidence
after the contrast correction; core services/model code are unchanged.


M6 final disposition: review fixes `5552622`, visual integration fix `2ee31ad`.
The final clean build passes 114/114 native and sanitizer tests, 10/10 UI/demo
checks in headless/WSLg/sanitizer modes, two actual widget-driven Compose
deployments, twelve native/twelve Compose exact-replay scenarios and four M1 runs
plus three isolation probes. `evidence/m6/review.json` and `summary.json` bind
findings, commits, actual tests and rendered artifacts. M6 review count remains
one. M7–M9 reviews have not run.

## M7 — implementation candidate verification; review not yet invoked

Fixed base `26211813a79d5f05720071de0b51df8089997476`. `codex review --help`
was checked before this phase. Real broker/role regressions cover pause/liveness,
immutable configuration, direct device STOP, replay/export, malformed administration,
failed services and recoverable interrupted evidence. Three actual ImGui tests run
headless, WSLg and with sanitizers; repeated headless/graphical Compose runs use
fresh processes in separate role containers. Retain the candidate SHA and single
review command/output before invocation. No M7 review has run at this checkpoint.

Pre-candidate diagnostics retained in `build/m7-*`: first Compose startup failed
because an unquoted flow-list tmpfs string split its mount options. Corrected YAML;
available volumes were extracted and confirmed empty before cleanup (`m7-compose-first/recovery.json`).
The new altered-patient fixture initially violated the existing initial concentration
consistency check, then attempted configuration before 200 mL priming completed.
The fixture now matches concentrations and waits sufficient declared virtual ticks;
no model limit or assurance check was relaxed. A stale-editor integration check also
requires the GUI to retain its loaded draft revision rather than adopt newer polling
revisions, preventing another client's configuration from being silently overwritten.

M7 candidate validation: 123/123 native and sanitizer tests each, 3/3 real console
tests in headless/WSLg/sanitizer modes, 10/10 device-UI regressions, ten native/ten
Compose model runs and two repeated-experiment console deployments pass. Exact
preliminary reports are in `build/m7-*-candidate*`; final clean evidence follows
the one review and any applicable corrections.

### M7 single review result — corrections required

Candidate `1cf008cfe05e6d61ea7892f278615cd7088a7b64`, base
`26211813a79d5f05720071de0b51df8089997476`. One read-only CLI invocation,
2026-10-08T03:10:47Z–03:24:13Z, exit 0 **with one P1 and ten P2 findings**.
Exact argv/output: `build/reviews/m7.json`, `build/reviews/m7-output.txt`.
The M7 review is consumed; no second review may run. All findings are applicable.

| ID | Severity | Reproduced problem / required regression |
| --- | --- | --- |
| M7-R1 | P1 | Journal write failure prevents STOP cancellation; prove actual HALT despite journal I/O error. |
| M7-R2 | P2 | START/REPLAY can race broker shutdown; reject new work before draining workers. |
| M7-R3 | P2 | Incomplete run directory prevents inventory startup; preserve/quarantine it and recover valid runs. |
| M7-R4 | P2 | Ownership released while artifact worker still writes; retain lock until every writer terminates. |
| M7-R5 | P2 | Reused revision after broker restart accepts stale editor; bind revision to broker incarnation. |
| M7-R6 | P2 | Accepted configuration exceeds stored JSON reader bound; cover maximum workflow/fault calendar and manifest overhead. |
| M7-R7 | P2 | Exhausted journal prevents terminal metadata; persist outcome/stop independently. |
| M7-R8 | P2 | Contradictory experiment build/hash/count accepted by comparison/export; reject all redundant identity mismatches. |
| M7-R9 | P2 | STATUS overwrites a command reply before rendering consumes it; retain replies through deliberate render stall. |
| M7-R10 | P2 | Manifest says unpaced while broker paces; record actual pacing owner/speed without a second wait loop. |
| M7-R11 | P2 | Random run IDs determine last-100 inventory after restart; sort persisted creation times before limiting. |

Additional integration finding M7-V1 (P2), reproduced in the same review transcript
but not included in its final finding list: unauthenticated error headers reveal
run/state/clock metadata. Return a neutral header before authentication and test
without a valid token. This does not constitute another review invocation.

M7 corrections implemented; 20/20 targeted broker/service tests and 5/5 actual
console tests pass in the working tree. Regressions map R1/R7 to journal-failure and
event-cap tests; R2/R4 to shutdown/real ownership-lock tests; R3/R11 to recovery and
chronological inventory; R5/R9 to actual broker restart/render-stall widgets; R6 to
a real 1000-tick, 1000-workflow/1000-fault replay/export; R8 to nine independently
corrupted identity fields; R10 to initial/final pacing metadata and elapsed time.
M7-V1 verifies a neutral unauthenticated header during an actual running experiment.
The maximum-calendar fixture uses SILENCE annotations valid in PREPARATION rather
than unauthorized prescription transitions; machine guards remain unchanged.
Record correction commit and clean final integration evidence next. No second review.

M7 final disposition: correction commit `bbecf598154f0dc00b787ed839141d96a704ce0d`
passes 134/134 native/sanitizer tests each, five actual console flows in each of
headless/WSLg/instrumented modes, ten device-UI regressions, ten native/ten Compose
model runs, two complete console deployments with retained aborted runs, four M1
Compose runs and three isolation probes. All eleven review findings and M7-V1 are
fixed. `evidence/m7/review.json`, `summary.json` and `README.md` bind the single
review, exact correction/build/configuration identities, tests and artifacts.
M8–M9 reviews have not run; M1–M7 reviews are consumed.
