# M4 verification evidence

Implementation `cca9ce6`, clean build; WSL2 Linux, native GCC 13.3.0/Python 3.12.3,
Docker GCC 14.2.0/Python 3.12.14. Exact configurations, hashes, dependencies and
commands are retained in reports and manifests.

## Actual results

- 87/87 native and 87/87 ASan/UBSan tests passed.
- 24 native/24 Compose runs cover HD, pre/post HDF, two dialyzers/patient imbalance,
  six observed quality faults and deliberately unobserved contamination. All
  native/container trajectory bytes match.
- Fourteen M2/M3 Compose regressions, four M1 Compose runs and two isolation probes passed.
- Two native and two Compose 100000-tick runs completed, each with gross UF
  166665 mL and positive remaining body water. All four hashes are
  `53263cf9909693eaf4427dd857f1c44ba51a503210b3af569c1f9a5d0efaffc6`.
  Native HALT acknowledgment and observed zero blood/UF/replacement are confirmed
  after the large cumulative UF; no discarded/reset cumulative counter is used.
- Maximum independent water error 3.654e-7 mL; solute error 4.065e-8 mmol.
  Both satisfy the predeclared 1e-6 tolerances without changing the gates.
- One review of `9a2d2df` against `47ffc5e` returned one P1 and five P2 findings.
  All fixed in `cca9ce6`, including live quality isolation **before COMMIT**.
  `review.json` contains command/output/dispositions and the full local transcript
  hash. No second review was run.

## Memory interpretation

Long-run Docker runner peak RSS is 23388160 bytes (22.31 MiB), below the unchanged
64 MiB RSS acceptance criterion within the 128 MiB container limit: 105.69 MiB
RSS headroom. There are no OOM kills. The cgroup peak **including reclaimable file
cache** reaches 128 MiB; RSS headroom is not reserved cgroup headroom. Each long
trajectory is about 378 MB on disk and is streamed, not retained in Python memory.

Native `ru_maxrss` reports a 463904768-byte process-lifetime high-water value,
while separately sampled Linux `/proc/PID/status` VmHWM/RSS is approximately
19–20 MiB. These distinct observations are retained, not rewritten or used as
proof of a native 128 MiB limit. Host cgroup memory includes unrelated processes.
Container-local measurements and inspected memory limits/OOM flags establish the
Compose criterion. `native-memory-samples.jsonl` and the launch diagnostic retain
the native measurement discrepancy for later investigation.

## Commands executed

```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --parallel 3
python3 tools/verify_m1.py --build-dir build --output build/m4-final-native-tests.json
cmake -S . -B build/sanitize -DCMAKE_BUILD_TYPE=Debug -DDIALYSISLAB_SANITIZE=ON
cmake --build build/sanitize --parallel 3
python3 tools/verify_m1.py --build-dir build/sanitize --output build/m4-final-sanitizer-tests.json
python3 tools/verify_models.py --scenarios treatment_hd treatment_hdf_pre treatment_hdf_post treatment_temperature treatment_ratio treatment_supply treatment_integrity treatment_route treatment_filter1 treatment_contaminant treatment_hdf_large treatment_hdf_imbalance --output build/m4-final-native
SOURCE_REVISION=$(git rev-parse HEAD) docker compose build
python3 tools/verify_models.py --compose --scenarios treatment_hd treatment_hdf_pre treatment_hdf_post treatment_temperature treatment_ratio treatment_supply treatment_integrity treatment_route treatment_filter1 treatment_contaminant treatment_hdf_large treatment_hdf_imbalance --output build/m4-final-compose
python3 tools/verify_models.py --compose --scenarios circuit_small circuit_large circuit_occlusion patient_baseline patient_overload patient_imbalance patient_large --output build/m4-final-compat-compose
python3 tools/verify_compose.py --output build/m4-final-m1-compose
python3 tools/verify_models.py --scenarios treatment_100000 --output build/m4-final-long-native
python3 tools/verify_models.py --compose --scenarios treatment_100000 --output build/m4-final-long-compose
```

Use fresh output directories. One complete 300-record trajectory for each mode
and the integrity fault is committed. Other complete trajectories/logs, including
all four long runs, remain in the indicated ignored `build/` directories; reports
record their exact hashes/counts/first/last records. No synthetic quality or
physiology result is clinical validation. Standards, independent risk acceptance
and the remaining M5–M9 work are not completed by these tests.
