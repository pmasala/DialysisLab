# Complete browser execution candidate

Request recorded before implementation, 2026-10-16: run the complete coupled
simulator and existing LVGL UI in the browser without a remote computation backend.
Base: b0f0ba3860b5f5a9c317074ddf4cc535a577fb7c.

| Requirement | Proposed acceptance before execution |
|---|---|
| WEB-REQ-001 | Run production C++ Plant, control/protection decisions and existing Python patient/physical coupling locally using WebAssembly and Pyodide. HD/PRE/POST must reach treatment with finite results and conserved water/solute inventories; no replacement physical equations or prerecorded telemetry. |
| WEB-REQ-002 | Render existing LVGL guided views in a browser canvas with touch/pointer input and working lifecycle actions, prescription, STOP, detail tabs and reduced motion. Keep simulation time independent of animation frame rate. |
| WEB-REQ-003 | Compare the same deterministic scenarios/commands and initial conditions in native and WebAssembly execution. Discrete stages/alarms must match exactly; finite numeric outputs use abs(a-b) <= 1e-8 + 1e-9*max(abs(a),abs(b)), in each field's documented units. Water and solute conservation retain existing 1e-6 mL/mmol bounds. These are proposed portability budgets, not global numerical accuracy approval. |
| WEB-REQ-004 | Serve static assets only; computation and patient state stay in the browser. Pause when hidden, do not catch up elapsed wall time, prevent overlapping ticks; stop advancing after runtime failure and report unavailable state. Reset must discard queued actions and old patient state. |
| WEB-REQ-005 | Pin toolchain/runtime dependencies, preserve source/configuration identifiers, build instructions and native/Wasm comparison results. Published build must identify its source and dependency artifacts. |

Design: Emscripten C++/LVGL canvas frontend plus worker with C++ Plant and Pyodide
Python patient. A deterministic local scheduler replaces process/socket transport.
The C++ source and Python equations are reused. Model transport is not translated
to JavaScript. Browser and native targets share scenarios and explicit time steps.
The browser is one fault domain: process isolation, independent service watchdogs,
Unix IPC and real-time scheduling are NOT preserved or claimed. Browser suspension
must not be represented as delivered treatment. This target is an educational
simulator, not a medical-device runtime, and cannot close CLOSE-NUM-01.

First acceptance covers the complete guided device/patient cycle for supplied
HD/HDF scenarios. Native experiment-console tooling, arbitrary scenario editing,
long-duration performance and mobile-browser qualification remain separate scope.
No prior native pass is inherited by this target. Dependency exceptions and
independent review remain explicit before merge/release, not silently approved.

## Implemented boundaries

`control_service.hpp` and `protection_service.hpp` contain the original native role
handlers, extracted without changing their decision bodies. Native executables
inject Unix RPC; `src/browser/engine.cpp` injects local Plant calls. The browser
engine preserves role selection, intent confirmation, session epochs, explicit
PREPARE/control/protection/COMMIT ordering and all final-delivery guards.
`python/dialysislab/browser.py` uses existing encoders, validators, physical feedback
and distributed patient transactions. One worker owns one interpreter/session;
module transport binding is not a multi-session server API.

`src/browser/ui.cpp` reuses the complete production device UI. A conditional client
replaces only its background socket thread with worker messages. It preserves
rendering, action eligibility, confirmation dialogs and telemetry freshness checks.
No pthread/shared-memory deployment headers are required. The HTML wrapper provides
mode/reset, virtual-clock pacing and state export. Browser viewport widths below
800 logical pixels scroll the existing supported UI; phone-specific redesign is
not claimed. All runtime assets are downloaded from the same static origin.

Build identity records the base Git revision, dirty state, exact source hashes,
dependency lock and all static-asset hashes. Execution evidence binds the actual
compiled artifacts, not only a branch name. See [verification](../testing/BROWSER.md)
and [dependency decision](../dependencies/BROWSER_DEPENDENCIES.md).

## Manual session lifetime correction — 2026-10-17

WEB-REQ-006 (recorded before implementation): an explicitly interactive browser
session shall allow the operator to wait in PREPARATION beyond the scenario's
batch tick count, then complete the confirmed PRIME and subsequent lifecycle
commands. Batch sessions retain the configured finite tick limit. Export shall
identify the execution profile. Physical time, consumable inventories, conservation
checks, STOP, stale-session rejection and fail-stop protections remain active.

Rationale: the supplied 2,200-tick experiment horizon is not an operator deadline.
At dt = 500 ms it represents 1,100 simulated seconds; accelerated manual operation
can exhaust it while the operator is deciding what to press. Freezing physical
time silently or changing the physical equations would conceal simulated behavior.
The user can pause the virtual clock explicitly.

Prospective acceptance: in HD, HDF PRE and HDF POST, hold PREPARATION until
2,400 ticks (1,200 simulated seconds), issue PRIME through the existing confirmed
command API, observe PRIMING, and reach CLEANED with zero alarms and existing
1e-6 mL/mmol conservation bounds. Compare native/Wasm trajectories using WEB-REQ-003
budgets, with identical commands and tick times. A bounded session must still
reject the first step beyond its configured count; malformed sequence must still
stop and reject further ticks. Exercise delayed manual PRIME in the actual browser.
This is a session-lifecycle regression, not long-duration physical qualification.

For a scripting-only repair, compiled assets may be reused only after checking
all recorded source and CMake inputs used by C++ and the dependency lock against
the candidate, plus verifying the base artifact hashes. Record the base build
identity and unchanged binary hashes in the new identity; otherwise rebuild.
Independent review and numerical/clinical validation are not inferred.

Deployment follow-up, recorded before implementation: after a successful Pages
deployment, normal reload still displayed the previous build identity. For this
repair WEB-REQ-006 also requires the wrapper to request the corrected app, worker,
Python bundle and displayed identity using a shared version query. Unchanged C++
binaries keep their verified hashes. Acceptance: a fresh page load displays the
new source input identifier and passes the delayed manual PRIME interaction.

## Mobile layout and fluid identity — 2026-10-17

Recorded before implementation. WEB-REQ-007: the production LVGL guided interface
shall reflow at phone widths 320, 375, 390 and 430 logical pixels and landscape
844 pixels, preserving readable labels, all tabs, prescription, progress/accumulators,
confirmation and STOP. No horizontal overflow on the main phone view; touch
controls at least 44 by 44 logical pixels. Scroll vertically where necessary.
Resizing cancels an outstanding confirmation rather than moving an armed control.
Detailed hydraulics remains in its own tab with explicit horizontal scroll if the
full engineering diagram cannot fit readably. Browser canvas and pointer coordinates
use the same logical dimensions. Test synthetic LVGL geometry/hit testing and a
real browser at phone dimensions; actual iPhone/Safari hardware remains unqualified.

WEB-REQ-008: arterial blood paths, pump and chamber indicators are red (#d73545);
venous paths and chamber indicators blue (#246bce), including stopped paths with
no animated flow. Dialysate quality uses light green (#9cdb91) only when all three
requested measurements are valid, fresh and inside their configured inclusive
limits; any known out-of-range value is orange (#e98525). Missing/stale/invalid
data is neutral gray with explicit text. Color supplements labels/direction; it
never changes delivery, protection or physical equations. Spent dialysate/drain
is identified separately and must not be portrayed as verified fresh fluid.

Current contract limitation: OBS12 has temperature and conductivity but no pH,
CO2 measurement or approved pH range. Do not derive or invent pH from bicarbonate.
Use the existing simulator limits (35–39 degrees C, 12–16 mS/cm) for the two known
measurements. Report pH unavailable and overall quality incomplete; green cannot
be reached by this live contract. Test the three-measurement color reducer using
explicit synthetic pH limits only, without adding a clinical threshold or a model.
Acceptance covers boundary values, one bad value among missing data, NaN, stale
data, zero-flow identity and arterial/venous transition at the filter. Independent
usability/color acceptance, a pH model/measurement contract and its limits remain
open decisions. Numerical closure and clinical validation remain outside scope.

Mobile input detail (before implementation): a sticky browser toolbar mirrors the
currently eligible phase action and STOP through the existing LVGL App::click
path. Numeric HTML inputs support the phone keyboard and copy only enabled fields
into existing LVGL textareas before opening the unchanged prescription review.
No direct model mutation or confirmation bypass is permitted. A newly opened
confirmation is scrolled into view; resize cancels it. Touch wrappers do not
replace the production LVGL screen or simulation.
