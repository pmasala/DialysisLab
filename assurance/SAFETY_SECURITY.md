# Safety and cybersecurity design obligations

Status: project-derived design obligations for development; not a completed risk management file, threat model, or normative clause assessment.

M1's implemented subset, failure sequences, controls, common causes and residual
limitations are recorded in `docs/M1_RISKS.md` and linked through M1 requirements
in `traceability.json`. Its synthetic thresholds are not clinical safety limits.

## Functional safety work

Define essential performance with measurable limits and exposure-time bounds before claiming protective coverage. Record the path hazard -> foreseeable events -> hazardous situation -> harm -> initial risk -> controls -> verification -> residual risk. Include normal operation, startup, treatment transitions, interruption/recovery, single faults, relevant combinations and common causes.

Starting hazard families to analyze include: excessive/insufficient fluid removal; electrolyte/composition error; temperature error; air delivery; blood loss/leak/disconnection; excessive pressure/suction; clotting/flow interruption; incorrect substitution routing or balancing; contaminated substitution fluid; sensor bias/stale data; pump/valve/clamp failure; loss of power/process/communications; alarm failure; use error; and corrupted configuration/software. This seed list is not an exhaustive analysis and does not assign clinical thresholds.

### Control/protection independence

Maintain separate state and decisions, independently modeled measurement faults and a direct protection-to-actuator-arbitration path. Assess shared algorithm, configuration, libraries, messaging, clock, kernel, resource exhaustion, sensors and power as common causes. A container split is not proof of independence. Define what faults the model can demonstrate and what would require hardware separation or other downstream risk controls.

Specify hazard-specific protective states, outputs, timing, alarm behavior, latching, permitted operator action and recovery conditions. Do not use an unanalysed global "stop everything" rule. Define behavior when protection itself fails or communications disappear. No automatic restart/recovery may bypass safety-state evaluation.

For every measurement specify units, sign convention, range, update rate, age/validity, calibration, noise/bias/delay and plausibility checks. For every command define authority, state-dependent permission, limits, acknowledgment, timeouts, duplicate handling and failure behavior.

### Examples requiring particular attention

- HDF gross ultrafiltration and replacement fluid must not be confused with net patient fluid loss. Evaluate substitution interruption, incorrect routing and mismatched estimates.
- Circuit pressure, patient blood pressure and hidden model truth must remain distinct variables; sensing assumptions must match the chosen circuit.
- Loss of a UI display or alarm-delivery path needs a defined response. Acknowledgment/silence is distinct from hazard removal and reset.
- Sterility/contamination models are surrogate assumptions; no hydraulic calculation can establish actual fluid microbial quality.

## Cybersecurity work

Create a versioned asset inventory, data-flow/trust-boundary model, attacker assumptions and threat register. Relate threats to hazardous situations where loss of integrity/availability can affect simulated treatment. Assess the reference project's real host/data exposure as well as the future device implications.

| Boundary/asset | Candidate abuse | Required design/verification work |
| --- | --- | --- |
| Device commands | Forged, replayed, reordered or unauthorized commands | Endpoint identity/authorization, freshness/sequence policy, state validation and negative tests. |
| Simulator administration | Device UI changes patient truth or bypasses protection | Distinct privileges and APIs, enforced network/access boundaries, denial tests. |
| Telemetry | Stale/corrupt values accepted as current | Schema/range/unit validation, age and validity handling, deterministic fault tests. |
| Host/container runtime | Privilege escalation or resource starvation | Least privilege, narrow mounts, no Docker socket, resource budgets, host failure analysis. |
| Configurations and models | Silent modification of patient/circuit/limits | Schema validation, provenance/integrity, controlled changes, recorded run snapshots. |
| Updates and dependencies | Malicious or incompatible artifact | Provenance/integrity verification, pinning, dependency assessment and update/recovery tests. |
| Logs/results/datasets | Tampering, leakage or storage exhaustion | Appropriate access controls, privacy-aware data use, audit integrity and retention/resource behavior. |

Choose cryptographic protocols only after the trust model is set; do not invent custom cryptography. Include credential provisioning/rotation/revocation, absence of default shared secrets, authentication failures, secure update rollback constraints, vulnerability disclosure/intake, triage/patch response and support lifetime in the secure lifecycle.

Security controls must preserve required safety response bounds. Validate behavior under denied traffic, flooding, invalid messages, full disks and corrupted state. Encryption or a vulnerability scan alone is not a cybersecurity assurance case.

## Evidence and review

Risk controls need both implementation verification and effectiveness verification. Evaluate new risks introduced by controls. Record risk acceptability criteria and authorized residual/overall risk decisions; a test pass is not risk acceptance. Findings from tests, dependencies, misuse, incidents, and security updates feed back into the risk/threat files.

Formal classification, numerical response limits, residual-risk decisions and the full hazard/threat analyses remain open in this package.

## M4 treatment increment

HAZ-003/006 include wrong route/composition/temperature, interruption of replacement
with continuing gross UF, occluded filters and unobserved quality-barrier failure.
M4 observed quality signals latch fluid-only isolation directly at the plant;
blood circulation remains subject to HAZ-002/004 pressure/validity protection.
Sensor snapshots precede integration: a physical deviation arising during a tick
can be delivered until the next observation. Synthetic timing tests measure this
latency; it is not a clinical acceptance of delivered exposure. Conductivity cannot
identify individual species; hidden contamination/breaches without a failed modeled
integrity test remain latent. Shared sensors/plant/runner/host remain common causes.
No sterility, hardware independence or residual-risk acceptance is claimed.

## M5 lifecycle increment

HAZ-002/004/005 address unguarded startup/recovery, ambiguous confirmations,
communication loss and alarm annotation mistaken for release. M5 retains latches
at plant arbitration, rejects automatic restart/override, and requires measured
safe recovery plus completed priming before treatment. Air/leak and positive
pressure/low-flow hazards isolate blood and fluids; quality/balance hazards retain
blood circulation during treatment but stop external flush pumps. Simultaneous
hazards combine. Low-flow/filter latches lack a functional reset test and require
a fresh run; retained high pressure is not silently erased. A stuck optical/supply
detector is a declared latent fault, not covered by hidden truth access.

HAZ-003/006 include priming/cleaning source/waste accounting. Flushed volume is a
synthetic readiness criterion only. UI endpoints cannot issue admin/raw actuator
commands. The shared device volume/UID and bounded synchronous handlers still have
endpoint impersonation and availability common causes for M8 analysis; native
same-user mode is trusted development. No hardware independence, clinical limits,
air removal, disinfection or residual-risk acceptance follows from these tests.


## M6 operator interface increment

HAZ-001/004/005 include stale data presented as current, obsolete confirmations,
lost pointer events, rounded intent, obscured alarms and ambiguous shutdown.
Session-bound requests reject old epochs; same-session reconnect does not renew
sample age. Bounded worker communication keeps rendering separate from RPCs.
Exact decimal confirmation, queued SDL transitions and complete alarm regions
are verified against actual services/framebuffers. ACK/silence do not release
constraints; STOP acknowledgment remains distinct from received measurements.
The UI mounts device endpoints only and has no simulation truth/admin channel.
UI/X11/host or shared code failures remain common causes, not hardware independence.
Native same-UID trust, shared device producers and broader abuse/availability
controls remain M8 work. No human residual-risk acceptance is inferred.

## M7 experiment administration increment

DX1 is separate from device DL1 sockets. The broker validates configuration before
fresh service activation; live runs use immutable configuration and scheduled
fault/workflow calendars. A filesystem-separated random credential, bounded frame
size/deadline, four connection workers, one artifact job, bounded run/event inventory
and explicit generated artifact names constrain administrative access/resources.
Console disconnect does not replay commands. Reused request IDs are idempotent
only for identical requests. External device STOP remains immediately authoritative;
scheduled experiments abort and retain actual stop observation rather than claiming
successful replay. See `docs/M7_EXPERIMENTS.md` and M7 trace requirements.

The console/broker are trusted simulation administrators, not clinical operators.
Native same-UID access, inherited OS/kernel/configuration, shared device producer
ownership and abrupt native broker orphan cleanup remain explicit M8 hardening
work. Token freshness does not establish hardware independence or eliminate
common-cause failure. No licensed standards or credentials belong in exports.
