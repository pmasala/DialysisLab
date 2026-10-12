# Model and reference-data assessment template

Use this before adopting a physiological, dialyzer, fluid-quality or sensor claim.
Synthetic fixtures are not clinical data and cannot establish calibration or
independent validation. No dataset is supplied or approved by this empty template.

## Claim and equations

- Model/version and linked requirements/design/hazards:
- Equations, units, signs, conserved quantities, solver and numerical bounds:
- Parameter meanings, origin, uncertainty and identifiable combinations:
- Claimed operating domain and explicitly excluded physiology/equipment:
- Independently derived numerical benchmarks and convergence criteria:

## Data provenance and permitted use

| Dataset / publication identifier | Origin / collection conditions | License and authorized uses | Population / device / measured units | Quality / uncertainty / gaps |
| --- | --- | --- | --- | --- |
| Unassigned | Unknown | Not cleared | Unspecified | Unassessed |

Record source version/digest and authorization evidence without placing private
records in Git. Check consent, de-identification and lawful access through the
responsible organization; do not infer permission from mere availability. Licensed
standards, extracted text and images remain outside public artifacts and Docker.
Commercial parameters require actual sourced specifications, not invented profiles.

## Calibration and independent validation

Predeclare separate calibration and validation datasets, split rationale, overlap
checks and leakage controls. Record fitted parameters, objective, uncertainty,
sensitivity, identifiability and residuals; retain unsuccessful fits. Define the
validation population/conditions, metrics, tolerances and acceptance before seeing
results. Show both disagreement and domain limits, not only favorable examples.

## Disposition and change impact

Record exact software/configuration, commands, actual numeric and experimental
results, artifacts, reviewer/competence and open decisions. Distinguish numerical
conservation, calibrated fit, independent predictive validation and clinical/product
claims. Link failed claims to risk controls and affected scenarios. A parameter,
solver, sensor or dataset update requires reassessing those claims; previous approval
is not inherited automatically. Until authorized review succeeds, mark the claim
UNVALIDATED/BLOCKED and retain the usable synthetic software separately.
