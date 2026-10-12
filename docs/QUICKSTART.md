# Run DialysisLab on Linux or WSL2

Choose a local run first, or use Docker if you already have it configured.
All commands below run from the repository root. Use a fresh output directory
for each experiment.

## 1. Run without a display

You need a C++17 compiler, CMake 3.16 or newer, make and Python 3.9 or newer.
On WSL2, use Linux tools and keep the checkout in the Linux filesystem.

```bash
cmake -S . -B build/core -DCMAKE_BUILD_TYPE=Release
cmake --build build/core --parallel 3
PYTHONPATH=python python3 -m dialysislab.runner --local --build-dir build/core --config scenarios/machine_hdf_pre.json --output build/first-hdf
```

The runner starts the services, follows the scenario and writes results.
Open `build/first-hdf/manifest.json` to see the outcome and completed tick count.
`trajectory.jsonl` contains one committed record per line. A failed run may contain
only part of the requested experiment; the manifest records errors and stop status.

The [simulation guide](SIMULATION.md) explains what these models represent.
For other examples, explore `scenarios/machine_hd.json` and
`scenarios/machine_hdf_post.json`.

## 2. Build the graphical applications

In addition to the core prerequisites, install X11/Xext development headers and
libraries, including `X11/extensions/Xext.h`. Use an existing authorized Linux X11
or WSLg display. The project fetcher downloads pinned GUI dependencies into the
build directory; downloads require network access.

```bash
python3 tools/fetch_gui.py --cache build/gui-deps
cmake -S . -B build/gui -DCMAKE_BUILD_TYPE=Release -DDIALYSISLAB_GUI=ON
cmake --build build/gui --parallel 3
```

For headers in a user-owned prefix, CMake accepts
`-DDIALYSISLAB_XEXT_PREFIX=/absolute/prefix` and
`-DXEXT_LIB=/absolute/path/libXext.so.6`.

## Alternative: a headless Docker run

You need Docker Engine and Compose available to your account. Build images after
changing source inputs; initial downloads require network access.

```bash
SOURCE_REVISION=$(git rev-parse HEAD) docker compose --profile device-ui build
SCENARIO=machine_hdf_pre docker compose up --no-build --abort-on-container-exit --exit-code-from runner
docker compose cp runner:/results/. /tmp/my-hdf-results
```

For a source archive without Git metadata, replace the first command with
`SOURCE_REVISION=unavailable docker compose --profile device-ui build`.

Collect results even when the runner fails. Only after successful extraction,
remove the deployment with `docker compose down --volumes --remove-orphans`.
If extraction fails, keep the volumes so the data can be recovered.
`python3 tools/recover_trajectory.py --help` describes inspection of partial trajectories.

## Native interactive device or external console

```bash
SDL_VIDEODRIVER=x11 python3 tools/run_device_demo.py --build-dir build/gui --output build/my-device
# Or render without a display, with an explicitly bounded wall duration:
python3 tools/run_device_demo.py --build-dir build/gui --headless --seconds 15 --output build/my-device-headless
```

The interactive device starts in preparation: prime, configure, enter a simulated
prescription, confirm and start. Pause/stop/recovery and protection are validated
by the services. The UI's stale observations are not replaced by internal truth.
Use a preconfigured calendar such as `--config scenarios/machine_air.json` for an
automated fault demonstration. Window closure requests and observes HALT.

For external experiment administration, keep the broker in one terminal:

```bash
PYTHONPATH=python python3 -m dialysislab.experiments --build-dir build/gui --output build/my-experiments --api-dir /tmp/my-dialysis-api
# Second terminal:
SDL_VIDEODRIVER=x11 build/gui/sim-console --api-dir /tmp/my-dialysis-api
# Batch alternative:
python3 tools/experiment.py --api-dir /tmp/my-dialysis-api load --preset machine_hdf_post
python3 tools/experiment.py --api-dir /tmp/my-dialysis-api --wait start
python3 tools/experiment.py --api-dir /tmp/my-dialysis-api runs
```

The GUI exposes full validated configuration JSON and presets, including patient,
circuit, dialyzer, mode, workflow and fault calendar. Load/validate a draft before
Start. Pause freezes virtual time while watchdog heartbeats continue. Replay starts
fresh services from the immutable run configuration. Compare verifies identities
and trajectory hashes; Export streams only named run artifacts. Closing this
console leaves the experiment running. Stop the broker with Ctrl-C/SIGTERM after
collecting results; keep its token file private and never pass tokens in arguments.

## Both graphical applications in Compose

```bash
test -S /tmp/.X11-unix/X0
docker compose -f compose.experiments.yaml -f compose.experiments-x11.yaml --profile console --profile device-ui up -d
```

The selected override uses existing display `:0` and a read-only X0 socket mount.
No `xhost` relaxation or privileged container is needed. If the authorized socket
is unavailable, use the headless profile and record graphical verification BLOCKED.
X11/host administration are trusted; this is not a hostile multi-tenant deployment.
For automated actual widgets use:

```bash
python3 tools/verify_experiments_compose.py --with-device --output build/both-headless
python3 tools/verify_experiments_compose.py --with-device --graphical --output build/both-graphical
```

Device requests cannot edit a scheduled experiment. Device STOP still acts directly
and aborts even when the experiment is paused; it never needs console RESUME.
A new experiment changes service sessions, invalidates old confirmations and
clears device trends. Wall-stale sensor data during a virtual pause is expected.

Preserve results before deleting this deployment's volumes:

```bash
docker compose -f compose.experiments.yaml stop scenario-runner
docker compose -f compose.experiments.yaml logs --no-color > /tmp/my-experiment-services.log
docker compose -f compose.experiments.yaml cp scenario-runner:/results/. /tmp/my-experiment-results
# Only after successful extraction:
docker compose -f compose.experiments.yaml --profile console --profile device-ui down --volumes --remove-orphans
```

A failed extraction leaves resources recoverable. Verifier reports include their
exact project-specific recovery commands. Do not prune unknown volumes. A broker
crash can leave an interrupted run with unconfirmed outputs; preserve it and use
fresh services/API sessions. No automatic treatment resume is supported.

## Numerical and package checks

`verify_integrated.py --group matrix` runs 18 synthetic configurations twice;
`--group faults` checks the declared detector/response fixtures. Add `--compose`
for isolated services. `--group long --archive` runs sustained HDF for 100,000 ticks,
requires at least 2048 MiB free for raw/extraction storage and verifies gzip round trips
before replacing owned raw duplicates. Recover with the recorded gzip command.
Run long verifications sequentially; free-space checks do not reserve storage
against concurrent writers. Aggregate reports replace their prior checkpoint
atomically, preserving earlier completed cases if a later write runs out of space.
The 27.8-hour virtual run is numerical stress, not a validated prescription.

`verify_package.py --output /tmp/fresh-package-check` builds two identical source
archives, extracts and runs the actual native tests and widgets. It can accept
`--deps-cache`, `--xext-prefix` and `--xext-library` for previously verified local
prerequisites. Its report distinguishes the package's SHA-256 from the absent Git
revision inside an extracted tree. Exact trajectory replay applies to identified
build/configuration; cross-toolchain numerical limits remain explicitly documented.


## Understand the results

Read [How the simulation works](SIMULATION.md) for the fluid paths, pressure model, solute exchange and weight calculation. See the [documentation guide](README.md) for other topics.

## Inspect circuits and trends

See [Visual inspection](UI_INSPECTION.md) for animated circuit views, selectable
trends and the full numerical inspector. To inspect saved data without a broker:

```bash
build/gui/sim-console --recorded /absolute/path/to/trajectory.jsonl
```

The native interactive demo defaults to the [guided treatment workflow](GUIDED_TREATMENT.md),
including initial tests, priming, connection, blood return and simulated disinfection.
