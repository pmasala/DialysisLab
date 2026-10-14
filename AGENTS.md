# Repository Guidelines

## Project Structure & Module Organization

DialysisLab contains a C++ dialysis equipment simulator, separate control and protection services, an LVGL device UI, a Dear ImGui experiment console, and a Python patient/experiment runtime. Only simulated equipment and patients are supported.

- `src/`: C++ machine components and graphical clients.
- `python/dialysislab/`: patient model and experiment runtime.
- `scenarios/`: synthetic patient, treatment and fault configurations.
- `tools/`: build helpers, verification, traceability/standards checks and packaging.
- `tests/`: model, runtime, interface and assurance tests.
- `docs/`: architecture, dependency candidates, and review templates.
- `assurance/`: lifecycle plans, evidence status, and `traceability.json`.
- `assurance/standards/`: JSON registers and generated `CHECKLIST.md`.
- `publication_manifest.json`: explicit public-package allowlist. New public files must be explicitly registered.

## Build, Test, and Development Commands

Run from the repository root with Python 3.9+. The core requires CMake 3.16+ and a C++17 compiler; GUI builds have additional dependencies. See `docs/QUICKSTART.md` for launch commands and `docs/DEVELOPMENT.md` for verification.

```bash
cmake -S . -B build/core -DCMAKE_BUILD_TYPE=Release
cmake --build build/core --parallel 3
python3 tools/check_traceability.py assurance/traceability.json  # Validate trace links/evidence
python3 tools/check_standards.py                               # Validate registers and rendered checklist
python3 tools/dependency_report.py --check-only                 # Validate dependency/CI review hashes without a build
python3 -m unittest discover -s tests -v                       # Run helper tests
python3 tools/render_checklist.py                             # Regenerate CHECKLIST.md
python3 tools/package_release.py --output /tmp/DialysisLab-baseline.zip
```

Packaging includes only allowlisted files and requires output outside the repository. Both checkers accept `--release`; these gates remain blocked by documented release obligations. Structural checks do not establish standards conformity.

## Coding Style & Naming Conventions

Use four-space Python indentation, `snake_case` functions/modules, and descriptive `test_*` methods. Follow nearby code; no formatter or linter is configured. Preserve Python 3.9 compatibility and two-space JSON indentation. Keep trace IDs globally unique and follow existing patterns such as `REQ-001` and `TEST-001`.

Edit checklist JSON and regenerate `CHECKLIST.md` rather than editing generated Markdown directly.

## Testing Guidelines

Use standard-library `unittest` in `tests/test_*.py`. Cover valid synthetic records and meaningful rejection cases, including broken links, missing evidence, and tampered hashes. Use temporary directories for fixtures. Tests cover software and numerical behaviour; they do not establish clinical validation. Never mark planned dialysis tests as passed without execution and evidence.

## Commit & Pull Request Guidelines

The short history uses concise, sentence-case subjects, such as “Initialize DialysisLab architecture and assurance baseline”; follow that imperative style. No formal prefix convention or PR template exists.

PRs should explain the change, link relevant issues or requirement IDs, report validation commands/results, and update affected documentation and generated files.

## Dependencies & Publication

Follow `DEPENDENCY_POLICY.md` when adding dependencies. Review content and redistribution rights before changing the publication allowlist. Keep licensed standards, extracts, screenshots, and private analysis outside the repository, as required by `assurance/standards/PUBLICATION_POLICY.md`.

## Current documentation and integration

All pull requests target `main`. The official reading set is `docs/document-set.json`: requirements, architecture, detailed design, test plans and current evidence applicability. Historical milestone narratives and runs belong to the separate `project-log/README.md` index, outside the official set. Preserve their bytes/hashes; never inherit their passed status without a current-baseline assessment. After the final edit, run `python3 tools/documentation.py --check`, traceability and publication checks on exactly what will be published.

Also run `python3 tools/dependency_report.py --check-only` before publishing. Changes to files listed in `dependency_inventory.json` require reviewing the actual dependency/license/CI impact and updating only the corresponding reviewed hashes. Do not refresh hashes automatically or weaken mismatch rejection.

## Project memory: final candidate checks

Read `project-log/PROCESS_MEMORY.md` before publishing. PR #11 failed because a late
screenshot addition changed `publication_manifest.json` after its trace hashes were
recorded. A pass on an earlier working tree is not a pass on the published commit.
Finish all allowlist/provenance edits first; review changed implementation artifacts
and update only their current trace hashes (never historical evidence). Run all
structural gates after the last edit on the staged candidate, record `git write-tree`,
and verify the committed/published tree equals it. Any intervening edit invalidates
that check. Do not report a full pass while one required gate fails.
