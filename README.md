# DialysisLab

Project baseline, 7 October 2026. Confirmed project name: DialysisLab.

Repository: [pmasala/DialysisLab](https://github.com/pmasala/DialysisLab). SSH remote: `git@github.com:pmasala/DialysisLab.git`.

An open-source dialysis software reference project, intended to democratize access to a working implementation together with its development and assurance evidence. Execution remains limited to simulated patients and equipment. This package contains the project baseline and an executable traceability checker, but no executable dialysis simulator.

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

The normal commands check trace/register structure and report gaps. The tests exercise the original trace checker only. Both release commands deliberately fail on this incomplete baseline. None of these commands verifies dialysis software or certifies conformity.

## Engineering intent

Develop traceable requirements, risk analysis, design, configuration management, and verification evidence with reference to IEC 62304, IEC 60601-1, IEC 60601-2-16, and ISO 14971. No standards conformity or clinical validation is claimed by this starter package. Simulation cannot establish the conformity of a physical medical device.

The target is a complete, executable reference implementation with reviewed lifecycle artifacts and evidence for an explicitly defined configuration and scope. The assurance plan now makes this a release objective, not optional supporting documentation. The project owner has confirmed ISO 14971 and EU-first, US-second adaptation. The supplied standards have been inspected and used to draft an original 184-entry explained checklist. All entries remain open; edition gaps and detailed hardware/annex coverage are explicit.

Calibration may use public papers, manufacturer specifications, shareable bench measurements, and authorized de-identified datasets. Availability and redistribution rights must be checked per source. Public demonstrations should use synthetic scenarios unless a dataset is explicitly cleared for redistribution.

## Open project decisions

Exact dependency versions and numerical acceptance tolerances remain to be selected. The project uses the [MIT license](LICENSE) already established in the repository. Third-party standards and dependencies retain their own licensing terms.

## Package the reviewed public files

```bash
python3 tools/package_release.py --output ../DialysisLab-project-baseline.zip
```

The builder includes only paths in `publication_manifest.json`. Review new content before adding it; standards PDFs and private analysis are never publication inputs. Packaging success is not a software release approval.
