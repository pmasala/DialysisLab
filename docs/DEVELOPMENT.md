# Development checks

Build the core or GUI using the [running guide](QUICKSTART.md). Run these commands
from the repository root, choosing fresh output paths. GUI and Compose checks
require the corresponding build, display or Docker prerequisites.

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
The [integration protocol](M9_INTEGRATION.md) defines acceptance before execution.

[Evidence](../assurance/STATUS.md), [review dispositions](../assurance/REVIEWS.md) and
[decision history](DECISIONS.md) distinguish software/numerical verification
from model calibration, clinical validation and human risk acceptance. Hosted CI
executes real builds/processes/widgets/Compose and retains exact report bytes.
[CI recovery and scans](M8_SECURITY_CI.md) document commands and coverage.
There are **73 open dependency advisory IDs** in the recorded M8 scan; this is not
a clean-image or complete third-party license-clearance claim.


## Short PR verification and manual endurance

PRs run a complete HDF POST lifecycle with ten simulated therapy minutes twice.
The 100000-step campaign is separate and manually enabled through `run_long` in
GitHub Actions. The [CI protocol](testing/CI.md) gives commands, budgets, acceptance
criteria and interpretation of progress diagnostics. Short-run success does not
establish long-run stability.

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
[MIT licensed](../LICENSE); third-party dependencies retain their own terms.


Return to the [documentation guide](README.md).
