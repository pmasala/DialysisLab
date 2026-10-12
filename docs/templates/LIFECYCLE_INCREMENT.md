# Lifecycle increment record template

Copy only when a new increment needs a record; use the existing milestone,
decision, review, risk and traceability registers as the authoritative locations.
Empty fields mean **unresolved**, never approval. Do not copy licensed standards,
credentials, personal data or private extracts into a public record.

## Configuration and responsibility

- Increment / issue / intended simulated use:
- Frozen base commit; candidate and correction commits; branch:
- Author, requirements/design owner, test owner, actual reviewer, release authority:
- Supported configuration, platform, dependencies, excluded uses:
- EU-first applicability references; later US differences; source-access gaps:

Do not invent a person's participation or signature. Identify conflicting roles
and the independent human assessment still needed. AI review is defect finding.

## Requirements, risks and design

| Requirement / parent | Measurable acceptance defined before execution | Component / design / interface version | Hazard / threat / control | Test IDs |
| --- | --- | --- | --- | --- |
| Unassigned | Unresolved | Unresolved | Unresolved | Planned |

For each affected risk, record foreseeable event sequence, hazardous situation,
possible harm, initial estimate and its basis, detection/action budget, actuator
outputs, latch/reset/restart policy, control verification and effectiveness limits.
Assign risk acceptability and residual/overall risk decisions only to an authorized
human using approved criteria. Include common causes and risks introduced by the
change; a test pass is not risk acceptance.

Record units, ranges, validity, timestamps, sequence/session rules, timeouts,
concurrency/resource budgets and shutdown semantics. Keep commanded and observed
states distinct. Document reversible decisions and unresolved assumptions.

## Implementation and verification

| Protocol / oracle | Exact command and build/configuration | Expected criterion | Actual result / deviation | Artifact path and SHA-256 |
| --- | --- | --- | --- | --- |
| Planned | Not executed | Predeclared | NOT_RUN | None |

Include negative, numeric, process-failure, resource, boundary/security and real
integration checks affected by the change. Separate numerical verification from
model validation and UI automation from representative-user evaluation. Record
BLOCKED checks and precise prerequisites without marking them passed. Preserve
failed artifacts and original errors before cleanup; verify any lossless archival.

## Review and problem resolution

Record the actual review method/command, frozen base/candidate, date, output/hash
and limitations. For each finding: ID, severity, reproducer, linked risks/requirements,
root cause, correction or justified non-applicability, correction commit and actual
regression evidence. Follow the increment's declared review policy; this execution
uses one automatic review per phase with no recursive or second review cycle.

Assess regressions and affected evidence after every change. Maintain historical
results rather than rewriting them to describe a newer build. Update dependency
pins/notices/SBOM/advisory dispositions where relevant; use the dependency exception
template for an explicit authorized license exception.

## Release, deployment and maintenance disposition

- Technical implementation status and remaining anomalies:
- Model calibration/validation status and authorized dataset uses:
- Security findings, mitigation coverage and residual decision owner:
- Human review / risk acceptance / normative applicability gaps:
- Exact artifact identity, explicit publication allowlist and recovery commands:
- Install/stop/fresh-session rollback; compatibility and migration:
- Monitoring/intake, update triggers, declared support responsibility/lifetime:
- Release decision, actual approver/date/evidence, or BLOCKED reason:

Run normal traceability/standards/publication checks and separately record release
gate outcomes. Never remove obligations or weaken checks to obtain approval. A
source package does not approve a physical medical device or an entire OS image.
