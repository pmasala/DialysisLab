# Build and run M1

M1 executes synthetic equipment/patients only. Read M1_MODEL.md for equations,
M1_INTERFACES.md for timing/failure behavior, M1_RISKS.md for limitations and
M1_PLAN.md for predeclared acceptance. Full roadmap features remain required.

## Native Linux or WSL2

Prerequisites: CMake >=3.16, GCC with C++17, Python >=3.9, GNU Make, Linux Unix
sockets. The verified native versions and pinned container versions are in
[dependencies/M1.md](dependencies/M1.md). No pip installation is needed.

From the repository root:

```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --parallel 3
ctest --test-dir build --output-on-failure
PYTHONPATH=python python3 -m dialysislab.runner --local --build-dir build --config scenarios/hd_nominal.json --output build/nominal
PYTHONPATH=python python3 -m dialysislab.runner --local --build-dir build --config scenarios/hd_occlusion.json --output build/occlusion
python3 tools/verify_m1.py --build-dir build --output build/m1-tests.json
```

Use a fresh output path for each execution; existing results are never overwritten.
Native mode launches four service subprocesses alongside the runner and cleans up
only its own temporary sockets. It assumes trusted same-user processes; container
mounts enforce the role boundary. A sandbox denying Unix sockets cannot run these
integration tests. Missing binaries make M1 tests fail with a build instruction.

## Docker Compose

Requires a running Docker daemon and Compose v2+ (tested with v5.1.1). The image
uses the exact base digest and dated Debian snapshot recorded in Dockerfile; first
build needs registry/snapshot access. Runtime uses no network and no host mounts.

```bash
python3 tools/check_publication.py
SOURCE_REVISION=$(git rev-parse HEAD) docker compose build
SCENARIO=hd_occlusion RUN_NAME=occlusion docker compose up --no-build --abort-on-container-exit --exit-code-from runner
mkdir -p build/compose-occlusion
docker compose cp runner:/results/occlusion/. build/compose-occlusion/
docker compose down --volumes
```

`down --volumes` removes this Compose project's sockets and result volume; copy
results first. It does not delete other projects. To run nominal HD, use
`SCENARIO=hd_nominal RUN_NAME=nominal` with a fresh project lifecycle. Processes do
not restart automatically and stale socket paths are deliberately not reused.

For retained acceptance evidence, including two repeats of each configuration and
actual administration-access denial probes:

```bash
python3 tools/verify_compose.py --output build/compose-verification
```

This creates uniquely named temporary Compose projects, copies records, captures
image IDs/isolation settings and removes only those projects afterward. It expects
the image to have been built from current sources. Verify its source hashes in the
record before reusing cached evidence after changes.

## Records and expected behavior

Each run writes deterministic `trajectory.json` plus `manifest.json` containing
UTC execution time, configuration/seed, model/interface versions, compiler/source
identity, actual binary/Python hashes, platform, outcome and trajectory hash.
Native and container builds may have different binary identities. Nominal HD has
300 mL/min blood flow, 150 mmHg circuit pressure and 1/3 mL removed over 20 ticks.
The occlusion scenario changes resistance at tick 5; pressure is observed as 600
mmHg, the synthetic 250 mmHg threshold trips, and final removal is 1/12 mL. These
are demonstrations, not clinical limits. Later control demands cannot clear the
latch. Invalid data trips; process failures abort instead of producing success.

## Assurance and publication

```bash
python3 tools/check_traceability.py assurance/traceability.json
python3 tools/check_standards.py
python3 tools/check_traceability.py assurance/traceability.json --release
python3 tools/check_standards.py --release
python3 tools/package_release.py --output /tmp/DialysisLab-m1.zip
```

Normal checks should pass. Both release checks must return nonzero while roadmap,
review and evidence obligations remain incomplete. Packaging is a source artifact,
not release approval. Add new original text/source/build inputs deliberately to
`publication_manifest.json`; add individual Docker inputs to `.dockerignore`.
Never add licensed standards, extracts, images, build outputs or Git metadata.

Optional C++ diagnostics:

```bash
cmake -S . -B build/sanitize -DCMAKE_BUILD_TYPE=Debug -DDIALYSISLAB_SANITIZE=ON
cmake --build build/sanitize --parallel 3
ctest --test-dir build/sanitize --output-on-failure
```

To verify clean-build binary identity and compare native trajectories with the
retained Compose records (numerical abs/rel tolerance 1e-9):

```bash
cmake -S . -B build/repro -DCMAKE_BUILD_TYPE=Release
cmake --build build/repro --parallel 3
python3 tools/verify_reproducibility.py --first-build build --second-build build/repro --compose-output build/compose-verification --output build/reproducibility.json
```
