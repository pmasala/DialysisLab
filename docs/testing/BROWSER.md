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

## Manual preparation wait regression (WEB-REQ-006)

The 2026-10-16 automatic cycle checks did not cover an operator waiting in
PREPARATION. The deployed prototype was reproduced failing at tick 2,200 with
`RuntimeError: configured tick limit reached`, while the manual clock kept running.
This was a batch-horizon/session-lifetime error, not evidence of physical model
instability or a clinical finding. The user's exact error was not supplied.

The worker now requests an explicit interactive execution profile. Only this
profile omits the batch horizon. Export includes `execution_profile`; `config.ticks`
remains the batch scenario horizon. Physical simulated time and finite supplies
continue to advance. Use **Ferma tempo** to pause while examining the UI; restarting
the clock does not replay wall time. **Nuova simulazione** resets both models.

Reproduce the delayed-command comparison on a fresh build:

```sh
python3 -m unittest discover -s tests -p test_browser.py -v
python3 tools/verify_browser.py --manual-delay-ticks 2400 --output build/manual-wait-new
```

For scripting-only changes with an intact prior static build and its Git history,
`python3 tools/build_browser.py --reuse-compiled /path/to/prior-build --offline`
verifies compiled input sets, source/CMake hashes, dependency locks and prior
artifact hashes before reuse. It records reuse provenance; it does not claim a
new C++ compilation. Full `--emsdk` builds remain supported.

Actual browser reproduction: uncheck **Ciclo automatico**, choose **100×**, start
the clock, let PREPARATION pass 2,400 ticks, select **Start priming**, review and
confirm, and observe PRIMING and then CONFIGURATION without a runtime error.
A numerical comparison cannot substitute for this UI interaction check.
Historical acceptance reports above retain their original scope and input hashes;
they do not certify this corrected session behavior.

The [delayed-start comparison](../../assurance/evidence/browser/manual-wait-final.json)
passed 8,172 paired intervals (2,724 per mode), including all three complete cycles,
with 4,698,900 numeric comparisons. Maximum budget usage was 0.00018694.
The [bounded-session rerun](../../assurance/evidence/browser/bounded-session-portability.json)
also passed its original 3,383 intervals.
[Regression execution](../../assurance/evidence/browser/manual-wait-acceptance.json)
records four passing native tests and two opt-in tests skipped; the separate
Wasm campaigns above were executed directly. Live UI status is recorded there.

The initial corrected deployment exposed a cache issue: after normal reload the
browser still displayed the old identity. The wrapper now shares an asset-version
query among app, worker, Python bundle, scenario and identity requests. The
[initial delayed-start report](../../assurance/evidence/browser/manual-wait-portability.json)
remains as pre-cache-fix evidence; the final comparison above binds the shipped
wrapper. Compiled code and Python physics are unchanged between these candidates.

Hosted verification passed on Pages commit `fc70847271e6ddfa6900c7662fc1b6b2c076f0a2`
(build input `4f5424c19ad412d9…`): in manual HD, PREPARATION remained healthy beyond
5,200 ticks; the actual Start priming / Confirm controls entered PRIMING with zero
alarms. Automatic continuation then reached CLEANED at tick 5,634. The retained
[export](../../assurance/evidence/browser/manual-wait-export.json) identifies the
interactive profile. PRE/POST delayed full cycles are covered by the paired model
campaign, not an additional hosted manual UI claim. Pointer timing and a cosmetic
terminal clock-status label remain recorded limitations in the acceptance record.

## Mobile reflow and fluid identity (WEB-REQ-007/008)

At widths below 700 logical pixels, the existing LVGL view reflows into a vertical
filter view, two-column metric cards, stacked accumulators and large actions.
The page scrolls vertically; Hydraulics retains its readable engineering diagram
inside a separate horizontally scrollable panel. A sticky phone toolbar mirrors
the eligible phase action and STOP through App::click. Phone prescription inputs
use the OS keyboard (decimal comma is normalized) and open the same LVGL review
and confirmation. A resize cancels a pending request. The mobile-preview.html
page embeds the actual application at selectable viewport widths; it does not
emulate iOS. Actual iPhone Safari performance and keyboard/touch qualification
remain pending.

Arterial paths/components are red, venous blue. The stopped paths retain identity
without animation. Fresh dialysate quality is orange when a known temperature or
conductivity measurement is outside the existing model limits. Gray means stale,
invalid or incomplete quality. The live OBS12 contract has no pH; this is shown
explicitly, so green is not claimed by the current live model. A pure reducer tests
light green only when all three readings and their explicit limits are present
and satisfied. Its synthetic pH fixture is not a proposed clinical pH threshold.
Spent drain fluid is distinguished from qualified fresh fluid.

Reproduce with the pinned full native GUI and browser builds, then:

```sh
DIALYSISLAB_MOBILE_CAPTURES="$PWD/build/mobile-captures-new" python3 -m unittest discover -s tests -p test_mobile.py -v
python3 tools/verify_synoptic.py --output build/mobile-synoptic-new.json
python3 tools/verify_preparation.py --output build/mobile-preparation-new.json
python3 tools/verify_browser.py --manual-delay-ticks 2400 --output build/mobile-portability-new
```

The SDK download URL in the lock was corrected to the official emsdk manifest
layout; its version and archive SHA256 are unchanged. No new shipped dependency
was added. Execution results and viewport interaction are recorded in
[mobile acceptance](../../assurance/evidence/browser/mobile-acceptance.json).

Executed on 2026-10-17: 3 mobile/color/SDL tests, 13 synoptic regressions and
18 preparation regressions passed without skips. The delayed 2400-tick native/Wasm
HD/PRE/POST campaign passed 4,698,900 numeric comparisons; this is portability
evidence, not CLOSE-NUM-01 closure. Hosted Pages commit
`9c4c9f03ccca3c1ca3d1f959d970ee78ca450a5e` (build input
`113e22a79d22453d…`) passed the manual HD flow through priming and treatment,
phone prescription edits and confirmation cancellation on resize. The initial
viewport trial found legacy SDL window bounds shifting pointer coordinates; the
bounds were corrected and a real SDL resize regression added before retesting.
At least 320 logical content pixels are required: a desktop 320 px iframe with
a classic scrollbar provides less usable width and can clip the edge. This is
recorded separately from native 320 px layout and hosted 390 px interaction.
