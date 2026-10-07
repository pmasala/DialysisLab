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

## M2–M9

Not yet invoked. Before each invocation, record the phase, base SHA, candidate
SHA, exact command and report destination here. Retain output and exit status;
read all findings even when the command exits zero. Register blocked attempts
without replacing them with a self-review approval.
