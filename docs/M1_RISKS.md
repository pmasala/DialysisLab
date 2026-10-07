# M1 change impact and limited risk analysis

This is a project-derived, synthetic simulation analysis, not an accepted medical
risk file. Numerical limits were fixed in M1_PLAN before implementation. Clinical
severity/probability estimates, residual-risk acceptance and independent review
remain unassigned/open. Implementation and test author: Codex, at the project
owner's request; no reviewer independence is claimed.

| Existing hazard | M1 event sequence / consequence | Design and verification | Remaining limitation |
| --- | --- | --- | --- |
| HAZ-001 | Decision service accesses scenario state or impersonates protection | Separate mounted socket capabilities; listener-based authorization; role-denial and container-boundary tests; M1-REQ-001 | Same UID native processes are trusted; shared host/runner compromise not contained. |
| HAZ-002 | Occlusion raises circuit pressure while control continues blood/UF demands | Independent observation and direct TRIP to latched plant arbitration, M1-REQ-004/005 | No real actuator, compliant tubing, clotting, blood return or approved recovery. Stopping flow could introduce real clinical risks outside this model. |
| HAZ-003 | UF integration or misinterpreted blood recirculation changes patient volume incorrectly | Separate patient service, compensated plant sum, Decimal patient ledger and independently derived test balance, M1-REQ-003 | No HDF, refill, electrolytes or dialyzer fidelity. Patient failure after plant commit leaves an explicitly uncommitted tick in the aborted manifest; no distributed rollback or successful conservation claim for that run. |
| HAZ-004 | Stale, missing, invalid or misordered sensor data is treated as current | Separate channel validity/sequence/time validation, conservative zero control demand and protective latch, M1-REQ-006 | Sensors are noiseless and share physical equations; bias, latent sensor faults and diverse sensor hardware remain unimplemented. |
| HAZ-002/004 | Decision service dies, hangs, or messages disappear | Per-tick fresh demand/permit; wall-clock role leases; process-loss tests, M1-REQ-007 | Host overload can exceed tested budgets; no hard real-time or malicious-flooding guarantee. |
| HAZ-002/004 | Scheduler stops or pauses | Bounded wall-clock watchdog separate from integer virtual clock; heartbeat during intentional pause | Shared kernel/clock/transport are common causes. Plant death removes simulated physics; this says nothing about physical equipment on power loss. |

The plant's three listeners run one bounded event loop: abusive traffic on one
listener can reduce availability of others. Bounded parsing and fail-closed
protocol handling contain ordinary malformed-message cases, not a complete DoS
argument. No TCP interfaces, Docker socket, privileged containers, secrets or real
patient data are used. Containers drop all capabilities, are read-only, have no
network, and run as UID 10001 with narrow volume mounts and memory/PID limits.

A latch has no runtime reset path. A fresh run must start all services and sockets
from zero. Losing an acknowledgment aborts rather than retrying integration. SIGTERM
is orderly; SIGKILL of control/protection/runner is covered by decision/lease policy.
After a patient or plant failure the runner reports `aborted`, never `completed`.
Configuration, source and binary hashes make stale results identifiable, but a hash
is not authenticity proof or validation of the model. Publication remains a manual
content/rights review plus explicit format/path allowlists.

Full HDF, online preparation, alarms/UI, multiple dialyzers, physical validation,
threat modeling, vulnerability scanning, risk acceptance and the release gates in
ASSURANCE_PLAN remain required. No existing requirement or standards item is
closed merely because M1's narrower synthetic tests pass.
