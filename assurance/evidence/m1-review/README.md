# M1 review-correction evidence

Verified implementation: `da5ccc26c5be63c7836f4970ebac5f0335007d9f` on the existing
`feat/m1-headless-hd` branch. The subsequent evidence commit changes no executable
sources. These results supersede the earlier acceptance claims for affected M1
behavior; historical files in `../m1/` remain unchanged.

## Actual results

- 47 native tests passed; the same 47 passed with AddressSanitizer/UBSan enabled.
  This includes all original assurance tests, actual control/protection STEP replies
  discarded after plant acceptance, failed HALT/STATUS, late-command rejection,
  actual runner SIGKILL with prefix recovery, RSS, short writes and collection order.
- Four original Compose scenarios and two access-denial probes passed. Native and
  container JSONL trajectories match exactly; independently configured native
  builds have identical executable hashes.
- Three actual Docker failure regressions passed: aborted runner (original exit 7)
  with five saved records; pre-start failure (exit 1); and failed extraction while
  the runner's original exit 7 remained intact. Logs and available files were
  retained before cleanup. The extraction failure retained its stopped container
  and volume; a subsequent real copy recovered and verified its manifest/trajectory
  before the verifier removed that test project. Pre-start results were independently
  confirmed absent/empty before test-owned cleanup.
- Two full 100000-tick Compose runs completed under the unchanged 128 MiB limit.
  Every record's sequence was checked; count=100000, last sequence=99999 and final
  virtual time=10000000 ms. Exact byte hashes matched each other and independent
  scans. Peak runner RSS was 23597056 bytes (22.50 MiB), below the predeclared 64 MiB
  bound, leaving 105.50 MiB RSS headroom. Peak cgroup use including file cache was
  74592256 bytes (71.14 MiB). Neither runner was OOM-killed.

## Exact commands

Executed from the repository root with CMake 3.28.3, GCC 13.3.0 and Python 3.12.3
for native builds; the pinned image uses GCC 14.2.0 and Python 3.12.14.

```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --parallel 3
cmake -S . -B build/repro -DCMAKE_BUILD_TYPE=Release
cmake --build build/repro --parallel 3
cmake -S . -B build/sanitize -DCMAKE_BUILD_TYPE=Debug -DDIALYSISLAB_SANITIZE=ON
cmake --build build/sanitize --parallel 3
python3 tools/verify_m1.py --build-dir build --output build/review-native.json
python3 tools/verify_m1.py --build-dir build/sanitize --output build/review-sanitizer.json
docker compose build --build-arg SOURCE_REVISION=da5ccc2
python3 tools/verify_compose.py --output build/review-compose
python3 tools/verify_m1_review.py --output build/review-docker
python3 tools/verify_reproducibility.py --first-build build --second-build build/repro --compose-output build/review-compose --output build/review-reproducibility.json
```

All verification commands returned 0. The deliberately failed runs have their
original nonzero codes recorded separately; verifier success means those failures
and recovery policies matched the expected behavior. Output paths must be fresh
when repeating commands. One initial sandbox approval check timed out before
execution; the permitted retry and subsequent real process/Docker checks succeeded.

## Records and limitations

`summary.json` indexes the retained artifacts and hashes. `native-tests.json` and
`sanitizer-tests.json` contain case results, actual output, source/build identity
and configuration. `compose-results.json`, `review-docker.json` and
`reproducibility.json` record image identities, configuration, memory measurements,
byte hashes, original return codes and recovery outcomes. Small nominal/occlusion
streams and aborted streams are retained with manifests; failed-run logs are
retained as `logs.json`. Collection reports describe resources at the moment of
collection, before the verifier's separately recorded recovery and cleanup.

Full long-run streams remain at `build/review-docker/hd_100000-{1,2}/results/run/`;
the source package retains their hashes/counts, configuration, first/last records
and RSS/cgroup measurements, not two large duplicated streams. The regression
source hashes and exact revision also identify derived fault/interruption cases.

HALT acceptance and observed output state are distinct. If both HALT and STATUS
fail, the manifest does not claim zero outputs; the independently acting wall lease
is checked later by the test. Streaming records survive process death through the
OS cache; power-loss durability and per-tick fsync are not claimed. RSS results
apply to the recorded 100000-tick configuration/image, not arbitrary unbounded
configuration payloads. No clinical limits, physiology calibration, hard real-time
or standards conformity is claimed. Full roadmap and independent reviews remain
open; both release gates remain blocked.
