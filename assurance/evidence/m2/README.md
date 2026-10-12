# M2 verification evidence

Implementation `2108e55`, clean source build; native GCC 13.3.0 / Python 3.12.3,
Docker GCC 14.2.0 / Python 3.12.14, linux/amd64 on WSL2. Exact source/binary hashes,
configurations, commands and individual case results are in the JSON reports.

## Actual results

- Native and ASan/UBSan suites: **58/58 passed each**, including all M1 regressions.
- Six native and six Compose M2 runs: passed; small/large/occluded circuits each
  repeated twice. Native/container trajectory bytes match exactly.
- Four M1 Compose runs and two real mount-isolation probes: passed.
- Hydraulic residual and cumulative patient/circuit/effluent balance meet the
  predeclared tolerances. Occlusion at 2000 ms latches by 2900 ms (deadline 3000).
- One review of candidate `9aeee60` against `1999741`: three P2 findings, all fixed
  in `2108e55` and regression tested. No second review was run. `review.json`
  contains exact invocation, output and dispositions; the full local transcript
  remains at `build/reviews/m2-output.txt`, with its SHA-256 recorded.

`summary.json` identifies/hash-links the reports. One complete 200-record Compose
trajectory per fixture is retained here; other repeats and logs remain in the
corresponding `build/m2-final-*` directories. Original M1 evidence remains intact.

## Commands executed

```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --parallel 3
python3 tools/verify_m1.py --build-dir build --output build/m2-final-native-tests.json
python3 tools/verify_models.py --output build/m2-final-native
cmake -S . -B build/sanitize -DCMAKE_BUILD_TYPE=Debug -DDIALYSISLAB_SANITIZE=ON
cmake --build build/sanitize --parallel 3
python3 tools/verify_m1.py --build-dir build/sanitize --output build/m2-final-sanitizer-tests.json
docker compose build --build-arg SOURCE_REVISION=2108e55
python3 tools/verify_models.py --compose --output build/m2-final-compose
python3 tools/verify_compose.py --output build/m2-final-m1-compose
```

The build used the full SHA of `2108e55` (see manifests). Use fresh output paths
for new runs. Trace/standards release checks intentionally remain blocked; no
gate or threshold was removed to obtain these software results. M2 has no clinical
validation or calibration; prescribed concentration boundaries are not yet a
dynamic patient solute model. Remaining work proceeds in M3–M9.
