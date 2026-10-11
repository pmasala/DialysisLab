# Documentation guide

Start with the question you want to answer. You do not need to read the milestone
specifications to run an experiment or understand the models.

| I want to… | Read this |
| --- | --- |
| Run a simulation or open the interfaces | [Running guide](QUICKSTART.md) |
| Inspect animated circuits, trends and patient state | [Visual inspection](UI_INSPECTION.md) |
| Understand the blood circuit, fluid preparation and dialyzer | [How the simulation works](SIMULATION.md) |
| Understand the separate software components | [Architecture](ARCHITECTURE.md) |
| Build, test or package changes | [Development checks](DEVELOPMENT.md) |
| See what has been verified and what remains open | [Evidence status](../assurance/STATUS.md) |

## Technical references

These documents contain equations, protocol fields and acceptance criteria.
Their M1–M9 prefixes identify the development milestone that introduced them;
they are not a reading order.

| Topic | Reference |
| --- | --- |
| Simulation clock, messages, failed calls and recording | [Execution contracts](M1_INTERFACES.md) |
| Hydraulic network and dialyzer equations | [Hydraulic model](M2_MODEL_INTERFACES.md) |
| Patient water and solute balances | [Patient model](M3_PATIENT.md) |
| HD, HDF and substitution-fluid preparation | [Treatment model](M4_TREATMENT.md) |
| Machine states, alarms and protective actions | [Machine behaviour](M5_MACHINE.md) |
| Machine screens and operator commands | [Device interface](M6_DEVICE_UI.md) |
| Patient configuration, faults, replay and export | [Experiment tools](M7_EXPERIMENTS.md) |
| Security controls, dependencies and CI | [Security and verification](M8_SECURITY_CI.md) |
| Integrated scenarios and acceptance checks | [Integration protocol](M9_INTEGRATION.md) |

## Requirements, risks and standards

The [assurance plan](../assurance/ASSURANCE_PLAN.md) explains the development
records. The [traceability register](../assurance/traceability.json) links
requirements, risks and verification evidence. The
[standards guide](../assurance/standards/README.md) explains the checklist and
its limitations. Licensed standards themselves are not distributed here.

For project history, use [decisions](DECISIONS.md), [milestones](MILESTONES.md)
and [review records](../assurance/REVIEWS.md). Historical evidence describes the
revision at which it was collected; it is not automatically evidence for a later change.
