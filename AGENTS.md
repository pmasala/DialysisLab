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
