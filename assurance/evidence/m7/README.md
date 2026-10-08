# M7 verified experiment console

Technical M7 COMPLETE on implementation `bbecf598154f0dc00b787ed839141d96a704ce0d`.
This is synthetic software/numerical/process/UI verification, not calibration,
clinical validation, human risk acceptance, hardware independence or conformity.
M8/M9 and all existing release gates remain required.

## Actual results

- Native and ASan/UBSan suites: **134/134 each**, including 20 broker/service tests.
- Actual ImGui widgets: **5/5 each** headless, WSLg and instrumented; ten LVGL/device
  regressions pass. Inputs, outputs and captures come from the real services.
- Ten native/ten Compose model runs reproduce identical trajectories. Independent
  water/species residuals stay below the unchanged **1e-6 mL/mmol** criterion;
  exact maxima are in [summary.json](summary.json).
- Separate-container console deployments pass both headless and X11: an original
  run, exact fresh-service replay and an aborted run with partial trajectory and
  observed HALT in each deployment. Four M1 runs and three isolation probes pass.
- Console RSS peaks: **16.55 MiB headless**, **18.97 MiB X11**; limit **128 MiB**,
  no OOM. Cgroup peaks are recorded separately (page cache is not reserved headroom).
  These are the recorded 400-tick workflows, not a new long graphical endurance claim.

The sole read-only review covered candidate `1cf008c` against fixed base `2621181`.
It returned one P1 and ten P2 findings; all are fixed and regression-linked in
[review.json](review.json). M7-V1 additionally removes unauthenticated header metadata.
Full original transcript remains at `build/reviews/m7-output.txt`, with retained hash.
No second review was invoked; the CLI's zero exit did not mean an empty report.

## Exact final commands

Executed on WSL2 Linux x86_64, GCC 13.3.0/Python 3.12.3 native and pinned
GCC 14.2.0/Python 3.12.14 Docker. GUI dependencies/selected notices are in
`gui_dependencies.json` and `docs/dependencies/M6.md`, `M7.md`, `GUI_NOTICES.md`.
The platform Xext prefix was already locally extracted; no global installation,
credential, TLS or display-access setting was changed. Use fresh output paths.

```bash
cmake -S . -B build/gui -DCMAKE_BUILD_TYPE=Release -DDIALYSISLAB_GUI=ON -DDIALYSISLAB_XEXT_PREFIX="$PWD/build/dependency-inspection/xext-platform/usr" -DXEXT_LIB=/lib/x86_64-linux-gnu/libXext.so.6
cmake --build build/gui --parallel 3
python3 tools/verify_m1.py --build-dir build/gui --output build/m7-final-native-tests.json
cmake -S . -B build/gui-sanitize -DCMAKE_BUILD_TYPE=Debug -DDIALYSISLAB_GUI=ON -DDIALYSISLAB_SANITIZE=ON -DDIALYSISLAB_XEXT_PREFIX="$PWD/build/dependency-inspection/xext-platform/usr" -DXEXT_LIB=/lib/x86_64-linux-gnu/libXext.so.6
cmake --build build/gui-sanitize --parallel 3
python3 tools/verify_m1.py --build-dir build/gui-sanitize --output build/m7-final-sanitizer-tests.json
python3 tools/verify_console.py --build-dir build/gui --output build/m7-final-console-headless
DISPLAY=:0 SDL_VIDEODRIVER=x11 python3 tools/verify_console.py --build-dir build/gui --graphical --output build/m7-final-console-wslg
python3 tools/verify_console.py --build-dir build/gui-sanitize --output build/m7-final-console-sanitizer
python3 tools/verify_device_ui.py --build-dir build/gui --output build/m7-final-device-ui
SOURCE_REVISION=$(git rev-parse HEAD) docker compose --profile device-ui build
python3 tools/verify_experiments_compose.py --output build/m7-final-console-compose
python3 tools/verify_experiments_compose.py --graphical --output build/m7-final-console-compose-x11
python3 tools/verify_models.py --build-dir build/gui --scenarios machine_hd machine_hdf_pre machine_hdf_post machine_air machine_recovery --output build/m7-final-native-models
python3 tools/verify_models.py --build-dir build/gui --compose --scenarios machine_hd machine_hdf_pre machine_hdf_post machine_air machine_recovery --output build/m7-final-compose-models
python3 tools/verify_compose.py --output build/m7-final-m1-compose
```

Reports include commands, source/binary hashes, actual configuration and per-test
results. Complete console Compose configuration/metadata/journal/manifest/JSONL
and widget input/output logs are retained here; other raw execution artifacts and
original build logs remain in `build/m7-final-*`. Registered PNGs are actual project
renderings with selected MIT fonts/notices; no licensed standards/private images.
Operational native/Compose/headless commands: [M7 contract](../../../docs/M7_EXPERIMENTS.md).

## Preserved diagnostics and limits

First Compose startup failed before services because an unquoted YAML tmpfs option
was parsed as separate mounts. `build/m7-compose-first/` retains the original failure
and recovery: every available volume was copied and confirmed empty before cleanup.
Early fixtures mismatched initial concentrations or requested configuration before
200 mL prime completed. Corrected inputs/calendar retain the existing guards; all
failed reports remain in `build/m7-*-preliminary*` and `build/m7-targeted-*`.
Pre-review/correction diagnostic output is historical, never substituted for final PASS.

Exact replay applies to immutable scheduled configuration, seed and identified build;
external emergency STOP interrupts the run. Pause affects wall scheduling only.
HALT acknowledgment and actual observation remain separate. Journal gaps, invalid
metadata quarantine and recovered torn prefixes remain explicit; they do not become
successful complete-run evidence. Same-UID native execution is trusted. Native
hard-kill orphan cleanup and shared device-producer ownership are M8 hardening tasks.
All 184 standards entries, 12 edition gaps and nine release prerequisites stay open.
