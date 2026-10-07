# Assurance and completion plan

Revision: 2026-10-07. Status: proposed detailed baseline; not a conformity assessment.

## Mission and evidence boundaries

Deliver a fully working, open-source dialysis software reference implementation and a reusable, evidence-producing lifecycle template. Support HD, HDF predilution/postdilution, online fluid preparation, LVGL device UI, separate control/protection, configurable circuits/dialyzers, and external Python patient simulation. Preserve WSL2/native Linux support and the dependency policy.

The present intended use remains simulation/research. It is distinct from a future manufacturer's medical-device intended use. Design artifacts should make adaptation possible, but a fork inherits neither an automatic safety conclusion nor certification. State the exact build, configuration, modeled envelope, standards baseline, and evidence scope for every claim.

Three completion levels must be reported separately:

1. **Reference implementation complete:** all agreed features work, supported deployment profiles run, models are validated within declared bounds, and requirements have reviewed implementation and test evidence.
2. **Lifecycle evidence complete for declared scope:** each applicable normative obligation has an applicability decision, artifacts, reviews, evidence, and a justified disposition. This requires authorized access to full standards; catalog abstracts are insufficient.
3. **Finished medical-device conformity:** requires a defined product, responsible organization, applicable jurisdiction, physical hardware, clinical/use context, and the additional verification/validation and conformity route for that product. This is not achievable by executing the simulation package alone.

The template must expose outstanding finished-device obligations explicitly rather than silently marking them satisfied or dropping them as "not software."

## Standards baseline to assess

These are candidate references, not a blanket declaration that all clauses apply to a simulator. Exact editions, amendments, corrigenda, regional adoptions, and market recognition must be baselined and reviewed.

| Reference | Workstream | Present evidence boundary |
| --- | --- | --- |
| IEC 62304:2006+A1:2015 | Software lifecycle, risk-related software work, configuration, problem resolution, maintenance | Draft grouped clauses 4–9 checklist written from supplied final text; applicability/evidence review remains open. |
| IEC 60601-1:2005+A1:2012+A2:2020 | Basic safety, essential performance, programmable-system lifecycle and system risk integration | Software/system obligations to derive; physical equipment tests are downstream obligations. |
| IEC 60601-2-16:2025 | Dialysis-specific requirements, including cybersecurity changes | Supplied 2018 US adoption mapped; 2025 normative delta and EU adoption review remain open. |
| ISO 14971:2019 | Risk management throughout the lifecycle | Confirmed by project owner; supplied clauses 4–10 mapped, European A11 review open. |
| IEC 81001-5-1:2021 | Secure software lifecycle | Review corrected version/interpretation information listed by IEC as 2025-12. |
| IEC 62366-1:2015+A1:2020 | Safety-related usability engineering | Simulated formative studies can help; final device usability evidence is product-specific. |
| IEC 60601-1-8:2006+A1:2012+A2:2020 | Alarm priorities, signals, control states, and verification | Include UI/audio behavior; acoustic and physical delivery evidence needs the final product. |
| IEC 60601-1-2:2014+A1:2020 | Electromagnetic disturbances and immunity | Model effects and required responses; actual EMC testing is physical-product evidence. |
| ISO 13485:2016 | Organizational quality processes and records | Supply reusable process artifacts; a repository cannot establish an organization's QMS conformity. |

Screen additional relevant references once intended context is frozen: ISO 23500 series for fluid quality/preparation, ISO 8637 series for dialyzers/circuits, and IEC 60601 collateral requirements for intended environments, physiological closed-loop control, and other applicable functions. This screening is not an exhaustive standards list.

ISO 14971 is confirmed. EU is the first target for the downstream adaptation template; US follows. See `standards/README.md`, `standards/checklist.json` and `standards/EDITION_GAPS.md` for the source-derived draft and its limits. The supplied US adoptions are not treated as equivalent to the selected EU package.

## Normative applicability register

Build a clause-level register from legally accessible copies. Record: exact reference/edition/clause; short original paraphrase; applicability to the reference and downstream product separately; rationale; derived requirement IDs; artifact/test links; owner; reviewer; evidence scope; decision status; and change history. Do not reproduce copyrighted standards in the public repository without permission.

Allowed dispositions: unresolved, applicable-open, applicable-evidence-under-review, applicable-satisfied-for-declared-scope, not-applicable-with-reviewed-rationale, downstream-product-obligation. An external obligation can never count as a passed simulation test. Final-device conformity remains blocked while its external obligations remain open.

## Lifecycle rigor and classification

Use the rigor expected for high-consequence dialysis functions as a conservative planning baseline, including Class C-oriented lifecycle artifacts. Formal IEC 62304 software safety classification must still be justified from intended use, hazards, external risk controls, and architecture. It is neither assigned by use of containers nor automatically inherited by every simulator utility. Do not equate IEC 62304 classes with IEC 61508 SILs.

Maintain separate assessments for reference device software, patient/plant models, and test tools. The latter can invalidate conclusions through erroneous test stimuli or oracles and therefore need justified confidence and verification measures.

## Required work packages and completion evidence

All rows are required planning workstreams. Existing short baseline documents provide partial inputs only; no row is represented as complete.

| ID | Work package | Completion evidence |
| --- | --- | --- |
| WP-01 | Intended use, users, environment, limitations, supported configurations | Approved scope and use specification; explicit simulation/product boundary. |
| WP-02 | Standards and jurisdiction applicability | Reviewed clause register and market-specific baseline with no unexplained omissions. |
| WP-03 | Development/quality plan and governance | Roles, competence, review responsibilities, document/change control, milestones, supplier and tool evaluation. |
| WP-04 | Risk management plan and file | Hazard analysis, foreseeable event sequences, hazardous situations, harms, risk criteria, controls, verification, residual/overall risk evaluation. |
| WP-05 | Essential performance | Measurable functions, operating envelopes, accuracy/latency limits, degradation behavior and fault conditions, with rationale. |
| WP-06 | User/system/software requirements | Unique IDs, measurable acceptance criteria, source/parent, architecture allocation, risk/security links, review status. |
| WP-07 | Architecture and detailed design | Components, interfaces, data flow, state machines, concurrency, timing, memory/resource budgets, segregation and common-cause analyses. |
| WP-08 | Control implementation | Preparation, setup, treatment, interruption, recovery and completion workflows plus regulated quantities, state/parameter validation. |
| WP-09 | Protective implementation | Hazard-specific detection/action/recovery rules, watchdogs, sensor validity, actuator authority and verified response bounds. |
| WP-10 | Cybersecurity | Assets, trust boundaries, threat model, security requirements, secure design, abuse-case verification, vulnerability response. |
| WP-11 | Third-party software and supply chain | Exact inventory/SBOM, licenses, provenance, known anomalies, supplier review, version controls, dependency exceptions. |
| WP-12 | UI, alarms and usability | Use-related risk analysis, alarm catalog, critical-task scenarios, formative work, validation plan and appropriate representative-user evidence. |
| WP-13 | Physical models | Equations, units, parameters, provenance, solver strategy, conservation, convergence, calibration/validation and uncertainty. |
| WP-14 | Patient physiology | Coupled fluids/solutes, configurable populations, acid-base assumptions, reference validation, identifiability and limitations. |
| WP-15 | External simulation tooling | Separate administration/observation interfaces, reproducible scenarios, fault injection, run records and tool-confidence assessment. |
| WP-16 | Verification plans and protocols | Unit, integration, system, fault, timing/resource, security, usability, numerical and deployment tests with predeclared acceptance criteria. |
| WP-17 | Verification execution and reporting | Actual results, raw evidence, build/configuration identity, deviations, reviewer disposition and regression records. |
| WP-18 | Validation of intended reference use | Demonstrations and user evaluation of teaching/research/engineering workflows against intended use; no substituted clinical validation. |
| WP-19 | Traceability and change impact | Bidirectional links, reviewed coverage, orphan/stale-evidence checks, propagation of changes through risks and tests. |
| WP-20 | Configuration and release | Reproducible builds, signed/provenanced release artifacts as designed, notices, SBOM, approved release report and known anomalies. |
| WP-21 | Maintenance and problem resolution | Issue intake, risk/security triage, root cause, correction, verification, release/update strategy and end-of-support rules. |
| WP-22 | Downstream adaptation package | Integration assumptions, required sensors/actuators/independence, external test obligations, tailoring guide and evidence reuse limits. |

## Release gates

G0: baseline intended use, market assumptions, exact standards, lifecycle plans and responsibility assignments.

G1: review system hazards, essential performance, threats and requirements. Justify measurable limits before implementing control/protection acceptance tests.

G2: review architecture, detailed interfaces, safety independence argument, hazard-specific responses and model assumptions.

G3: build and test each vertical feature with linked evidence; include negative and fault cases, numerical verification and dependency review.

G4: evaluate full HD/HDF scenarios, fluid preparation, alarms/UI, security, model fidelity and deployment profiles; conduct reference-use validation.

G5: close all applicable reference-scope requirements and high-priority issues, review residual risks, complete clause dispositions, and approve a reproducible release package. List downstream-product obligations separately; never label that package a certified dialysis machine.

No placeholder document, planned test, coverage percentage alone, or passing trace checker can satisfy these gates. Claim completeness only after both technical evidence and substantive review are finished.

## Roles and change control

Assign a maintainer, requirements/design owners, safety and security reviewers, model-validation owner, test owner, and release approver. In a small project one person may perform several roles, but document conflicts and seek independent review for high-consequence decisions. Record actual participants and dates; no fabricated signatures or approvals.

Every change records rationale, affected requirements/hazards/threats/interfaces/models, test impact, reviewer outcome, and release impact. Changed behavior invalidates affected evidence until reassessed.

## Immediate unresolved decisions

- Resolve the recorded edition, European adoption and missing-source gaps; review each drafted checklist entry against authorized sources.
- Complete the EU-first regulatory/GSPR and standards baseline; preserve a separate later US assessment.
- Define treatment envelopes, quantified essential-performance limits, risk acceptability criteria, and review responsibilities.
- Supply/identify validation data and its authorized uses.
- Repository confirmed: `git@github.com:pmasala/DialysisLab.git`. The existing repository establishes MIT licensing; select toolchain/dependency pins and release governance.

## Primary-source scope references

- IEC 62304: https://webstore.iec.ch/en/publication/22794
- IEC 60601-1: https://webstore.iec.ch/en/publication/67497
- IEC 60601-2-16: https://webstore.iec.ch/en/publication/68379
- ISO 14971: https://www.iso.org/standard/72704.html
- IEC 81001-5-1: https://webstore.iec.ch/en/publication/63293
- IEC 62366-1: https://webstore.iec.ch/en/publication/67220
- IEC 60601-1-8: https://webstore.iec.ch/en/publication/67388
- IEC 60601-1-2: https://webstore.iec.ch/en/publication/67554
- ISO 13485: https://www.iso.org/standard/59752.html

Public catalogs establish edition/scope only. The separately supplied licensed copies underpin the draft checklist; missing editions and collateral documents have not been inferred from catalog abstracts. See the source register for exact inputs.
