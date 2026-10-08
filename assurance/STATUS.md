# Current status

## Integrated execution checkpoint — 2026-10-08

Branch `feat/integrated-dialysis-roadmap`. **Technical phases M1–M9 COMPLETE**
for the declared synthetic simulator and development template. **Reference
release BLOCKED**: assurance-plan completion levels also require validation and
substantive independent human review that this execution does not supply.

Runtime verification identifies clean build `935692a`; test/integration corrections
`0051ca1` and `4e50564` preserve application sources. 158/158  native and 158/158 sanitizer
tests pass. 72 nominal matrix runs,60 fault runs and four 100000-tick sustained HDF
runs pass across native processes and Docker, with exact replay and independent
water/six-species balances. Ten actual LVGL and six ImGui widget tests pass,
including simultaneous headless/WSLg clients and device STOP during virtual pause.

Runner RSS max 20.76 MiB is below the64 MiB acceptance bound. Total cgroup peak
reaches 128 MiB: **zero peak cgroup headroom**, no OOM. The observed RSS allowance
is not reserved container capacity. No numerical/protective threshold, tick count
or memory limit was relaxed. Failed attempts, including ENOSPC partial outputs,
remain identifiable; no unpersisted shutdown state is claimed as observed.

Exactly one review per phase was consumed; M1 uses the supplied review. All
applicable findings are corrected and regressed, without review-fix-review cycles.
Hosted CI 37747683346 passes and 43 original artifacts recover byte for byte.
Two identical code-source archives build and pass 158 tests plus10 device/6 console
widget tests; separate actual no-Git invocation passes. Final delivery-archive
verification is kept outside Git after the evidence commit, avoiding self-hashes.

| Phase | Technical status and implemented scope | Evidence |
| --- | --- | --- |
| M1 | COMPLETE — separate deterministic processes, direct protection, terminal RPC abort, streamed records/hash, retained failed Compose artifacts and 100000-tick memory. | [M1 corrections](evidence/m1-review/README.md), [later Docker failures/memory](evidence/m8/m1-long-failures.json) |
| M2 | COMPLETE — configurable compliant hydraulic graph, synthetic dialyzers, diffusion/convection/UF, numerical convergence and conservation. | [M2](evidence/m2/README.md) |
| M3 | COMPLETE — Python body/circuit water and six species, external transfers, water-only weight and limited fixed-pCO2 indicator. | [M3](evidence/m3/README.md) |
| M4 | COMPLETE — HD/pre/post HDF, online mixing/temperature/filter hydraulics, replacement and gross/net balances. | [M4](evidence/m4/README.md) |
| M5 | COMPLETE — guarded lifecycle, hazard-specific constraints, ACK/silence/reset/restart and independent actuator arbitration. | [M5](evidence/m5/README.md) |
| M6 | COMPLETE — actual LVGL/SDL device client, input/confirmation, modeled observations, trends, stale/disconnected sessions. | [M6](evidence/m6/README.md) |
| M7 | COMPLETE — separate ImGui console/authenticated broker, immutable configurations/fault calendars, pause/replay/compare/export and batch CLI. | [M7](evidence/m7/README.md) |
| M8 | COMPLETE — input/process/network/role controls, actual-image inventories/SBOMs, scans, license/integrity checks and recoverable real CI. | [M8](evidence/m8/README.md) |
| M9 | COMPLETE — integrated deployments/matrix/long runs, actual simultaneous UI/console, reproducible source package and lifecycle/operating templates. | [M9](evidence/m9/README.md) |

Persistent checkpoints: [milestone plan](../docs/MILESTONES.md),
[decisions](../docs/DECISIONS.md), [reviews](REVIEWS.md).
Each M9 acceptance has its own checked artifact chain. Historical M1–M8 trace
test states/evidence remain unchanged. The schema 1 assurance anchor is retained;
new artifacts identify actual software builds separately, without relabeling old
runs as executed on newer source. Original broad normative tests remain planned.

## Remaining limitations and decisions

All 184 standards checklist entries,12 edition/applicability gaps and nine release
prerequisites remain open. Independent clinical/model/usability and risk review,
authorized calibration/validation datasets, the intended physical product/treatment
envelope and EU-first applicability/GSPR assessment remain unresolved. A later US
assessment remains separate. No owner, signature or normative approval is invented.
The73 recorded dependency advisory IDs remain open; software controls neither
accept those risks nor clear redistribution of complete container images.

Models and thresholds are synthetic and uncalibrated. Fixed-pCO2 indication is
not a full acid-base/respiratory model. No cardiac/red-cell/osmotic regulation,
validated cleaning/air clearance, microbial quality or sterility is demonstrated.
Conductivity does not identify individual species; contamination, breaches and
stuck detectors can remain latent. Some pump/filter latches require a fresh run.
Shared kernel/plant/runner/configuration/protocol causes remain; hardware
independence is not established. Native same-UID mode and X11 administration
are trusted development boundaries.

HALT requested, acknowledged and observed states remain distinct. Lost delivery
can remain unconfirmed. Patient failure after plant commit aborts without distributed
rollback. JSONL recovery covers process interruption, not power-loss durability.
Free-space checks do not reserve a shared filesystem; long verifications require
2048 MiB and sequential execution. Resource measurements apply to recorded
configurations. WSL2, Linux containers, actual WSLg and hosted Ubuntu CI were
exercised; other hardware/display stacks remain outside this evidence.

There is no remaining process, Docker or graphical permission block. Earlier
blocked/failed attempts are historical failures, never retroactively PASS.
Publication and Docker inputs remain explicit allowlists. Licensed standards,
extracts/images and private material remain excluded. Normal structural checks
must pass while release gates remain BLOCKED. Existing user work and Git history
are preserved; owned large artifacts have verified reversible storage records.

## Next step for the remaining external obligations

Obtain authorized calibration/validation data and independent clinical/model,
usability, cybersecurity/risk and regulatory review for a defined intended use.
Resolve standards/applicability and dependency findings before a physical-device
or clinical release. Use the supplied lifecycle/model-data templates and separate
calibration from validation data. The documented synthetic demos and regression
suites are executable without those external approvals.
