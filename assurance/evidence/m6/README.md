# M6 device UI verification

Technical M6 software scope is complete at `2ee31adc06f3a68ff5844a67a133632cae35d8e7`.
M7–M9 remain required. All results below identify a clean build, exact source,
configuration, dependencies, commands and retained artifacts. This is simulated
software verification, not clinical usability, calibrated physiology, standards
conformity, alarm audibility, human approval or hardware independence.

## Actual results

- 114/114 native and 114/114 ASan/UBSan regression tests pass.
- 10/10 real UI/demo tests pass in headless, WSLg/X11 and sanitizer builds;
  LVGL and SDL are also instrumented in the latter.
- Real widget-driven Compose runs pass in headless and graphical deployments.
  Each records 400 ticks, applies the selected prescription/START/STOP, and retains
  complete trajectories, manifests, widget input/output logs and actual captures.
- Twelve native/twelve Compose HD/pre/post, air/invalid-sensor/recovery runs have
  exact cross-build replay hashes. Maximum independent water error is
  1.283e-11 mL and species error 1.570e-11 mmol, within unchanged 1e-6 tolerances.
- Four M1 Compose runs and three actual isolation probes pass. The running UI
  container also cannot connect to admin/patient/raw plant endpoints; device
  endpoints reject HALT. Device sockets are mounted read-only, with no network,
  dropped capabilities, no-new-privileges and the 128 MiB memory limit.
- Measured UI VmHWM: 9,547,776 bytes headless (9.11 MiB), 20,500,480 bytes X11
  (19.55 MiB); no OOM. These are process/container observations for the recorded
  workflows, not a new 100000-tick graphical endurance claim. Cgroup peaks and
  exact process status are retained separately in the Compose reports.

`summary.json` binds artifact hashes; `native-tests.json`, `sanitizer-tests.json`,
`ui-*.json`, `native-models.json`, `compose-models.json` and `m1-compose.json`
contain actual detailed results. `ui-compose/` and `ui-compose-x11/` retain full
widget-driven records. Eight individually registered `captures/*.png` files come
from actual LVGL rendering with the original project font, including maximum
alarms, stale reconnection and the exact fractional-prescription confirmation.
Complete local diagnostics remain under `build/m6-final-*`.

## Exact verification commands

The inspected host is WSL2 Linux x86_64, GCC 13.3.0, CMake 3.28.3 and CPython
3.12.3. Docker uses the pinned CPython 3.12.14/Debian image, GCC 14.2.0 and CMake
3.31.6. Application pins: LVGL 9.6.0 and SDL2 2.32.10; see
`gui_dependencies.json`, `docs/dependencies/M6.md` and the platform inventory here.

```bash
python3 tools/fetch_gui.py
cmake -S . -B build/gui -DCMAKE_BUILD_TYPE=Release -DDIALYSISLAB_GUI=ON \
  -DDIALYSISLAB_XEXT_PREFIX="$PWD/build/dependency-inspection/xext-platform/usr" \
  -DXEXT_LIB=/lib/x86_64-linux-gnu/libXext.so.6
cmake --build build/gui --parallel 3
python3 tools/verify_m1.py --build-dir build/gui --output build/m6-final-native-tests.json
python3 tools/verify_device_ui.py --build-dir build/gui --output build/m6-final-ui-headless
DISPLAY=:0 SDL_VIDEODRIVER=x11 python3 tools/verify_device_ui.py --build-dir build/gui --graphical --output build/m6-final-ui-wslg
cmake -S . -B build/gui-sanitize -DCMAKE_BUILD_TYPE=Debug -DDIALYSISLAB_GUI=ON -DDIALYSISLAB_SANITIZE=ON \
  -DDIALYSISLAB_XEXT_PREFIX="$PWD/build/dependency-inspection/xext-platform/usr" \
  -DXEXT_LIB=/lib/x86_64-linux-gnu/libXext.so.6
cmake --build build/gui-sanitize --parallel 3
python3 tools/verify_m1.py --build-dir build/gui-sanitize --output build/m6-final-sanitizer-tests.json
python3 tools/verify_device_ui.py --build-dir build/gui-sanitize --output build/m6-final-ui-sanitizer
SOURCE_REVISION=$(git rev-parse HEAD) docker compose --profile device-ui build
python3 tools/verify_ui_compose.py --output build/m6-final-ui-compose
python3 tools/verify_ui_compose.py --graphical --output build/m6-final-ui-compose-x11
python3 tools/verify_models.py --build-dir build/gui --scenarios machine_hd machine_hdf_pre machine_hdf_post machine_air machine_invalid machine_recovery --output build/m6-final-native-models
python3 tools/verify_models.py --build-dir build/gui --compose --scenarios machine_hd machine_hdf_pre machine_hdf_post machine_air machine_invalid machine_recovery --output build/m6-final-compose-models
python3 tools/verify_compose.py --output build/m6-final-m1-compose
```

Choose new output paths when repeating. The Xext prefix is the locally extracted,
authenticated development package used on this host; normal native development
packages or the pinned Docker build are alternatives. Final reconfiguration reused
these existing CMake cache values. No global display access, credentials,
certificates or security controls were changed to obtain these results.

## Review and corrections

Exactly one review: base `445c667`, candidate `00baa58`, 01:58:14–02:09:25 UTC,
exit zero **with six P2 findings**, all fixed in `5552622`. `review.json` preserves
command, base/candidate, final output, transcript hash, findings and tests.
Corrections cover same-session sample age, queued SDL transitions, exact decimal
confirmation, alarm layout, unexpected demo failure exit and cancellable paced
waits. Final visual inspection found M6-V1 (dark dialog text); `2ee31ad` fixes it
and checks >=7:1 luminance contrast in the rendered detail region. That display
criterion is not accessibility or clinical conformity. No second review ran.
Earlier candidate/failing diagnostic results and the unpublished `5552622` evidence
draft remain in `build/`; their dark-dialog capture is not final visual evidence.

## Limits and remaining obligations

Interactive device actions add external input; an initial scenario alone does not
replay those interventions. M7 must provide an explicit experiment event schedule
and distinguish replayable from externally interrupted/interactive runs. Trends
retain 120 received valid samples, not the complete trajectory. UI session IDs
supply freshness, not authentication. Same-user native trust, shared device-volume
producer ownership, X11 host interaction and availability/common-cause analysis
remain M8 concerns. Graphical verification succeeded here; other Linux displays,
physical touch hardware, audibility and representative users were not validated.

All 184 standards items, 12 edition gaps and nine release prerequisites remain
open. Normal assurance/publication checks pass; release gates remain blocked.
