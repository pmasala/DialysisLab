# Read DialysisLab from requirements to evidence

DialysisLab is a software laboratory: a simulated patient and fluid circuit are
operated by separate control and protection services. The machine interface is
for treatment operations; a second application is for experiments. This guide
explains the current implementation without requiring its development history.

To run it first, use [Quickstart](QUICKSTART.md). The optional
[complete-browser candidate](testing/BROWSER.md) executes C++/LVGL and the Python
patient locally, with its separate verification and dependency-review limits. To assess or change it, read in
this order. The documents are written in English so that the public project has
one maintained technical baseline.

| Order | Document | Question answered |
| --- | --- | --- |
| 1 | [Requirements](REQUIREMENTS.md) | What must the software do, for whom, under which constraints, and how is each requirement accepted? |
| 1a | [Atomic obligations](ATOMIC_REQUIREMENTS.md) and [coverage matrix](testing/COVERAGE.md) | How are implemented requirements allocated to measurable decisions and tests, with deferred work explicit? |
| 2 | [Architecture](ARCHITECTURE.md) | Which components own state, communicate, constrain outputs and retain evidence? |
| 3 | [Treatment design](design/TREATMENT.md) | How do tests, preparation, priming, connection, therapy, return and disinfection work? |
| 4 | [Fluid and transport design](design/MODELS.md) | Which physical quantities and equations are implemented, and where do they stop being credible? |
| 5 | [Interfaces and failure design](design/INTERFACES.md) | What crosses each boundary, in which order, and what happens when an exchange fails? |
| 5a | [Protective behavior and security](design/SAFETY_SECURITY.md) | Which failures are detected, which outputs are restricted, and which common causes remain? |
| 6 | [UI and experiment design](design/INTERACTION.md) | How do commands, confirmations, observations and experiment controls differ? |
| 7 | [Master verification plan](testing/PLAN.md) | What must be tested, with which oracles, configuration and acceptance rules? |
| 8 | [Executable test catalogue](testing/CATALOG.md) | Which registered tests and concrete test methods exist? |
| 9 | [Documentation audit](../assurance/audits/DOCUMENTATION_AUDIT.md) | What was checked, what was repaired and what still blocks an approval? |

Interface reference: [wire protocol](design/WIRE_PROTOCOL.md),
[field order and units](design/WIRE_FIELDS.md), [patient JSON](design/JSON_FIELDS.md).
Planned evidence collection: [measurement protocol](testing/MEASUREMENTS.md) and
[boundary/approval protocol](testing/CLOSURE.md).

Prospective requirement change: [concentrate preparation, pumps and startup](design/DIALYSATE_PREPARATION_CHANGE.md).
This proposal records requested behavior, proposed states and planned tests; it is not implemented evidence.

The [document-control rules](DOCUMENT_CONTROL.md) explain precedence, change
review and how to regenerate the requirements and test catalogues. The
[glossary](GLOSSARY.md) defines terms and units used along this route.

## Evidence is a separate layer

A requirement describes an obligation. A design explains its implementation. A
test plan states how to challenge it. A test report records an execution. None of
these substitutes for the next. A link to a test does not mean that it passed on
the current commit or that its scope covers the entire requirement.

The [current verification status](testing/STATUS.md) names the assessed baseline
and the evidence applicable to it. The [standards register](../assurance/standards/README.md)
contains open applicability obligations, not a conformity declaration.

## Supporting guides and separate history

[Quickstart](QUICKSTART.md), [guided operation](GUIDED_TREATMENT.md),
[physical models](PHYSICAL_MODEL.md), [dynamic models](DYNAMIC_MODEL.md) and
[inspection](UI_INSPECTION.md) support users. The official controlled reading set
is enumerated in [document-set.json](document-set.json).

The [Project Log](../project-log/README.md) is separate and **not part of the official
project documentation**. It indexes milestones, earlier reviews and historical
executions for investigation. You do not need it to read the current specification.

Build instructions remain in [Development](DEVELOPMENT.md), dependency decisions
in [the dependency policy](../DEPENDENCY_POLICY.md), and security response in
[SECURITY.md](../SECURITY.md).

Cold-start concentrate preparation: [requirements](design/DIALYSATE_PREPARATION_CHANGE.md) →
[design](design/PREPARATION.md) → [verification protocol](testing/PREPARATION.md).
