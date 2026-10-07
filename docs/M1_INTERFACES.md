# M1 interface contract, DL1 (abort-policy revision 2)

Defined before implementation. Linux AF_UNIX streams, one request and one response
per connection, ASCII space-separated tokens ending in LF, maximum 4096 bytes.
Every message begins `DL1`; unsupported versions, unknown operations, trailing
tokens, invalid numbers and out-of-range fields return `DL1 ERR protocol`.
Transport deadline is 500 ms per exchange; startup retries last at most 10 wall
seconds. Integers are decimal nonnegative integers; floating values must be finite.
No private source text or request payload is logged on error.

## Endpoints and authority

Paths are relative to `--runtime-dir` (default `/run/dialysis`).

| Socket | Caller | Requests |
| --- | --- | --- |
| `admin/plant.sock` | Runner | PREPARE, COMMIT, STATUS, PING, HALT, STOP |
| `control/plant.sock` | Control | SENSE, DEMAND, PING |
| `protection/plant.sock` | Protection | SENSE, PERMIT, TRIP, PING |
| `control/service.sock` | Runner | STEP, PING, STOP |
| `protection/service.sock` | Runner | STEP, PING, STOP |
| `patient/service.sock` | Runner | INIT, ADVANCE, STATUS, PING, STOP |

Control/protection have only their own socket directory mounted. Patient has only
its own directory. Runner mounts all four. No ports or networks are used. Endpoints
are capabilities provided by mount visibility, not cryptographic authentication.
The host and runner are trusted. Same-user native mode does not enforce this split.

## Tick, measurements and commands

`n` is a contiguous tick sequence starting at 0; `t` is integer virtual milliseconds
at the start of a tick; `dt` is 100 ms in the acceptance configuration (allowed
1..1000). First `t=0`; next `t=previous t+dt`. Duration is at most 100000 ticks.
There is only one tick in flight. Every state-changing tick operation is accepted
once; duplicates, skips, future times and reordered operations are rejected.

1. Runner sends `DL1 PREPARE n t dt resistance control_fault protection_fault`.
   Plant freezes independently modeled sensor records from the preceding actuator
   state with the current physical resistance. Reply `DL1 OK`.
2. Runner sends control `DL1 STEP n t blood_mL_min uf_mL_min`. Control reads
   `DL1 SENSE n t` from its plant listener and writes `DL1 DEMAND n t blood uf`.
   Invalid measurements produce zero demand. Reply `DL1 OK`.
3. Runner sends protection `DL1 STEP n t pressure_limit_mmHg`. Protection reads
   its own SENSE and sends either `DL1 PERMIT n t` or
   `DL1 TRIP n t reason` directly to plant. Reply `DL1 DECISION reason`, where
   reason is `none`, `pressure`, or `measurement`. It does this even if control
   has died; no control acknowledgment or computed pressure is an input.
4. Runner sends `DL1 COMMIT n t`. Fresh control demand and a fresh protection
   decision are required. A missing decision or any active latch gives zero blood
   flow, zero UF and clamp closed. Integration happens only here. Reply is STATE.
5. Runner sends patient `DL1 ADVANCE n t dt removed_mL`; patient independently
   tracks its fluid volume and replies VOLUME. The record is then committed to the
   run output. A patient failure aborts; no incomplete tick is called successful.

SENSE reply: `DL1 OBS n_sample t_sample valid blood_mL_min pressure_mmHg uf_mL_min`.
Validity must be 1, sequence and timestamp must equal the requested tick, and
measurements must be finite and in range: blood 0..500, pressure 0..1000, UF 0..20.
Pressure is positive circuit gauge pressure, not patient blood pressure. Sensors
are noiseless in M1. Faults: `none`, `invalid` (valid=0), `missing` (valid=0 with zero
values), `stale` (previous frozen sample), `future` (timestamp + dt), `replay`
(previous sequence with current timestamp; sequence 1 at startup). Invalid startup stale samples carry valid=0. Physical occlusion
changes resistance separately from sensor faults.

STATE: `DL1 STATE n t_end blood pressure uf removed_total removed_tick latched clamp_closed reason`.
It is observer-only truth and never sent to control/protection. Before any tick,
STATUS uses n=0, t_end=0 and zero outputs. Reasons additionally include
`control_missing`, `protection_missing`, `liveness`, `protocol`, `shutdown`.
First latch wins. Clamp is closed iff latched; startup also has zero outputs.
Positive DEMAND cannot clear a latch, and PERMIT never resets it.

Patient INIT: `DL1 INIT volume_mL`; allowed once, range 1000..100000. ADVANCE uses
nonnegative removal <= 20*dt/60000 mL and cannot take volume below zero. Reply
`DL1 VOLUME n t_end volume_mL removed_total_mL`. STATUS returns the last VOLUME.
All request/response numbers use full binary64 round-trip decimal precision.

## Liveness and lifecycle

Services start with zero outputs, no permit and no treatment advancement. Socket
binding refuses an existing path: stale runs require explicit cleanup after all
processes exit. Runner waits for PING readiness, then initializes patient.
PING replies `DL1 OK`; control/protection PING also contacts its plant listener.

Once armed by PREPARE, plant tracks a separate monotonic wall-clock lease for
runner, control and protection. Any lease exceeding 2000 ms latches `liveness`
and zeroes actuators, without integrating fluid or incrementing virtual time.
The poll loop checks at least every 20 ms when idle; bounded failed I/O can delay
checking, with the tested acceptance bound 3 s. A deliberate virtual pause calls
all three PING paths every <=250 ms. No wall duration enters model equations.

At a control/protection STEP RPC failure runner still attempts the other decision,
but never sends COMMIT or patient ADVANCE for that tick. It requests HALT, then
independently queries STATUS and aborts. This includes a STEP reply lost after the
service's command was accepted. The manifest records the aborted tick, RPC cause,
HALT acknowledgment, observed state and any separate request/observation error.
An acknowledgment proves acceptance of HALT, not an observed actuator state.
Missing STATUS leaves `outputs_zero_observed=null`; an observed running plant gives
false. Unacknowledged HALT leaves pending-tick cancellation unconfirmed, even if a
later observation shows zero outputs. No tick command is retried.
Plant/patient failures abort without advancing another tick. On runner loss the plant watchdog remains
independently active. STOP and SIGTERM latch zero outputs and exit; SIGKILL of the
plant removes the simulated plant itself (no physical device is controlled).
HALT latches zero outputs, discards any prepared tick and pending decisions, and
permanently rejects further PREPARE/COMMIT/DEMAND/PERMIT in that process. Liveness
and protocol shutdowns do the same. It leaves the process alive for observation
and Compose orchestration. If HALT cannot be delivered, the independent wall lease
eventually cancels the pending tick; the runner does not claim this without an
observation. STOP additionally exits. Neither has clinical recovery meaning.
Fresh processes and sockets are required
for a new run. Malformed commands on plant decision/admin listeners latch
`protocol`; denied role operations also fail closed. Availability under hostile
flooding and shared-host failures is outside M1's verified envelope.

## Run artifacts: manifest schema 2 / trajectory JSONL v1

New runs use `manifest.json` schema_version=2 with
`trajectory_format="dialysislab.trajectory.jsonl.v1"` and
`trajectory_file="trajectory.jsonl"`. DL1 sensor/command fields and model equations
are unchanged. Historical schema-1 manifests and `trajectory.json` arrays remain
unaltered historical evidence; they are not input to the new streaming reader.

Each UTF-8 JSONL line is one complete record with the existing physical, patient
and observation fields, sorted keys, compact separators and a terminating LF.
`sequence` starts at zero and must be contiguous. A record is capped at 16384 bytes.
The writer holds one record at a time, writes without Python output buffering, and
incrementally hashes only bytes successfully written, including each LF. The final
manifest records completed ticks, byte count, exact SHA-256 and peak process RSS.
The returned Python result is a disk-backed iterable, not an in-memory list.

An atomic initial manifest has `outcome=running`, no final hash, and the exact
configuration/build. The final manifest replaces it atomically after the stream is
closed. SIGTERM/INT requests abort and observed stop; SIGKILL may leave the initial
manifest and a partial last line. Never interpret that manifest as success or its
initial tick count as the persisted prefix. `tools/recover_trajectory.py` counts,
validates and hashes complete lines; it discards only an unterminated final line
and never rewrites evidence. A malformed complete line or sequence gap is an error.
Complete writes survive process death through the OS cache; power-loss durability
is not claimed (no per-tick fsync). Disk failures may prevent final metadata, but
an already written prefix remains recoverable. STOP does not imply rollback.
