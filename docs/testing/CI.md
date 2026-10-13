# CI: short lifecycle and separate endurance campaign

Document ID STP-CI; revision 2; engineering verification, approval pending.
The PR gate gives quick feedback on complete behavior. Endurance remains a separate
obligation: passing a short run does not close [CLOSE-RES-01](CLOSURE.md).

## Source dependency check before expensive work

Run `python3 tools/dependency_report.py --check-only` before publishing. It checks
reviewed-file hashes, dependency/license metadata, action declarations and container
pins without a build, Docker or network. A changed reviewed file requires assessing
its actual impact and updating only its corresponding hash; automatic hash refresh
is not an acceptable review.

The general CI executes this same check first with a 60-second limit. A mismatch,
checker failure or timeout ends that job before downloads/builds/tests and preserves
its failed report and diagnostic log. It does not replace the later SBOM/image
checks, which still require actual built binaries and containers.

## On every pull request and push

The `verify` job retains the existing build, software and fault tests. The
`dynamic-resources` job runs the actual distributed physical HDF POST scenario
through isolated Compose services twice, with 600000 ms of delivered therapy.
At a 500 ms step this is 1200 treatment integration steps; the complete scheduled
fixture has 1440 steps (12 simulated minutes including other phases and margins).
Simulation time is not CI wall time: execution is unpaced batch.

Acceptance requires all twelve nominal phases in order: self-test, preparation,
priming, configuration, connected, treatment, finished, returning, disconnecting,
disconnected, cleaning and cleaned. The final state must be cleaned. Both the
retained treatment clock and the sum of treatment integration intervals must be
exactly 600000 ms. No unexpected alarm is accepted. Existing independent trajectory,
water/species, source identity and replay-hash checks remain enabled, as do the
64 MiB runner RSS criterion and 128 MiB container/no-OOM checks. Fault injection
remains in the main verification suite; the nominal lifecycle is not a fault test.

Each repetition has a 900-second wall budget; the job has 40 minutes including build,
verification and diagnostic collection. Failure is retained as failure, even when
artifacts were copied successfully.

```bash
python3 tools/verify_integrated.py --group dynamic-short --compose \
  --build-dir build/dynamic-native --output build/short-new --archive
```

Build the core and Compose images first as shown in the workflow. Output directories
must be new. The local pipe regression runs the same scheduled configuration twice
against the actual plant and patient. It checks full phase order, conservation,
exact treatment duration, replay, and rejection of missing phases or an alarm.
That regression does not replace the actual service/container run.

## Manual endurance campaign

In the `Simulator software verification` workflow, choose `Run workflow` and enable
`run_long`. The separate `dynamic-endurance` job executes the unchanged 100000-step
physical HDF POST fixture twice. It retains the original long-run criteria and
artifact verification. At 500 ms per tick, each run spans 13 h 53 min 20 s simulated;
it deliberately sustains treatment rather than returning after ten minutes.

The manual wall budget is selectable as 3600 or 7200 seconds per repetition; the
job has 300 minutes. Increasing this budget is not a claim that the earlier timeout
has been fixed. Endurance acceptance stays open until complete current-source runs
pass. No scheduled or PR-triggered endurance execution is configured.

```bash
python3 tools/verify_integrated.py --group dynamic-long --compose \
  --compose-timeout 7200 --build-dir build/dynamic-native \
  --output build/endurance-new --archive
```

## Recognizing progress and stalls

CI enables `--progress-every 100` in the runner. It writes `progress.json` atomically
and emits `DIALYSISLAB_PROGRESS` at initialization, each phase change, every 100
completed steps and final completion/abort. Fields identify completed/total ticks,
virtual time, treatment time, current phase, overall percentage, wall time and
average throughput. These wall-clock diagnostics never enter trajectory records,
so enabling them does not change the deterministic trajectory hash.

Compose output is streamed to the job log while retaining the captured output for
failure collection. The retained sidecar is the last reported accepted tick, not
necessarily the most recent tick at termination. If messages stop, its timestamp
and count provide a lower bound on progress; they do not by themselves locate the
blocked service. The final manifest, trajectory verification and job result remain
the authority for completion. The initial manifest's zero count is not used to
infer that no work happened. Both short and endurance diagnostics are retained
on failure; raw trajectories are not uploaded into CI logs.
