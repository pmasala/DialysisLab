# M1 execution evidence

Executed on 2026-10-07 against implementation revision `b598a5c`. Full revision,
source hashes, compiler identity, binary hashes, configuration and seed are stored
in the JSON reports; Docker image identity is recorded per service. Evidence scope
is synthetic simulation and assurance tooling only. Codex executed and inspected
these checks; independent review, risk acceptance and release approval are pending.

## Commands actually executed

From the repository root:

```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --parallel 3
cmake -S . -B build/repro -DCMAKE_BUILD_TYPE=Release
cmake --build build/repro --parallel 3
cmake -S . -B build/sanitize -DCMAKE_BUILD_TYPE=Debug -DDIALYSISLAB_SANITIZE=ON
cmake --build build/sanitize --parallel 3
python3 tools/verify_m1.py --build-dir build --output build/native-tests.json
python3 tools/verify_m1.py --build-dir build/sanitize --output build/sanitizer-tests.json
docker compose build --build-arg SOURCE_REVISION=b598a5c
python3 tools/verify_compose.py --output build/compose-verification
python3 tools/verify_reproducibility.py --first-build build --second-build build/repro --compose-output build/compose-verification --output build/reproducibility.json
```

All returned exit status 0. `verify_m1.py` runs the same unittest discovery suite
registered with CTest; 32 tests passed in each build. CTest was also exercised during
development. Compose verification launches five containers per run using
`up --no-build --abort-on-container-exit --exit-code-from runner`; runs both
`scenarios/hd_nominal.json` and `scenarios/hd_occlusion.json` twice; copies outputs;
probes control/protection access to administration/patient sockets; and removes
only its uniquely named test projects. All four runs completed and both probes
were denied as expected. See individual test output and per-run records below.

## Artifact index and trace allocation

- `summary.json`: high-level results and SHA-256 inventory of raw JSON artifacts;
  directly referenced by M1-TEST-001..007 in the trace graph.
- `native-tests.json`, `sanitizer-tests.json`: test cases, actual output, build and
  scenario identity. Cover M1-TEST-002..007 and publication regression checks.
- `compose-results.json`: four runs, Docker/Compose versions, per-service image
  identity, mounts, restrictions and access probes; M1-TEST-001/002/003/004/005.
- `hd_nominal-1/`, `hd_nominal-2/`, `hd_occlusion-1/`, `hd_occlusion-2/`: complete
  manifests and deterministic trajectories, copied without altering their data.
- `reproducibility.json`: both native build identities and hashes plus comparisons
  with container trajectories; M1-TEST-002.
- `container-packages.json`: build and runtime package inventories from the exact
  verified image. This is an inventory, not a reviewed SPDX/CycloneDX SBOM.
- `assurance-checks.json`: actual structural/publication/package command results;
  both release gates return the required nonzero status (60 trace gaps, 184 open
  standards entries and 12 edition/applicability gaps).

The output paths in execution commands identify original ignored `build/`
locations; public copies are retained here. Tests derive additional fault and
failure configurations in versioned `tests/test_m1.py`; test-source hashes are
recorded, so those derived cases can be reconstructed exactly. Synthetic constants
and predeclared bounds are in `docs/M1_PLAN.md` and `docs/M1_MODEL.md`.

Nominal removal is 1/3 mL; occlusion removal is 1/12 mL. Pressure is observed at
600 mmHg at fault onset; the demonstration's 250 mmHg threshold triggers zero flow
and a closed clamp within the declared 100 ms virtual bound. Same-build repeats
and native/container trajectories were byte-identical; clean native executable
hashes also matched. Cross-build declared numerical tolerance remains abs/rel
1e-9; the independent fluid balance tolerance is 1e-8 mL.

## Deviations and remaining evidence limits

The execution sandbox prohibits local sockets and daemon access; integration and
Compose commands ran with the authorized host access. An initial Compose syntax
error was corrected before retained verification. Earlier exploratory runs are
not substituted for the final committed-source records. HALT (stop outputs without
exiting the process) was added to permit correct Compose exit-code collection;
Decimal patient and compensated plant ledgers avoid long-run accumulation drift.
These implementation refinements are recorded in the final interfaces/model.

The watchdog kill test terminates an actual scheduler heartbeat subprocess after
a committed tick; it does not simulate physical power loss. Native Linux outside
this WSL2 host, malicious flooding, real-time scheduling, sensor bias, calibrated
physiology, HDF, online preparation, GUI/usability and independent reviewer
acceptance remain outside this evidence. All full-roadmap release prerequisites,
184 standards entries and 12 edition/applicability gaps remain open.
