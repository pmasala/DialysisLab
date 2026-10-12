# M9 integrated verification evidence

Technical M1–M9 software/numerical integration is COMPLETE for the declared
synthetic scope. Runtime build `935692a` was clean at configure; harness corrections
`0051ca1` and `4e50564` preserve application source/binaries. The five `m9-test-*.json`
files bind each acceptance criterion to specific actual reports and byte hashes.
Historical M1–M8 trace test records remain unchanged.

## Actual results

- 158/158  native and 158/158 ASan/UBSan regressions;10 LVGL widget tests and 6 ImGui
widget tests, with all 6 console tests also passing under sanitizers.
- 18 mode/patient/dialyzer combinations twice per deployment:36  native/36 Compose
runs. The Compose matrix actually ran under host `umask 077`.
- 15 fault scenarios twice per deployment:30  native/30 Compose runs, including
recovery and latent contamination without an invented sensor response.
- Two native and two Compose100000-tick HDF runs, each with 99896 treatment ticks,
118445.139108 mL gross UF, no nominal alarm and ordered virtual timestamps.
- Maximum independent water/species residuals1.94879248738e-7 mL and
1.29413848526e-8 mmol, below 1e-6. Same-build and observed cross-deployment hashes
match exactly; long trajectory SHA-256 is
`59e342fe0a5fe174630dcd3a2206169c5019268d197f7f0d44c65d75a8a82269`.
- Actual simultaneous headless/WSLg clients exercise pause/stale observations,
request rejection, replay, comparison/export and device STOP without another
tick. Aborted state/observed stop arrive in 0.113 s/0.316 s, within the5 s Docker bound.

Runner peak RSS is21770240 bytes (20.76 MiB),43.24 MiB below the64 MiB acceptance
bound. **Total cgroup peak reached 128 MiB: zero measured headroom at that peak**;
no inspected service was OOM-killed. RSS margin is not reserved container capacity.
M1's earlier actual simpler100000-tick Compose runs had19.47 MiB RSS and 68.96 MiB
cgroup peak; their separate evidence remains in `../m8/m1-long-failures.json`.
No threshold, tolerance, tick count or container memory limit was relaxed.

## Review, failures and recovery

Exactly one M9 review compared `4719ebc` against `eb290de`. Its one P1/two P2 findings
are fixed and regressed. `review.json` records scenarios, commits and tests;
V1–V7 identify additional integration/test/storage findings. No second review ran.
Failed initial fixtures, candidate CI and harness attempts remain under `failed/`.

Concurrent earlier long attempts hit shared-host ENOSPC. Their original partial
bytes remain losslessly archived; recovery verifies45445  native/37674 Docker
complete records and excludes only torn final lines. Shutdown remains UNCONFIRMED
because final manifests could not persist. The Docker volume was removed only
after original-volume hashes matched recovered files. Fresh complete sequential
runs above provide acceptance. Atomic aggregate checkpoints and a partial-ENOSPC
regression now preserve earlier completed cases. `storage/` gives restoration
commands for owned archived trajectories, captures and build artifacts.

## Package, dependencies and CI

`package-code.json` records actual clean `4e50564` source packaging: two byte-identical
445-file archives, SHA-256
`52f39e80da4c2e96273eddca0ae4562facec75cd6aa65abba15ce0af2b0c43e4`, followed by
158 tests,10 device and 6 console widget tests from extracted sources.
`package-nogit.json` independently records successful invocation from a tree
without `.git`; its earlier package/test identity is kept distinct. All six
Release executables from checkout and extracted source were byte-identical with
the recorded toolchain; this is not a cross-platform binary reproducibility claim.
The final delivery archive, including this evidence, is verified externally after
the evidence commit to avoid a source archive hashing its own verification report.

Hosted CI 37747683346 passes. All 43 original artifacts recover byte for byte;
all 21 report and 21 command-log digests cross-check. `hosted/` retains actual JSON
and reversible UTF-8 command logs. Five actual SBOMs validate; limited Cppcheck
analysis reports no findings. The recorded M8 scan still has73 open advisory IDs,
without human risk acceptance or a clean-image claim.

Exact commands, build/configuration identities, dependencies and outcomes are in
the reports; operational commands are in `docs/QUICKSTART.md`. Long raw JSONL v1
is retained as verified gzip archives; restore using each storage record before
existing readers. Source/publication and Docker allowlists remain explicit.

## Remaining obligations

The models are synthetic and uncalibrated. Clinical/model/usability validation,
sterile-fluid quality, hardware independence, substantive human review and
standards conformity are not established. 184 checklist entries,12 edition/
applicability gaps and nine prerequisites remain open; release gates are BLOCKED.
No process, Docker or WSLg permission block remains on the tested environment.
