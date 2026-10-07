# Current status

As of 7 October 2026, this is an expanded project baseline and initial assurance infrastructure, not a complete working dialysis system.

| Area | Actual status |
| --- | --- |
| Functional scope and container/UI boundaries | Recorded baseline; detailed engineering remains. |
| Dependency policy | Written policy and exception template. |
| Assurance, safety/security, verification strategy | Initial plans written; substantive review pending. |
| Traceability tooling | Executable structural checker; 12 self-tests executed and passed in the development environment. |
| Starter trace graph | Six illustrative project-derived chains; not an exhaustive requirements/risk/test database. |
| Standards checklist | 184 original grouped entries derived from the supplied sources and project/EU screening; all open. Detailed equipment/annex coverage and substantive review remain incomplete. |
| Market and risk-standard decision | ISO 14971 confirmed; EU-first adaptation, US later. |
| Edition/applicability gaps | 12 open gaps recorded, including newer IEC texts and European material. |
| Hazard/threat files and essential-performance limits | Incomplete; starting obligations identified. |
| C/C++ device software, LVGL UI, plant and Python physiology | Not implemented. |
| Dialysis unit/integration/system/security/UI/model tests | Not executed. |
| Model calibration/validation | Not performed. |
| Regulatory/standards conformity | Not established. |
| Repository | Project owner confirmed the empty `pmasala/DialysisLab` repository. |
| Repository baseline | Builds on the existing MIT-license commit; software implementation and compliance evidence remain incomplete. |

The traceability report is a mechanical snapshot of entered records. It must not be presented as a percentage of standard compliance. All seed requirements remain draft and all seed protocols remain planned. Release checking intentionally fails until missing evidence and prerequisites are resolved.

Verification performed on this package: the seed graph has zero structural errors; the checker reports 39 release gaps and returns nonzero exit status in release mode. The 12 helper tests cover missing evidence, stale baseline, tampered hashes, orphan references, reverse-link errors, duplicate IDs, out-of-root artifacts, incomplete requirements/protocols/prerequisites and a synthetic complete fixture. These results are not dialysis verification evidence and are not an independent qualification of the checker.

Standards-package verification on 7 October 2026: the 184-entry register and six starter requirement chains have no structural errors. Twelve edition/applicability gaps remain open. Three negative register checks rejected an unknown source, a broken requirement link and an unsupported completion claim. Three publication checks rejected path escape, PDF inclusion and duplicate entries. Both release-mode checks returned the expected nonzero status. The existing 12 trace-checker self-tests passed again. These are checks of the assurance tooling/data only, not dialysis or standards-conformity evidence.
