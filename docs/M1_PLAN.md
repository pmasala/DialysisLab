# M1: deterministic headless HD

Recorded before implementation, 2026-10-07. Implementation authorization: the
repository owner's M1 request. Technical acceptance is distinct from independent
safety review, risk acceptance, or release approval. All numbers below are
synthetic demonstration settings, not clinical safety limits.

## Requirements and acceptance

| Requirement | Acceptance / planned test | Parent hazard/design |
| --- | --- | --- |
| M1-REQ-001 | CMake builds three C++17 executables; five services run through Compose; source/configuration and binary identities accompany results. M1-TEST-001. | HAZ-001 / DES-001 |
| M1-REQ-002 | Fixed integer virtual ticks, same configuration and seed reproduce records exactly on the same build; cross-build numeric tolerance 1e-9 absolute and relative. M1-TEST-002. | HAZ-004 / DES-004 |
| M1-REQ-003 | HD balance matches an independent Decimal calculation to 1e-8 mL over the declared run; zero-removal and partial-flow cases included. M1-TEST-003. | HAZ-003 / DES-003 |
| M1-REQ-004 | Resistance fault at tick 5 yields pressure >= 250 mmHg; protection directly latches blood pump off, UF off and venous clamp closed before that tick's integration, at most one 100 ms virtual interval after onset. M1-TEST-004. | HAZ-002 / DES-002 |
| M1-REQ-005 | Repeated conflicting control demand and subsequent protective permits cannot release a trip; no runtime reset. M1-TEST-005. | HAZ-002 / DES-002 |
| M1-REQ-006 | Missing, invalid, stale, future and replayed observations trip by the same bound; control and protection have separate sensor channels. M1-TEST-006. | HAZ-004 / DES-004 |
| M1-REQ-007 | Loss of control/protection denies the current commit; plant/patient loss aborts the run; runner loss latches plant within 3 wall seconds without advancing virtual time. Heartbeats support a pause longer than the 2 s lease. M1-TEST-007. | HAZ-002, HAZ-004 / DES-002, DES-004 |

The 250 mmHg threshold is chosen solely to separate the demonstration's nominal
150 mmHg from fault pressure 600 mmHg. Response bounds derive from the 100 ms
scheduler, not clinical requirements. The wall budget is a development watchdog,
not a real-time guarantee on Linux.

## Architecture decisions

- Separate C++ control, protection and plant executables; Python patient and
  scenario-runner processes. Standard libraries and Linux Unix-domain sockets;
  no downloaded application libraries, GUI, external network, or real actuator.
- Role-specific socket directories, independently mounted in containers. Plant
  authorizes operations by the listener, never by a claimed role in a message.
  Only runner/plant see fault and truth administration. Local mode assumes trusted
  processes under one user; container mounts are the supported isolation boundary.
- Runner owns the virtual clock and serial barriers. Protection fetches its own
  observation and sends its own decision to the plant; the runner does not compute
  or forward protective commands. Plant requires fresh decisions for every tick.
- Plant arbitration, protection decisions and control decisions have distinct
  implementations. Shared kernel, transport codec, plant and runner remain common
  causes; containers establish neither hardware independence nor risk acceptance.
- Latches last for the process lifetime. Recovery means ending the run and starting
  a fresh, zero-output configuration; automatic process restart is disabled.

See [M1_INTERFACES.md](M1_INTERFACES.md) for the contract frozen before code and
[M1_MODEL.md](M1_MODEL.md) for equations and model boundaries.

## Implementation sequence

1. Record requirements, contracts, failure policies, model and dependency pins.
2. Implement bounded transport, plant arbitration and separate decision services.
3. Implement patient accounting, scheduler, synthetic configurations and manifests.
4. Add CMake, constrained Compose deployment and allowlisted build context.
5. Execute numerical, protocol, fault, process-loss, replay and Compose tests;
   retain actual build/configuration-specific evidence and document deviations.
6. Extend trace links and publication formats without changing release criteria;
   update status, commands, remaining decisions and make coherent local commits.

## Retained roadmap

Full HD treatment workflows, pre/post HDF, online mixing/heating/filtration and
substitution, configurable circuits and multiple dialyzers, electrolyte/solute and
acid-base models, LVGL device UI, separate experiment console, model calibration,
usability, security and downstream equipment evidence remain required. M1 does
not remove or satisfy those workstreams. Native Linux deployment beyond this WSL2
host and all substantive assurance reviews remain open until actually performed.
