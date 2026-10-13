# Detailed design: protective behavior and security boundaries

Document ID SDD-05; current technical design candidate. Read the architecture and
interface design first. This document describes controls that exist, their failure
assumptions and verification routes. It supplies the engineering analysis needed
for review; it does not assign a medical-device software safety class or accept
residual risk on behalf of a responsible organization.

## Protective output contract

The independent protection service evaluates its own frozen observation and sends
a bit mask directly to plant arbitration. Control cannot erase a bit. The plant
combines existing and new masks by union before integration. A later permit, ACK
or silence does not clear that union. Observations are sampled before integration:
a deviation created inside one tick is first visible at the next sample.

| Hazard / bit | Current synthetic detector | Required effect |
| --- | --- | --- |
| Pressure / 0 | Inlet or venous >= prescribed pressure limit; physical arterial <= negative limit | Stop blood and all prepared fluid outputs |
| Low flow / 1 | Active pump phase, cycles>1, prescribed blood>10 and measured blood<1 mL/min, without an existing blood block | Stop blood and fluids; blockage is not proved cleared merely by zero flow |
| Air or level / 2 | Air signal>=0.5; dynamic chamber level<0.15 or >0.90 | Stop blood and fluids |
| Blood leak / 3 | Leak signal>=0.5 | Stop blood and fluids |
| Measurement / 4 | Invalid, missing or wrong-clock protective sample | Stop blood and fluids |
| Temperature / 5 | Outside 35..39 C | Stop UF, substitution and dialysate; blood may continue in treatment |
| Composition / 6 | Conductivity outside 12..16 mS/cm | Fluid-only restriction during treatment |
| Filter / 7 | Filter pressure>300 mmHg | Fluid restriction; automatic recovery lacks a functional blockage test |
| Integrity / 8 | Modeled integrity indication false | Fluid restriction |
| Route / 9 | Actual route differs from mode during treatment/flush | Fluid restriction |
| Supply / 10 | Supply-ready false, or unexplained replacement<1 mL/min after startup in HDF | Fluid restriction |
| Balance / 11 | Absolute measured UF−substitution−expected net exceeds 5 mL during treatment | Fluid restriction |
| Communication / 12 | Terminal plant watchdog/shutdown path | Stop all outputs; terminal state cannot resume |

Any active alarm also stops external pumping during self-test, priming, return and
cleaning. In these phases that pumping is a source/waste or rinseback operation,
not ongoing patient circulation. During treatment blood is stopped by bits
0,1,2,3,4,12; all bits inhibit prepared fluids. These are implemented simulation
rules, not clinically approved thresholds or alarm priorities.

`Machine::hazards5`, `protect`, `pumping` and `fluid_blocked`, followed by
`Plant::enforce_machine` and COMMIT5, implement this contract. The audit campaign
checks every mask in every state, then each single/pair mask against hostile demands
in the actual coupled plant for five active phases. Sample-fault cases additionally
exercise detection; injecting a mask alone proves arbitration, not sensor coverage.

## Failure analysis and detection limits

| Event chain / affected property | Existing control and observable evidence | Residual / required external decision |
| --- | --- | --- |
| Wrong UF/substitution → net water error | Separate gross/substitution/storage/body ledgers; independent residual tests; measured balance detector | Correct equations do not establish calibrated pumps/meters or clinically acceptable water error |
| Wrong electrolyte composition → incorrect exchange | Finite mixing stocks, conductivity indication and six-solute bookkeeping | Conductivity is not a unique measurement of all electrolytes; composition-specific bench validation required |
| Heater or inlet disturbance → wrong delivered temperature | Finite heater model, temperature observation and fluid isolation | Sensor lag/bias and thermal exposure need measured calibration and approved limits |
| Air entry / empty or overfilled chamber → unsafe simulated return | Optical/level indications and blood stop | Stuck optical/level sensors and unmodeled bubbles remain detection gaps |
| Leak/disconnection → blood loss | Modeled leak indication, pressure/flow response and blood stop | No model of every disconnection or physical detector geometry; validate physical detection separately |
| Needle/tube obstruction → pressure or low flow | Pressure/flow observation; retained latch; conservative isolation | Same synthetic flow/pressure model is a common cause; low-flow latch needs a fresh run because no functional clearing test exists |
| Barrier breach / contaminated substitution | Modeled integrity failure inhibits delivery | Hidden contamination with nominal integrity is deliberately unobserved; no sterility claim |
| Wrong route or replacement loss → unmatched filtration | Route/supply/balance detectors and separate HDF ledgers | Actual routing valves, monitor independence and threshold justification require downstream evidence |
| Malformed/stale sample → erroneous decision | Bounded parsers, exact tick matching, separate role samples, protective invalidity response | Shared parser and clock defects can affect both channels |
| Failed STEP reply after accepted command → ambiguous plant state | Runner HALTs without COMMIT/ADVANCE; no retry; stop request/acknowledgment/observation separately recorded | Total communication loss can leave observed state unknown |
| Patient fails after plant COMMIT → inconsistent distributed transaction | Atomic patient validation, aborted prefix and diagnostics | No distributed rollback; an equipment step may exist without patient acceptance |
| Owner/host death → lost liveness or evidence | Parent-death handling, two-second wall lease, bounded stop tests, partial-record recovery | Host/kernel failure defeats all containers; cleanup is not observed actuator state |
| UI stale display or delayed confirmation → unintended action | Fresh epochs, single expiring intent, no automatic critical retry, measured state separate from request | Human comprehension, alarm perception and representative-user validation remain external |
| Numerical nonconvergence → misleading nominal output | Solver limitation and zero output; finite/positive inventories required before acceptance | Numerical conservation does not validate constitutive equations or the full operating envelope |
| Corrupt results/full disk → false evidence | Streaming hashes, atomic manifests, bounded readers, failed collection retention | No per-tick fsync and no signed attestation against a trusted malicious administrator |

Each row supplies a foreseeable event sequence, affected function, control and
remaining limitation. Clinical harm severity/probability, essential performance,
software class, risk acceptability and overall benefit/risk require an approved
intended-use/product analysis. Their absence is an approval gap, not permission to
invent a class, numeric probability or “acceptable” risk label.

## Current trust and common-cause analysis

The trusted computing base includes host/kernel, executable/configuration sources,
plant arbitration, runner administration and broker. A native same-UID developer
can access that developer's files/sockets. Compose restricts mounts, runs unprivileged,
drops capabilities, disables network and makes root filesystems read-only; it cannot
isolate a compromised host or correct a shared software defect.

| Boundary / threat record | Current controls / verification | Residual decision |
| --- | --- | --- |
| Device producers / T8-001 | Separate writable producer volumes, read-only clients; role/session tests and real Compose spoofing probes | A compromised producer can lie about its own observations; native same-UID trust remains |
| Process ownership / T8-002 | Parent-death signal with PID recheck; actual SIGKILL tests and partial evidence recovery | Kernel death can prevent final records; do not infer observed zero |
| DL1/DX1 parser availability / T8-003 | Frame/depth/worker limits, whole-frame deadlines, strict JSON; malformed/trickle tests | An authorized hostile local client can still deny availability or force stop |
| Broker identities/results / T8-004 | Per-incarnation random credential, revisions/run IDs, frozen configuration and hashes | Hashes are integrity checks, not authentication against trusted administrators recomputing them |
| Dependencies / T8-005 | Pinned selected sources, notices, actual binary/platform inventories and advisory tools | Native/container/host coverage differs; unresolved matching versions remain affected until justified otherwise |
| Publication/CI / T8-006 | Explicit allowlists, restricted Docker context, exact event-SHA fetch, read-only repository permissions, retained results | Maintainer and hosted runner compromise are separate trust assumptions |
| Shared model/host / T8-007 | Separate roles and samples, direct arbitration, watchdog, numerical/fault tests | Plant, parser, sensors, clock, runner and kernel remain common causes; container count is not independence |

These IDs map to the existing threat register. Its historical evidence links are not
a current execution claim. Current executions and environment blocks are listed in
[verification status](../testing/STATUS.md) and the audit evidence report.

## Dependency and vulnerability disposition

`dependency_inventory.json` and `gui_dependencies.json` identify selected application
sources; the default application policy remains MIT/BSD/Apache-2.0/zlib. Container
OS/interpreter packages and CI tools have separate inventories and license duties.
`dependency_report.py` rejects stale native/image source identities and builds the
SBOM from actual binaries and runtime modules. `security_scan.py` retains static
and advisory coverage, pagination, timestamps and unavailable queries explicitly.

The older `DEPENDENCY_FINDINGS.json` references its identified scan, not a current
clean-image assessment. Do not silently update its date or mark matches accepted.
A fresh image inventory/scan requires Docker and network access to the relevant
advisory source; responsible reviewers must then disposition reachability, fixes,
exceptions and residual risk. During this audit execution Docker and cppcheck are
unavailable locally. Hosted CI remains the execution route for those tools. Compiler
warnings and unit tests are useful evidence but do not substitute for that scan.

Technical triage can document a reachable function, remove unused attack surface,
apply a supported patch and rerun regressions. Risk acceptance, support lifetime,
formal normative applicability and independent approval remain assigned-role decisions.
