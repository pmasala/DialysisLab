# M5 verification evidence

Implementation `443f73f`, clean build; WSL2 Linux x86_64, GCC 13.3.0/Python 3.12.3
native and GCC 14.2.0/Python 3.12.14 in the pinned Compose image. Reports identify
source/configuration/binary hashes, commands and actual outcomes.

## Actual results

- 108/108 native and 108/108 ASan/UBSan tests passed.
- 22 native and 22 Compose workflow/fault runs passed with identical trajectory
  bytes across builds: HD, pre/post HDF, air/leak/stall/pressure/invalid/quality/
  metering faults and guarded recovery.
- Twelve M2–M4 Compose compatibility runs, four M1 runs and three real isolation
  probes passed. Device-only mounts reach device services but cannot connect to
  admin, patient or either plant decision endpoint.
- Two native and two Compose 100000-tick priming runs passed. Each flushes
  333320.0666667 mL from external source while body volume remains
  exactly 100000 mL. All four trajectory hashes are
  `57fefc9faa80ce87965c1b023e4d483bc8084e0c3b3808be10e7b8c791554030`.
- Maximum independent water residual: 4.366e-11 mL;
  species residual: 9.965e-10 mmol. Both are below the
  predeclared 1e-6 bounds. Native HALT acknowledgment and observed zero outputs
  were also confirmed after both long runs.

## Review and failures retained

The single review compares candidate `a490984` with base `e1c8ae2`. Its two P2
findings are fixed in `c54422c`: isolated body-volume cancellation and missing
alarm-mask/actuator evidence checks. `review.json` contains exact command,
findings, output, dispositions and full local transcript hash. No second review.

The first real long native/Compose attempts then exposed M5-V1: a finite subnormal
concentration was rejected at tick 4662. Decimal parsing is fixed in `443f73f`,
with an actual transport regression and all four full long runs passing.
`failed-attempts.json` retains failed manifests, trajectory scans and Compose
collection status. Full partial files remain in `build/m5-final-long-native/`
and `build/m5-final-long-compose/`; Compose collected them before removing volumes
and preserved its nonzero result. Preliminary `m5-candidate-*`/`m5-final-*` tests
are diagnostic history, not the final clean-build evidence above.

## Memory and model limits

Long-run Compose runner RSS peaks at 23277568 bytes
(22.20 MiB), below the unchanged 64 MiB
RSS criterion in a 128 MiB container: 105.80 MiB RSS headroom, no OOM.
Cgroup peak including reclaimable file cache reaches 128 MiB; RSS headroom is
not reserved total-cgroup headroom. Native `/proc/PID/status` sampling peaks at
20758528 bytes (19.80 MiB); sample every second in
`native-memory.jsonl`. The verifier runs as a child of its sampling wrapper, so
both share a process namespace; a separate exec could not locate that PID.
Process-lifetime `ru_maxrss` and host cgroup readings remain separately retained.
No retrospective correction of M4's launch-dependent memory reading is claimed.

Thresholds/detectors are synthetic. Priming/cleaning readiness is a flushed-volume
criterion, not validated air removal/disinfection. No pump/filter functional reset
is modeled: those latches require a new run; retained unsafe pressure cannot be
reset by erasing physics. Stuck sensors, common host/plant/protocol causes,
calibration, clinical/quality validation and independent risk acceptance remain
limits/gaps. Floating decimal parsing is verified with the recorded GCC 13/14
standard libraries; older C++ libraries lacking that C++17 facility are unverified.

## Commands executed

```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --parallel 3
python3 tools/verify_m1.py --build-dir build --output build/m5-verified-native-tests.json
cmake -S . -B build/sanitize -DCMAKE_BUILD_TYPE=Debug -DDIALYSISLAB_SANITIZE=ON
cmake --build build/sanitize --parallel 3
python3 tools/verify_m1.py --build-dir build/sanitize --output build/m5-verified-sanitizer-tests.json
python3 tools/verify_models.py --scenarios machine_hd machine_hdf_pre machine_hdf_post machine_air machine_leak machine_stall machine_balance machine_quality machine_pressure machine_invalid machine_recovery --output build/m5-verified-native
SOURCE_REVISION=$(git rev-parse HEAD) docker compose build
python3 tools/verify_models.py --compose --scenarios machine_hd machine_hdf_pre machine_hdf_post machine_air machine_leak machine_stall machine_balance machine_quality machine_pressure machine_invalid machine_recovery --output build/m5-verified-compose
python3 tools/verify_models.py --compose --scenarios circuit_occlusion patient_imbalance treatment_hd treatment_hdf_pre treatment_hdf_post treatment_integrity --output build/m5-verified-compat-compose
python3 tools/verify_compose.py --output build/m5-verified-m1-compose
python3 tools/verify_models.py --scenarios machine_priming_100000 --output build/m5-verified-long-native
python3 tools/verify_models.py --compose --scenarios machine_priming_100000 --output build/m5-verified-long-compose
```

Use new output paths. The native long command was launched by a Python parent that
sampled the child's `/proc` VmRSS/VmHWM once per second; this does not alter the
simulation inputs. Four complete short trajectories are committed. Other complete
trajectories/logs, including long files, remain at the reported ignored build paths.
M6–M9 remain required; this evidence does not complete the reference project or
its independent/regulatory release gates.
