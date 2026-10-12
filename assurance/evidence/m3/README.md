# M3 verification evidence

Implementation `64645fd`, clean build, WSL2 Linux. Native GCC 13.3.0/Python
3.12.3; pinned Docker GCC 14.2.0/Python 3.12.14. Reports identify exact source,
binary, configuration and trajectory hashes, commands and individual results.

72/72 native and 72/72 ASan/UBSan tests passed. Eight native/eight Docker patient
runs reproduce exactly across builds; six M2 and four M1 Docker regressions plus
two mount-isolation probes passed. Summary records maximum independent water and
solute residuals (acceptance 1e-6 mL/mmol) and fresh-process 100000-step RSS (<64 MiB).
This patient-only memory probe does not replace full-system long-run deployment.

One review of `ec832d0` against `40533e4` returned four P2 and one P3 findings;
all corrected by `64645fd` with targeted regressions. No second review occurred.
Review metadata/output/dispositions are in `review.json`; full local transcript
is `build/reviews/m3-output.txt`, hash recorded. Each fixture retains one complete
500-record Compose trajectory; remaining repeats/logs are in `build/m3-final-*`.

## Executed commands

```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --parallel 3
python3 tools/verify_m1.py --build-dir build --output build/m3-final-native-tests.json
cmake -S . -B build/sanitize -DCMAKE_BUILD_TYPE=Debug -DDIALYSISLAB_SANITIZE=ON
cmake --build build/sanitize --parallel 3
python3 tools/verify_m1.py --build-dir build/sanitize --output build/m3-final-sanitizer-tests.json
python3 tools/verify_models.py --scenarios patient_baseline patient_overload patient_imbalance patient_large --output build/m3-final-native
SOURCE_REVISION=$(git rev-parse HEAD) docker compose build
python3 tools/verify_models.py --compose --scenarios patient_baseline patient_overload patient_imbalance patient_large --output build/m3-final-compose
python3 tools/verify_models.py --compose --output build/m3-final-m2-compose
python3 tools/verify_compose.py --output build/m3-final-m1-compose
python3 tests/patient_memory_probe.py > build/m3-final-memory.json
```

Fresh output paths are required. Pure synthetic software/numerical evidence;
no calibration, clinical validation, independent approval or standards conformity.
The fixed-pCO2 indicator omits dynamic respiration/buffers; M4–M9 remain required.
