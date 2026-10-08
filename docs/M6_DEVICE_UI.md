# M6 device UI and connection contract

Phase base `445c667939d1fcdf37e46dea697f3c881dfbadca`, fixed before implementation.
This is an operator interface for simulated equipment only. Rendered realism,
automated UI tests and AI review do not establish clinical usability or conformity.

## Requirements and acceptance

| Requirement | Acceptance fixed before implementation | Links |
| --- | --- | --- |
| M6-REQ-001 | Build a C++ LVGL application with the selected SDL2 software backend; actual widgets run against M5 services in native and Compose headless deployment and an available graphical display. | HAZ-004,005 / M6-DES-001 / M6-TEST-001 |
| M6-REQ-002 | Setup/prescription offers HD/pre/post HDF and bounded blood/net UF/replacement input with visible units, error feedback and explicit confirmation; backend rejection never appears as success. | HAZ-002,003,005 / M6-DES-002 / M6-TEST-002 |
| M6-REQ-003 | Display authoritative machine state separately from intent; show measured pressures/flows/temperature/conductivity, separate UF/sub/net counters and timestamped trends. Invalid/stale/disconnected data must not become invented zero values. | HAZ-003,004,005 / M6-DES-003 / M6-TEST-003 |
| M6-REQ-004 | Show active protective constraints and synthetic priority; separate acknowledgment, bounded silence and guarded reset. No override or direct plant/admin access. Verify actual denied container connections. | HAZ-001,002,005 / M6-DES-004 / M6-TEST-004 |
| M6-REQ-005 | Detect reconnect/new service sessions, discard stale confirmations and clear old trends; do not automatically resend ambiguous critical requests. UI remains responsive during failed RPCs. | HAZ-001,004,005 / M6-DES-005 / M6-TEST-005 |
| M6-REQ-006 | Actual widget/service workflow, fault, input, stale/disconnect/reconnect tests and captured rendered evidence identify build/configuration/dependencies; earlier affected tests pass. | HAZ-001–005 / M6-DES-006 / M6-TEST-006 |

## Architecture and authority

LVGL runs on the main UI thread. A bounded worker polls the two device endpoints
and executes operator requests, keeping 500 ms transport failures out of rendering
and input processing. There is at most one queued critical UI action; server-side
M5 confirmation/state/protection guards remain authoritative. STOP bypasses the
ordinary UI confirmation dialog but still reports requested/acknowledged/observed
state separately. Lost acknowledgment is not evidence of success or zero outputs.

The UI uses only device control/protection endpoints. Compose mounts only device
sockets and an explicitly scoped capture directory; it receives no simulation
admin, patient, raw plant decision socket, Docker socket or network. Graphical
profiles may additionally mount the selected local display socket read-only.
Native same-UID mode is trusted development. Shared producer volume weaknesses
and common causes remain explicit M8 work; no security claim rests on a hidden menu.

The UI has no patient-model, circuit/dialyzer-model, fault injection, model truth
or virtual-clock controls. Sensor timestamps and treatment/trend time may be
displayed. Patient body volume/weight cannot be inferred from metered UF alone:
only measured gross UF, replacement and their net difference are shown.

## Session-bound device protocol

Additive device version 6 retains bounded `DL1` framing and the M5 observation/
machine schemas. Each decision service generates a fresh 128-bit random process
session identifier before publishing its device endpoint. This is freshness, not
authentication or a secret. Initialization failure must not use a fixed fallback.

- `HELLO6` returns `SESSION6 <32 lowercase hexadecimal characters>`.
- `STATUS6 session` returns `VIEW6 session MACHINE5 ... OBS5 ... INTENT5 ...`.
- `REQUEST6 session action`, `PRESCRIBE6 session mode blood net_uf replacement`,
  `CONFIRM6 session id`, `STOP6 session`, `ACK6 session` and
  `SILENCE6 session duration_ms` preserve the respective M5 role semantics.
- A wrong/old session returns `REJECT session` without changing plant state.
  Unsupported administration/actuator commands remain rejected. Legacy version-5
  device calls remain for the trusted deterministic runner and existing tests.
- Reconnection or a session change clears local pending confirmation and trends.
  A request with a lost reply is not automatically retried. Query current intent
  and effective state; require a new deliberate operator action where uncertain.

Machine metadata and frozen observations have distinct timestamps. UI validity
requires a valid observation matching its metadata sequence with nonnegative age
no more than the supported 1000 ms tick. Wall age over 1500 ms without a new sensor
sample is marked stale, even if a live service holds a paused simulation. A failed
RPC marks the corresponding channel disconnected. These are synthetic UI policies,
not clinical deadlines. Acceptance fixtures require display of communication loss
within 2 wall seconds; this is not a hard-real-time guarantee.

Read the two services independently and conservatively retain active constraints
while their snapshots differ. Never use an older unlatched view to erase a newer
protective alarm. Trends omit invalid samples and retain their actual sensor times.
The GUI is not a source of protective state and cannot release a plant constraint.

## Display and interaction

Keep a persistent SIMULATION indication. Present the lifecycle and connection
state, active alarms, measured circulation/quality values, metered fluid counters
and a trend area. Separate prescribed targets from measurements. Setup fields show
units and supported bounds. Critical dialogs summarize the exact requested action/
prescription, with distinct cancel/confirm controls; backend completion appears
only after it is observed. State changes can invalidate an open editor/dialog.

Blood/measurement/communication hazard bits use a synthetic high-priority visual
style; fluid-quality/balance bits use a synthetic medium-priority style. Active
constraints remain visible after acknowledgment/silence. No alarm audibility,
physical touchscreen performance or representative-user validation is claimed.

Use an original project bitmap font with distinct lowercase glyphs so `mL`,
`mmHg`, `mmol/L` and other units remain legible. Do not adopt bundled Montserrat,
FontAwesome or other separately licensed assets. Captures must come from the
actual LVGL framebuffer and real service state, not a mockup or fixed replies.

## Build, pacing and verification plan

1. Record pinned LVGL 9.6.0/SDL2 2.32.10 sources, selected/transitive licenses,
   disabled features, notices and integrity checks before adoption. Keep GUI
   libraries outside control/protection. Add an explicit optional CMake GUI build.
2. Implement/test the session wrapper and real UI client, bounded worker, widgets,
   original font and SDL/headless framebuffer backend.
3. Add external runner wall pacing for interactive use while preserving the
   integer virtual clock and liveness heartbeats. Default batch execution remains
   unpaced. The device UI must not control pacing.
4. Drive real widget events and RPCs for HD/pre/post, input rejection, confirmation,
   STOP, alarms, stale data and reconnection. Compare displayed state with service
   observations; test failed/ambiguous delivery and old-session confirmations.
5. Execute native headless, WSLg graphical and actual Compose UI integration;
   capture original rendered output. Record display-specific blocks accurately.
6. Deliberately admit named C/header/CMake sources and owned capture formats to
   publication tooling and Docker contexts; keep standards/private material out.
7. Run affected regressions, create candidate, execute one review against the
   frozen phase base, fix findings, regress and record final evidence before M7.

No license exception, clinical threshold or independent approval is implied by
these implementation choices. The full console/security/final-integration scope
remains required after this phase.

## Operating commands and evidence collection

```bash
python3 tools/fetch_gui.py
cmake -S . -B build/gui -DCMAKE_BUILD_TYPE=Release -DDIALYSISLAB_GUI=ON
cmake --build build/gui --parallel 3
DISPLAY=:0 SDL_VIDEODRIVER=x11 python3 tools/run_device_demo.py --output build/device-demo
python3 tools/run_device_demo.py --headless --seconds 15 --config scenarios/machine_air.json --output build/device-headless
python3 tools/verify_device_ui.py --build-dir build/gui --output build/ui-tests
DISPLAY=:0 SDL_VIDEODRIVER=x11 python3 tools/verify_device_ui.py --graphical --output build/ui-graphical
SOURCE_REVISION=$(git rev-parse HEAD) docker compose --profile device-ui build
python3 tools/verify_ui_compose.py --output build/ui-compose
python3 tools/verify_ui_compose.py --graphical --output build/ui-compose-x11
```

Native builds require existing C/C++17 tools and X11/Xext development packages.
On the inspected WSL2 host the already extracted platform package can be selected
without host installation using
`-DDIALYSISLAB_XEXT_PREFIX="$PWD/build/dependency-inspection/xext-platform/usr"`
and `-DXEXT_LIB=/lib/x86_64-linux-gnu/libXext.so.6`; this path is local evidence,
not a distributed dependency. Other hosts supply their own platform packages.
Use the pinned container build when those native development packages are absent.

The interactive native demo starts in preparation. PRIME, then CONFIGURE after
at least one modeled circuit-volume flush, review/confirm the HD/HDF prescription,
then START. PAUSE/START and STOP/RECOVER/RESET follow M5 guards. Closing the window
asks the external runner to abort with HALT and records observed shutdown state.
It does not imply clinical termination or patient return. Use a fresh output
path each time; numeric fields accept physical keyboard input, including backspace.
No physical touchscreen or alarm-audibility validation is claimed.

For scripted Compose observation use
`SCENARIO=machine_air WALL_SPEED=1 docker compose --profile device-ui up --abort-on-container-exit --exit-code-from runner`.
The optional `compose.device-x11.yaml` mounts only the selected `X0` display socket;
Linux/WSLg must already authorize that display connection. Do not weaken display
access controls. GUI failure leaves the protective services independent of UI.
Copy `/captures` from device-ui and `/results` from runner before removing volumes.
The automated Compose UI verifier retains both, logs and the original failure
code; extraction failure retains resources and records recovery commands.

Pressure trends use actual sensor timestamps as their x coordinates, bounded to
120 received valid samples. UI polling can skip simulation samples; it is not a
complete experiment recorder. Only the external runner's JSONL is the full record.
`--test-input` enables bounded stdin widget events for the verification harness;
it has no administrative protocol and does not replace real service responses.
PNG evidence is encoded from the actual RGB framebuffer with no external image
assets. Publication requires each owned capture's explicit path, provenance,
command and matching digest; arbitrary images/metadata remain excluded.


## Single-review corrections

The sole M6 review (`00baa58` against `445c667`) identified six P2 defects.
Same-session reconnection now invalidates confirmation/trends without refreshing
an unchanged sensor sample's wall age. A new session or new sample starts a new
age. SDL pointer transitions are queued (128 maximum) until LVGL consumes them;
a down/up pair in one event batch still activates a widget. Queue overflow
releases input with explicit feedback. The test harness covers the actual SDL
path, including STOP, as well as direct LVGL events.

Prescription confirmation and wire values share the same round-trip decimal
representation; `0.04 mL/min` cannot be displayed as zero while being submitted.
Effective prescriptions also preserve that precision. Negative text remains
visible for range rejection. Alarm, delivery and feedback regions reserve room
for every supported hazard plus disconnected-state annotations in an 1100x890
framebuffer; a maximum-mask real-plant fixture checks non-overlap.

The demo distinguishes normal window closure/duration expiry from an unexpected
simulation abort. Unexpected workflow/communication failures return nonzero even
if HALT succeeds. Pacing checks window closure at bounded 100 ms wait intervals,
while keeping liveness heartbeats and virtual time separate. The recorded aborted
tick identifies the unexecuted next tick. A real 1-second demo at wall speed .001
must stop within 4 seconds, not wait for its 100-second tick interval.

GUI-driven experiments include external operator input and are not claimed to
replay from the initial scenario alone. Widget test input/output logs, actual
trajectory and build/configuration identify these runs. M7 must add a reproducible
operator-event schedule for experiment replay. Deterministic batch scenarios
without external interaction retain the existing exact-hash acceptance.


Visual integration finding M6-V1 adds an explicit light dialog foreground; the
confirmation-detail framebuffer must provide at least 7:1 luminance contrast
between its rendered glyphs and background. This is a project software display
criterion, not a claim of clinical usability or accessibility conformity. The
actual frame is checked after rendering, alongside exact-value and SDL input tests.

M7 scheduled experiment deployments allow device observation and immediate STOP;
ordinary requests receive authoritative `REJECT scheduled` feedback. The external
console, never this UI, owns configuration, fault calendars and virtual pause.
A device STOP interrupts the experiment and requires fresh services for replay.
