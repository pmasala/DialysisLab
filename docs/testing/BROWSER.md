# Complete browser runtime verification

Engineering review candidate, 2026-10-16. See [design and prospective criteria](../design/BROWSER_RUNTIME.md).
This target executes the existing C++ plant and role handlers, Python patient,
distributed transport and preparation model locally. It does not use a server
simulation, replay or JavaScript replacement equations.

## Reproduce

Install Emscripten 4.0.15 using the official emsdk. Use the pinned existing GUI
sources (`python3 tools/fetch_gui.py --cache build/gui-deps`). Then:

```sh
python3 tools/build_browser.py --emsdk /path/to/emsdk
python3 -m http.server 8000 --directory build/browser
```

Open `http://localhost:8000`. The HTTP process only serves static files; it performs
no simulation computation. Opening index.html directly as a file is not supported
because browsers restrict worker/module/Wasm loading from file URLs.

Choose HD, HDF PRE or HDF POST and **Nuova simulazione**. **Avvia tempo** advances
virtual time; **Ciclo automatico** exercises the complete lifecycle. Otherwise use
the actual LVGL buttons and confirmation dialogs. The supplied synthetic scenario
uses 60 seconds of treatment; its preparation and priming phases still execute.
Speed is a pacing request, not a real-time guarantee. At 1x, each 500 ms tick is
scheduled at least 500 wall ms apart; calculation cost can slow the simulation.
The 20x/100x modes batch ticks without deriving any physical dt from render timing.
Closing/reloading the page discards the session. **Esporta stato** downloads the
configuration and final coupled record; it is not a full trajectory archive.

For full portability and browser acceptance, build the native GUI and use:

```sh
DIALYSISLAB_BROWSER_ACCEPTANCE="$PWD/build/browser-acceptance-new" \
DIALYSISLAB_CHROMIUM=/path/to/chrome-headless-shell \
python3 -m unittest discover -s tests -p test_browser.py -v
python3 tools/verify_synoptic.py --output build/browser-synoptic-new.json
python3 tools/verify_preparation.py --output build/browser-preparation-new.json
```

The explicit browser acceptance requires Node.js, Playwright and Chromium. Without
that environment, two browser-specific unittest methods are **skipped**, never
counted as browser passes. The two native transport contracts still execute.
The selected local Chromium was 155.0.8059.84; Playwright was 1.62.1. Those are
verification tools, not shipped application dependencies.

## Scope and proposed criteria

The portability campaign executes all 3,383 committed intervals of HD, HDF PRE and
HDF POST through their complete cycles in CPython/native and Pyodide/Wasm. It
compares discrete outputs exactly and every floating field against the budget
specified before execution. It checks patient and preparation solute balances and
preparation water conservation against the existing 1e-6 bounds. Native and Wasm
records are retained by the reproduction command; report hashes bind both streams.
The comparison reuses identical scheduler code, so it establishes platform
portability, not an independent oracle for every scheduler equation. Existing
model/preparation tests remain separate evidence.

Chromium checks real canvas touch navigation, 1x timing, keyboard prescription
editing with review/confirmation, pause/resume, STOP, session reset, the complete
POST cycle, a narrow viewport and export of the distributed patient. A synthetic
hidden-document event verifies the pause handler and explicit resume rule; actual
OS suspension, background throttling and Safari/mobile hardware remain unqualified.
All observed requests must be same-origin static assets. Error paths stop execution
and require reset; invalid sequence and old-session command rejection are tested.

The unchanged physical equations are not sufficient to claim preservation of
native process isolation. Control/protection handlers are now shared with native
executables, with the same handler bodies and an injected transport. The browser
worker is a common fault domain and has no independent real-time watchdog.

## Remaining decisions

- Approve the Pyodide MPL-2.0 / CPython license exception under the dependency policy;
  complete the generated runtime/transitive-notice inventory before public release.
- Cross-browser/device performance, actual background suspension and long treatments.
- Independent usability review and wider native integration CI on the published head.
- CLOSE-NUM-01 remains open; portability is distinct from global numerical accuracy,
  experimental validation and clinical validation.

See [dependency review](../dependencies/BROWSER_DEPENDENCIES.md). The candidate can
be hosted on a static server such as GitHub Pages after release decisions; no
Codespaces or remote computation backend is needed. No public deployment is implied
by a successful local build or this document.

## Recorded execution

The final [portability report](../../assurance/evidence/browser/portability-final.json)
records 1,945,225 numeric comparisons across HD 1,087, PRE 1,148 and POST 1,148
intervals. The largest error consumed 0.00004367 of the proposed mixed absolute/
relative budget. Stages and alarm flags matched exactly. The [Chromium report](../../assurance/evidence/browser/ui-final.json)
records the real UI checks; [execution log](../../assurance/evidence/browser/acceptance.json)
records four passing browser/transport unittest procedures with no skips.
The [13 UI/guided/protocol regressions](../../assurance/evidence/browser/synoptic-contract-reviewed.json)
and [18 preparation regressions](../../assurance/evidence/browser/preparation-final.json)
also passed with no skips. Earlier reports remain history.

[Development findings](../../assurance/evidence/browser/development.json) preserve
installation failures, resolved pacing/reset-message defects and the native Unix
service startup block. The real-process guided test was attempted but failed to
start local services; no native IPC integration pass is claimed. Hosted CI must
assess that integration on the published revision.
