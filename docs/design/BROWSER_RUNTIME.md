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
