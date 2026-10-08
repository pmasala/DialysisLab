# M8 verification evidence

Correction build `e8c497c995949562b1901d1346b841b955100a17`, clean at configure.
Native and sanitizer suites pass 150/150 each; real device/console widgets pass
10/10 and 5/5. Ten native/ten Compose HD/HDF/fault/recovery runs, four M1
container runs, three isolation probe groups and separate UI/console deployments
pass. Each report retains exact commands, build/source/configuration identities.

The sole review found four P2 defects. `review.json` records their fixes and
regressions. Actual stale image rejection and byte-exact recovery of 16 real
artifacts complement the unit regressions. Five actual SBOMs validate against
the official CycloneDX 1.6 schema; each container has its own inspected binaries,
modules, build and OS inventory. No second review was invoked.

Cppcheck reports zero findings in its declared limited scope. OSV reports
70 queried identities, 19 matching queries and **73 open advisory IDs**, with
zero blocked queries. See `../../DEPENDENCY_FINDINGS.json`; these are not
accepted risk or a clean-image declaration. Original RSS/PID1/inventory diagnostics
remain under `build/`; `capture-storage.json` records reversible compression of
owned raw rendered frames after independent decompression hashes.

Candidate hosted CI 37728309834 passed with historical retention limitations.
Corrected hosted CI 37730439086 is still running at this checkpoint; its actual
log recovery must be recorded before closing hosted evidence. All local
verification commands are in the retained reports and `docs/M8_SECURITY_CI.md`.
Release gates remain blocked: 184 checklist entries, 12 applicability/edition
gaps and nine prerequisites. No clinical/model calibration, standards conformity
or independent human approval is claimed. M9 integration remains outstanding.
