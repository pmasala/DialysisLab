# M7 external experiments

Phase base: `26211813a79d5f05720071de0b51df8089997476`. This increment adds
administration of **synthetic** experiments; it does not expand model validity.
Existing M1–M6 equations, limits, clinical/standards gaps and release gates apply.

## Requirements and acceptance declared before implementation

| Requirement | Behavior / criterion | Risk |
| --- | --- | --- |
| M7-REQ-001 | Separate C++ Dear ImGui console and Python broker run actual native/Compose services; actual widgets render on headless software and available Linux/WSLg X11. | HAZ-001,004 |
| M7-REQ-002 | Edit and validate patient, circuit, synthetic dialyzer, modality, workflow and fault calendar before a run; immutable accepted configuration/seed identify every run. | HAZ-001,003 |
| M7-REQ-003 | Start, pause, resume and stop at virtual barriers; paused virtual sequence remains fixed for >2 wall seconds while independent liveness continues. A stop records requested/acknowledged/observed HALT. | HAZ-002,004 |
| M7-REQ-004 | Replay a completed scheduled experiment in fresh services; unchanged configuration/build yields identical JSONL bytes. Compare/export stream validated artifacts, retaining partial failed runs. | HAZ-003,004 |
| M7-REQ-005 | Administrative truth/status/export is available only on the experiment channel, absent from device UI. Bad credentials, stale revisions/run IDs, path traversal and oversize frames are rejected. | HAZ-001 |
| M7-REQ-006 | Multiple native/container experiments need no Docker socket or service reset bypass; crashes/restarts retain evidence and never resume a treatment implicitly. | HAZ-001,002 |

## Architecture and authority

`sim-console` uses the existing pinned SDL2 software backend and pinned Dear ImGui
core. It connects only to the external Python scenario-runner broker. The broker
owns configuration, virtual scheduling and result storage; it never supplies hidden
truth to control/protection. Native runs create four fresh processes. The Compose
deployment keeps four role containers: fixed-command supervisors observe a small
read-only activation record (run identifier only), start fresh role processes and
retain their logs. No Docker daemon socket, arbitrary command or arbitrary output
path is exposed through the experiment API. Device UI remains a separate client.

Runs are scheduled experiments: all clinical-device requests and faults are in the
immutable configuration at integer virtual tick boundaries. `SCHEDULE7` on each
private role service enables a one-way policy before stepping. `OPERATOR7` routes
the runner's existing confirmed requests through that private service. Device
observations remain available; external mutations are rejected as `scheduled`.
Emergency device STOP is always allowed and immediately reaches plant arbitration;
it marks the experiment interrupted, rejects further STEP and prevents an exact
replay claim. Ordinary M5/M6 deployments retain their interactive behavior.

## Administrative contract DX1

Unix stream endpoint `experiment/broker.sock`; generated 256-bit bearer token in
`experiment/token`, mode 0600, never included in command arguments/logs/exports.
The directory is private to the administrator. Token secrecy is not isolation from
the native same UID. Compose mounts this volume only in broker/console.

One request per connection: ASCII `DX1 TOKEN OP PAYLOAD\n`, where PAYLOAD is the
hex encoding of UTF-8 strict JSON. Reply: `DX1 OK REVISION RUN STATE SEQUENCE TIME_MS PAYLOAD\n` (or `ERROR`).
The fixed metadata header is versioned; sequence is -1 before the first commit.
Decoded JSON is at most 256 KiB, frame at most 524544 bytes, wall timeout 2 seconds;
nonfinite numbers, unknown keys and extra frames are rejected. Persisted JSON has
a separate 1 MiB bound to accommodate indentation and build/stop metadata for
accepted maximum calendars; wire bounds remain unchanged. Unauthenticated errors
carry neutral revision/run/state/time fields. Strings/errors do
not echo credentials. No unsolicited messages. Units remain explicit JSON keys.

Operations: STATUS (bounded latest committed truth, state, sequence, virtual ms),
PRESETS/LOAD, DRAFT/VALIDATE (revision compare-and-swap), START (revision and unique
request identifier), PAUSE/RESUME/STOP (current run identifier), RUNS, REPLAY,
COMPARE and EXPORT (validated generated run identifiers). These streaming
artifact operations return a job ID immediately; STATUS reports the bounded job
result without blocking STOP/pause or the rendering thread. START/REPLAY duplicate
request IDs return the original run; IDs cannot be reused for a different request.
Revisions are opaque exact decimal integers: a random 128-bit broker incarnation
and a bounded 32-bit edit counter. Preserve all digits; do not convert to binary64.
A restart cannot make an old editor valid by repeating its edit count. Command
replies remain queued until the GUI consumes them; periodic status is coalesced.
Status distinguishes requested pause from acknowledged paused barrier and reports
wall receipt age separately from virtual time. Draft edits never change a live run.
Only one run may be active. One bounded console job executes off the rendering
thread. Closing/reconnecting the console does not change the experiment.

Run IDs are generated, never paths. RUNS sorts persisted UTC creation timestamps
before returning the latest 100 entries, including after restart. Artifacts are configuration, JSONL v1, manifest
v2, experiment metadata/event journal and service logs. Hashes cover actual bytes.
Export ZIP contains only explicitly named generated artifacts from that run; no
recursive repository/archive inclusion. Comparison reports configuration/build
identity and exact trajectory hashes separately from final patient differences.
Only completed, verified, scheduled records qualify for exact replay comparison.
Experiment metadata must agree with its manifest on build/configuration, digest,
count, scheduling, pacing owner/speed, outcome and observed stop. Broker pacing is
recorded in both initial/final manifests without enabling internal runner pacing.

Pause freezes the next barrier, not wall watchdogs or protection. Resume rebases
pacing (no catch-up burst). STOP is cooperative scheduler cancellation, serviced
within bounded 100 ms waits plus existing RPC timeouts; plant watchdog remains an
independent fallback. Journal failure cannot veto STOP. Terminal metadata is attempted independently
of the capped event journal; journal errors remain explicit in experiment metadata.
Broker shutdown first rejects new work, requests stop and collects its actual result.
Output ownership remains held until every run/artifact writer has terminated.
Broker crash leaves a recoverable JSONL prefix and an interrupted/unconfirmed run;
restart never retries the old run or claims zero outputs without observation.

## Implementation and verification order

1. Pin/assess ImGui and notices; extend selected GUI build only.
2. Add scheduled role policy, bounded broker/API and fresh-role orchestration.
3. Build actual console widgets plus headless CLI; streaming compare/export.
4. Test real pause/liveness/stop/replay, credentials/input/role boundaries, failure
   evidence and actual GUI workflows in native, sanitizer and Compose deployments.
5. Commit candidate, run the single review against the fixed base, correct findings,
   regress and bind final evidence to source/configuration/build identities.

No throughput, hard real-time, clinical usability, calibration, microbiological
quality or physical isolation claim follows from these software acceptance checks.

## Operating commands

Use fresh API/results directories. The broker and console are separate processes;
closing the console leaves the experiment running. End the broker with SIGTERM or
Ctrl-C so it records HALT before exiting. Native same-UID access is trusted.

```bash
python3 tools/fetch_gui.py
cmake -S . -B build/gui -DCMAKE_BUILD_TYPE=Release -DDIALYSISLAB_GUI=ON
cmake --build build/gui --parallel 3
PYTHONPATH=python python3 -m dialysislab.experiments --build-dir build/gui --output build/experiments --api-dir /tmp/dl-experiment-api
# In another terminal, Linux X11/WSLg (set DISPLAY=:0 only if that socket exists):
DISPLAY=:0 SDL_VIDEODRIVER=x11 build/gui/sim-console --api-dir /tmp/dl-experiment-api
# Batch alternative; the same backend/configuration/authorization applies:
python3 tools/experiment.py --api-dir /tmp/dl-experiment-api load --preset machine_hdf_pre
python3 tools/experiment.py --api-dir /tmp/dl-experiment-api --wait start
python3 tools/experiment.py --api-dir /tmp/dl-experiment-api runs
python3 tools/experiment.py --api-dir /tmp/dl-experiment-api --wait replay --run-id RUN_ID
python3 tools/experiment.py --api-dir /tmp/dl-experiment-api --wait compare --run-id RUN_A --right RUN_B
python3 tools/experiment.py --api-dir /tmp/dl-experiment-api --wait export --run-id RUN_ID
```

The M6 dependency runbook documents native platform prerequisites and the optional
local Xext header prefix; no global installation bypass is required. `--headless`
renders the same actual console widgets with SDL's dummy software backend.

```bash
SOURCE_REVISION=$(git rev-parse HEAD) docker compose --profile device-ui build
docker compose -f compose.experiments.yaml up -d plant control protection patient scenario-runner
docker compose -f compose.experiments.yaml exec -T scenario-runner python3 tools/experiment.py --api-dir /experiment --wait start
# Separate graphical console (requires the existing X0 socket):
docker compose -f compose.experiments.yaml -f compose.experiments-x11.yaml --profile console up sim-console
# Preserve results BEFORE removing named volumes:
docker compose -f compose.experiments.yaml stop scenario-runner
docker compose -f compose.experiments.yaml cp scenario-runner:/results/. /tmp/dl-experiment-results
docker compose -f compose.experiments.yaml down --volumes --remove-orphans
```

Do not remove result volumes if copying fails. Streaming exports are under
`results/exports/`; only available named artifacts are included. Interrupted
prefix exports include `recovery.json`, preserve original partial bytes and do
not claim a completed run or confirmed final outputs. Artifact jobs are bounded to
one concurrent job and do not block simulation control. Inventory is bounded to
1024 runs per result directory, last 100 listed; existing run IDs remain usable.

After abrupt broker failure, never reuse stale sockets blindly. Preserve results
and logs, stop the old role processes/containers, then use a fresh API directory
(native) or explicitly remove the known stopped broker's socket before restarting
its deployment. Incomplete/corrupt run metadata is quarantined in place and listed in STATUS; it
does not prevent recovery of other runs. Preserve these directories for manual
recovery rather than treating them as verified or deleting them. The output
ownership lock prevents concurrent brokers. Old active
runs become `interrupted`, with stop unconfirmed; no automatic treatment resume.
Native parent-death cleanup and separate writable device producer volumes are
implemented in M8; trusted-host/common-cause limits still apply.

M9 integration addition: the broker polls scheduled-control CHECK7 while virtual
time is paused. An observed external device STOP aborts the run without RESUME or
another PREPARE/COMMIT; communication failure uses the same terminal HALT policy.
The paused last committed truth/sensor sample remains historical, never proof of
current active outputs. Actual stop is separately queried from plant state.
