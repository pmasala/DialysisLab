# DialysisLab

[DialysisLab](https://github.com/pmasala/DialysisLab) is an MIT-licensed dialysis
simulator and development template for requirements, architecture, risks,
cybersecurity, verification and traceability. **Only simulated patients and
simulated equipment are supported.** Models and alarm thresholds are synthetic
and uncalibrated; software tests do not establish clinical safety, sterile fluid,
hardware independence or standards conformity.

The working implementation covers HD, pre/post HDF, online replacement preparation,
configurable hydraulic components/dialyzers, Python patient water and six species,
guarded machine workflows, independent protective decisions, an LVGL device UI
and a separate ImGui experiment console. M1–M9 technical verification and integrated source packaging are recorded;
model/clinical validation and normative release obligations remain open. The authoritative
[status](assurance/STATUS.md) identifies actual results and remaining work.

## Quick start: headless

Use Linux or WSL2 with CMake >=3.16, a C++17 compiler, make and Python >=3.9.
The core uses the C++ and Python standard libraries. Run from the repository root;
use a fresh output path for each command.

```bash
cmake -S . -B build/core -DCMAKE_BUILD_TYPE=Release
cmake --build build/core --parallel 3
PYTHONPATH=python python3 -m dialysislab.runner --local --build-dir build/core --config scenarios/machine_hdf_pre.json --output build/demo-hdf
python3 tools/verify_m1.py --build-dir build/core --output build/core-tests.json
```

The runner starts separate plant/control/protection/patient processes. JSONL records
and the manifest identify configuration, seed, virtual time, build, outcomes and
actual-byte hashes. Protection constrains plant arbitration directly; a conflicting
control command cannot release it. Failed RPCs use terminal HALT and distinguish
requested, acknowledged and actually observed output state.

## Docker Compose

Docker Engine with Compose is required; the application containers use no network,
run as UID 10001 with read-only roots, dropped capabilities and 128 MiB limits.
Initial image/dependency downloads require network access with TLS verification.
The [dependency assessment](docs/dependencies/M8.md) records pins and open findings.

```bash
SOURCE_REVISION=$(git rev-parse HEAD) docker compose --profile device-ui build
SCENARIO=machine_hdf_post docker compose up --no-build --abort-on-container-exit --exit-code-from runner
docker compose cp runner:/results/. /tmp/dialysislab-results
# Only after successful extraction:
docker compose down --volumes --remove-orphans
python3 tools/verify_compose.py --output build/compose-verification
```

If extraction fails, preserve the volume and recover it before cleanup. Automated
verifiers retain logs and available artifacts even on failure, preserve the original
exit code and write recovery instructions when resources must remain. See the
[Linux/WSL2 operating guide](docs/QUICKSTART.md).

## Device UI and experiment console

The native GUI build additionally needs X11/Xext development headers and libraries.
Dependencies are locked to reviewed archives; no system-wide installation is
performed by the project fetcher.

```bash
python3 tools/fetch_gui.py --cache build/gui-deps
cmake -S . -B build/gui -DCMAKE_BUILD_TYPE=Release -DDIALYSISLAB_GUI=ON
cmake --build build/gui --parallel 3
python3 tools/run_device_demo.py --build-dir build/gui --output build/device-demo
```

Use an already authorized Linux X11/WSLg display; the selected backend is SDL2
software rendering. `--headless --seconds 15` runs the same device client without
a display. Device UI exposes machine requests and modeled sensor observations;
it cannot configure the patient, inject faults, control time or access hidden truth.

To use both separate graphical applications with the experiment services:

```bash
docker compose -f compose.experiments.yaml -f compose.experiments-x11.yaml --profile console --profile device-ui up -d
# Console: choose a preset, Load, then Start; Pause/Resume affect virtual time.
# Headless administrative client uses the same broker:
docker compose -f compose.experiments.yaml exec -T scenario-runner python3 tools/experiment.py --api-dir /experiment status
```

This graphical override expects the existing `/tmp/.X11-unix/X0` socket. It does
not change host display permissions. The console owns experiment administration;
the device UI cannot alter scheduled prescriptions but retains immediate STOP,
including during a virtual pause. Native broker/console commands, replay/export
and recovery are documented in [M7_EXPERIMENTS.md](docs/M7_EXPERIMENTS.md).

## Verification and evidence

```bash
python3 tools/verify_device_ui.py --build-dir build/gui --output build/device-tests
python3 tools/verify_console.py --build-dir build/gui --output build/console-tests
python3 tools/verify_experiments_compose.py --with-device --output build/both-ui-tests
python3 tools/verify_integrated.py --build-dir build/gui --output build/matrix-native
python3 tools/verify_integrated.py --build-dir build/gui --compose --output build/matrix-compose
python3 tools/verify_integrated.py --group faults --build-dir build/gui --compose --output build/faults-compose
python3 tools/verify_integrated.py --group long --archive --build-dir build/gui --compose --output build/long-compose
python3 tools/check_traceability.py assurance/traceability.json
python3 tools/check_standards.py
python3 tools/check_publication.py
```

The matrix combines three modes, three synthetic patients and two dialyzers with
exact repeats. Long-run acceptance covers 100000 ticks, independently checked
water/species balances and actual process/container memory. `--archive` losslessly
compresses verified owned trajectories and records original hashes/recovery commands.
The [integration protocol](docs/M9_INTEGRATION.md) defines acceptance before execution.

[Evidence](assurance/STATUS.md), [review dispositions](assurance/REVIEWS.md) and
[decision history](docs/DECISIONS.md) distinguish software/numerical verification
from model calibration, clinical validation and human risk acceptance. Hosted CI
executes real builds/processes/widgets/Compose and retains exact report bytes.
[CI recovery and scans](docs/M8_SECURITY_CI.md) document commands and coverage.
There are **73 open dependency advisory IDs** in the recorded M8 scan; this is not
a clean-image or complete third-party license-clearance claim.

## Models and lifecycle template

| Topic | Specification |
| --- | --- |
| Components, authority and deployment | [Architecture](docs/ARCHITECTURE.md) |
| Baseline clock, wire validity, abort and recording | [M1 contracts](docs/M1_INTERFACES.md) |
| Hydraulic network, transients and synthetic dialyzers | [M2 equations](docs/M2_MODEL_INTERFACES.md) |
| Body/circuit water, urea, Na, K, Cl, bicarbonate and Ca | [M3 patient](docs/M3_PATIENT.md) |
| HD/HDF, gross/net transfer, online mixing/filter/temperature surrogates | [M4 treatment](docs/M4_TREATMENT.md) |
| Lifecycle, hazard-specific outputs, latch/reset/ACK/silence | [M5 machine](docs/M5_MACHINE.md) |
| Actual LVGL views, confirmations, stale data and reconnect | [M6 device UI](docs/M6_DEVICE_UI.md) |
| Separate experiment administration, immutable runs and replay | [M7 console](docs/M7_EXPERIMENTS.md) |
| Threat controls, inventory, SBOM, CI and open findings | [M8 security](docs/M8_SECURITY_CI.md) |

The patient has two body compartments plus circuit mixing, not validated physiology.
Its pH indication assumes fixed pCO2; no respiratory, full buffer, cardiac or red-cell
model is supplied. Contamination and some stuck sensors may remain unobservable.
Cleaning/priming states do not prove disinfection, air clearance or microbiological
quality. Containers share kernel, plant, runner, configuration and protocol risks.

The EU-first, US-later template includes the [assurance plan](assurance/ASSURANCE_PLAN.md),
[safety/security obligations](assurance/SAFETY_SECURITY.md), [V&V plan](assurance/VERIFICATION_VALIDATION.md),
[trace graph](assurance/traceability.json), [184-entry standards checklist](assurance/standards/README.md)
and [edition/applicability gaps](assurance/standards/EDITION_GAPS.md). Licensed standards
and private extracts stay outside Git, Docker contexts, CI logs and public packages.
Both `check_traceability.py --release` and `check_standards.py --release` remain
blocked by explicit obligations; normal structural checks are not release approval.

## Reproducible source package

```bash
python3 tools/package_release.py --output /tmp/DialysisLab-source.zip
python3 tools/verify_package.py --output /tmp/DialysisLab-package-verification
```

Only explicitly reviewed paths in `publication_manifest.json` enter the archive.
The package verifier compares two byte-identical archives, then builds and runs
real tests/widgets from their extracted sources. It needs the same GUI prerequisites
and a fresh external output directory. Packaging does not approve a medical product
or redistribution of an unassessed complete container image. The project is
[MIT licensed](LICENSE); third-party dependencies retain their own terms.
