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

## M4–M9

Not yet invoked. Freeze phase base/candidate and retain one command/output per phase.
