# DialysisLab

Project baseline, 7 October 2026. Confirmed project name: DialysisLab.

Repository: [pmasala/DialysisLab](https://github.com/pmasala/DialysisLab). SSH remote: `git@github.com:pmasala/DialysisLab.git`.

An open-source dialysis software reference project, intended to democratize access to a working implementation together with its development and assurance evidence. Execution remains limited to simulated patients and equipment. M1 implements a deliberately limited, deterministic headless HD demonstration with separate control, protection, plant, patient and scenario-runner processes. It is uncalibrated and does not establish clinical safety or standards conformity.

## Run M1

```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --parallel 3
ctest --test-dir build --output-on-failure
PYTHONPATH=python python3 -m dialysislab.runner --local --config scenarios/hd_occlusion.json --output build/occlusion
SOURCE_REVISION=$(git rev-parse HEAD) docker compose build
docker compose up --no-build --abort-on-container-exit --exit-code-from runner
```

See the [M1 runbook](docs/M1_RUNBOOK.md) for result extraction, Compose cleanup,
repeatability/failure tests, exact dependencies and assurance commands. The
[plan](docs/M1_PLAN.md), [interfaces](docs/M1_INTERFACES.md), [model](docs/M1_MODEL.md)
and [risk analysis](docs/M1_RISKS.md) define the narrow scope. All features below
remain required; M1 does not complete the roadmap.

## Configurable circuit increment (M2)

The opt-in circuit model adds compliant nodes, tube/resistor/clamp/dialyzer edges,
a finite-head pump, synthetic small/large dialyzers, membrane transfer rates and
separate patient/circuit/effluent water ledgers. See its
[equations, limits and contracts](docs/M2_MODEL_INTERFACES.md). M2 uses prescribed
solute concentration boundaries; dynamic patient solute coupling follows in M3.

```bash
PYTHONPATH=python python3 -m dialysislab.runner --local --config scenarios/circuit_occlusion.json --output build/circuit-demo
python3 tools/verify_models.py --output build/circuit-native
SOURCE_REVISION=$(git rev-parse HEAD) docker compose build
python3 tools/verify_models.py --compose --output build/circuit-compose
```

Choose new output paths for each invocation. The verification command collects
Compose logs and results before cleanup, including failure artifacts. See the
[complete milestone plan](docs/MILESTONES.md) and
[current execution checkpoint](assurance/STATUS.md) for remaining phases.

## Agreed scope

- Intermittent haemodialysis and both predilution and postdilution haemodiafiltration.
- Online substitution-fluid preparation, including modeled mixing, thermal behavior, filtration stages, hydraulics, and delivery.
- A generic machine assembled from configurable components; multiple dialyzer profiles.
- C/C++ machine control, protective system, physical plant, and medical-device-style user interface.
- A configurable Python patient model for fluid volumes, electrolyte/solute dynamics, and patient scenarios.
- Linux containers usable on WSL2 and native Linux, with headless experiments and automated verification.
- LVGL for the device UI. Patient simulation and experiment tools are separate applications, not device-UI pages or modes.
- Application libraries should preferably use MIT, BSD, Apache-2.0, or zlib licenses; exceptions require explicit review.

## Documents

- [Architecture decisions](docs/ARCHITECTURE.md)
- [Dependency policy](DEPENDENCY_POLICY.md)
- [Candidate dependencies](docs/DEPENDENCY_CANDIDATES.md)
- [Dependency exception template](docs/templates/DEPENDENCY_EXCEPTION.md)
- [Assurance and completion plan](assurance/ASSURANCE_PLAN.md)
- [Safety and security design obligations](assurance/SAFETY_SECURITY.md)
- [Verification and validation strategy](assurance/VERIFICATION_VALIDATION.md)
- [Current evidence status](assurance/STATUS.md)
- [Machine-readable starter trace graph](assurance/traceability.json)
- [Explained standards checklist and coverage](assurance/standards/README.md)
- [Edition and EU applicability gaps](assurance/standards/EDITION_GAPS.md)
- [Licensed-source publication policy](assurance/standards/PUBLICATION_POLICY.md)

## Run the assurance infrastructure

From this directory, using Python 3.9 or newer:

```bash
python3 tools/check_traceability.py assurance/traceability.json
python3 tools/check_standards.py
python3 -m unittest discover -s tests -v
python3 tools/check_traceability.py assurance/traceability.json --release
python3 tools/check_standards.py --release
```

The normal commands check trace/register structure and report gaps. Build M1 before running the full test suite; it now exercises the synthetic services, publication boundaries and original trace checker. Both release commands deliberately fail while roadmap work and reviews remain incomplete. Passing these checks does not establish standards conformity.

## Engineering intent

Develop traceable requirements, risk analysis, design, configuration management, and verification evidence with reference to IEC 62304, IEC 60601-1, IEC 60601-2-16, and ISO 14971. No standards conformity or clinical validation is claimed by this starter package. Simulation cannot establish the conformity of a physical medical device.

The target is a complete, executable reference implementation with reviewed lifecycle artifacts and evidence for an explicitly defined configuration and scope. The assurance plan now makes this a release objective, not optional supporting documentation. The project owner has confirmed ISO 14971 and EU-first, US-second adaptation. The supplied standards have been inspected and used to draft an original 184-entry explained checklist. All entries remain open; edition gaps and detailed hardware/annex coverage are explicit.

Calibration may use public papers, manufacturer specifications, shareable bench measurements, and authorized de-identified datasets. Availability and redistribution rights must be checked per source. Public demonstrations should use synthetic scenarios unless a dataset is explicitly cleared for redistribution.

## Open project decisions

M1's exact build dependencies and synthetic tolerances are recorded in its runbook and model specification. Versions, numerical acceptance limits and validation sources for the broader roadmap remain open. The project uses the [MIT license](LICENSE); third-party standards and dependencies retain their own licensing terms.

## Package the reviewed public files

```bash
python3 tools/package_release.py --output ../DialysisLab-project-baseline.zip
```

The builder includes only paths in `publication_manifest.json`. Review new content before adding it; standards PDFs and private analysis are never publication inputs. Packaging success is not a software release approval.
