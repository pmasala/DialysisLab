# Detailed design: interfaces, ordering and failure

Document ID SDD-03; revision 1; review candidate. Requirements: REQ-001/002/004/005,
M1-REQ-005…009, M5-REQ-003…006, M7-REQ-003…006, M8-REQ-001…006.
Previous: [Models](MODELS.md). Next: [Interaction](INTERACTION.md).

## Interface inventory

Paths below are relative to the run's runtime directory. Experiment supervisors
create run-specific locations and aliases; clients must not infer authority from a
path string alone. Mount permissions and server role checks enforce the boundary.

| Interface | Producer / consumer | Content and permissions |
| --- | --- | --- |
| `admin/plant.sock` | Plant / runner | Configuration, PREPARE, COMMIT variants, HALT and internal inspection |
| `control/plant.sock` | Plant / control | Own sensor sample, demand, guarded machine changes; no protective override |
| `protection/plant.sock` | Plant / protection | Own sample, protective mask and guarded reset |
| `control/service.sock` | Control / runner | Tick requests and scheduled operator forwarding |
| `protection/service.sock` | Protection / runner | Tick requests and scheduled protective forwarding |
| `patient/service.sock` | Patient / runner | Initialization and ordered conservative transactions |
| `device/control.sock` alias | Control / device UI | Session, observations, treatment intent/confirmation, immediate STOP |
| `device/protection.sock` alias | Protection / device UI | Session, observations, alarm annotations and confirmed reset |
| `broker.sock` in API directory | Experiment broker / external console | DX1 credential-protected configuration, run control, replay and export |
| `trajectory.jsonl`, `manifest.json` | Runner / evidence readers | Persisted observations, truth and identity; never an actuation interface |

DL1 uses ASCII tokens, a newline terminator and one request/reply per connection.
Parsers reject nonfinite values, surplus fields and values outside their local bounds.
Positional numeric fields with overlapping bounds cannot necessarily detect reordering;
producer/consumer conformance therefore needs explicit tests. Known decoder bound
differences are recorded in the current protocol specification. Core
frames have a 4096-byte bound and 500 ms exchange deadline. Distributed patient
**responses** explicitly allow 32768 bytes; this does not enlarge plant/control
requests. Trajectory lines also have a 32768-byte cap. DX1 has a separate bounded
JSON framing and credential contract in [experiment_rpc.py](../../python/dialysislab/experiment_rpc.py)
and [current wire protocol](WIRE_PROTOCOL.md). Do not reuse DL1 assumptions for DX1.

## Current protocol families and ownership

| Family | Purpose | Encoder / decoder |
| --- | --- | --- |
| CONFIG2, TRANSPORT2, circuit transaction | Hydraulic topology, membrane properties, per-step exchange | [circuit.py](../../python/dialysislab/circuit.py), [plant.cpp](../../src/plant.cpp) |
| ONLINE4 and treatment transactions | Fluid preparation and PRE/POST routing | [treatment.py](../../python/dialysislab/treatment.py), [online.hpp](../../src/online.hpp) |
| MACHINE5 / MACHINE8 | Legacy / guided authoritative state and counters | [machine.hpp](../../src/machine.hpp), [machine.py](../../python/dialysislab/machine.py) |
| OBS5 / OBS8 / OBS9 / OBS10 | Successive sensor payloads, adding guided, physical and dynamic fields | `MachineObservation::encode`, `usable5`, Python observation decoder |
| PHYSICAL9, FLUID9 | Physical blood and preparation configuration | [physical.py](../../python/dialysislab/physical.py), plant admin parser |
| DYNAMICS10, INVENTORY10, BLOOD9 | Dynamic configuration and timestamped blood properties | Same pair; no device-side configuration authority |
| REQUEST / CONFIRM / STATUS session variants | Requested, queued and observed operator actions | [control](../../src/control.cpp), [protection](../../src/protection.cpp), [device_session.hpp](../../src/device_session.hpp), [client.hpp](../../src/ui/client.hpp) |

The number on a payload is not a single global software version. For example, a
VIEW5 envelope can contain MACHINE8 and OBS10. The current implementation accepts those versioned combinations explicitly. Historical
wire lists are retained through the Project Log for compatibility analysis only.
The controlled [wire protocol](WIRE_PROTOCOL.md), [fixed-field dictionary](WIRE_FIELDS.md)
and [patient JSON dictionary](JSON_FIELDS.md) now specify current extensions. The
fixed-field register covers 32 message forms and 394 ordered fields with units and
bounds. Selected actual serializers are compared with that register in
[test_document_contracts.py](../../tests/test_document_contracts.py). Source hashes
force review when an inspected parser changes. Exhaustive boundary conformance and
independent approval remain separate gates; known implementation discrepancies stay open.

## Ordered transaction and failure behavior

The runner validates configuration before initialization, configures plant and
patient, then advances contiguous sequence numbers from zero with integer start
timestamps. It updates accepted patient-derived coefficients before PREPARE.
PREPARE freezes observations; both services submit their decisions. COMMIT requires
both fresh decisions and applies their intersection with active restrictions.
The returned equipment snapshot is atomic within the plant; a separate later
STATUS read must not be substituted for it when reconstructing balances.

On either failed STEP, the runner still attempts the other service, then HALTs and
aborts without COMMIT or patient ADVANCE. It must handle a lost reply after a command
was accepted exactly as a failure, not guess that it was safe to continue. HALT
invalidates pending decisions and further tick commits. No ambiguous tick is retried.

Patient ADVANCE follows plant COMMIT. Failure here means a plant step exists without
an accepted patient step; no distributed rollback is implemented. Persist the failure,
completed prefix and any available transaction diagnostics. Do not claim an entirely
committed simulation record. The patient service itself validates prospective state
before replacing its accepted inventories.

A stop request, its acknowledgment and observed zero outputs are three separate
facts. An absent observation is unknown, not zero. Lost runner/control/protection
liveness causes a wall-clock watchdog stop: nominal lease is 2 s, with a tested
acceptance bound of 3 s. During a virtual pause, PINGs maintain liveness without
advancing physiology. These are software scheduling bounds, not hard real time.

## Persistence and recovery

[Trajectory writer](../../python/dialysislab/trajectory.py) writes one record at a
time and hashes the bytes actually written. The initial manifest says running;
completion or abort replaces it atomically. Process death may leave a partial last
line; recovery accepts only a valid contiguous complete prefix, rejects malformed
complete records and never rewrites original evidence. No per-tick fsync means
power-loss durability is not claimed.

[Compose collection](../../tools/verify_compose.py) retains failure logs and available
artifacts before volume cleanup. Failed extraction must leave recovery instructions
and retained volumes. The manifest, source/build/configuration identities and actual
trajectory hash must agree before replay or comparison is trusted.

Common-cause failures remain: shared host/kernel, protocol code, simulated sensors,
trusted runner and writable resources. Security design and vulnerability handling
are in [M8](../M8_SECURITY_CI.md), [threat register](../../assurance/THREATS.json) and
[SECURITY.md](../../SECURITY.md). Their findings require disposition, not merely links.

Verification: [failure/deployment protocol](../testing/FAILURES.md). Unsafe output
arbitration, malformed messages, role spoofing, stale frames, lost replies and
artifact recovery must be exercised on actual processes/containers where stated.

Current protective thresholds, failure sequences, trust assumptions and dependency
dispositions are specified in [protective and security design](SAFETY_SECURITY.md).
