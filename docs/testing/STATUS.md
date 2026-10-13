# Current baseline: verification and acceptance

Document ID SVR-01; revision 5; prepared 2026-10-13; approval pending.
This is the current applicability decision. Exact source identities and executed
checks are in [checks.json](../../assurance/audits/checks.json); the containing Git
commit identifies the complete candidate. Main `602e8dab8e65efdb0bc8db1051ce0006f0d3adfd`
is the change base. Earlier execution records are not automatically current passes.

## Current CI policy

The [CI protocol](CI.md) defines the new PR gate: two complete HDF POST cycles with
ten minutes of simulated therapy, plus retained phase/count/throughput diagnostics.
The 100000-step campaign remains a manual `dynamic-endurance` job. The current
[CI regression report](../../assurance/audits/ci-regressions.json) identifies local
execution; actual current-head Compose acceptance must be inspected in Actions.
The earlier `2332ee6` hosted run 38361819029 passed `verify` and timed out in the
100000-step resource job, with no reported OOM and no final manifest.
The shorter gate does not retroactively close that timeout or endurance acceptance.

## Numerical correction and supporting evidence

The latest correction allows conservative reverse transport between internal
dialysate cells during valve closure. External feed/drain validation remains
one-way. It also replaces misleading comparisons of unequal per-tick averages with
common observation windows and separately examines unequal starting states.
The [flow protocol](FLOW_REFINEMENT.md) explains the equations, reproduction,
criteria, measured results and unresolved scope.

| Decision area | Applicable evidence | Remaining closure |
| --- | --- | --- |
| Internal dialysate transport | Before-source HD failure reproduced at 25 ms; corrected HD/PRE/POST complete; analytic and seeded conservative-transfer regressions | Wider physical envelope and independent scientific review |
| Numerical flow refinement | 24 analytic valve cases; 30 coupled runs; identical-checkpoint common-window and volume differences decrease down to 25 ms | Fresh workflows not uniformly monotonic; global error budgets, concentration/UF steps and mesh/coupling study |
| Local regression selection | 40 tests passed on the preceding solver correction; exact methods and source hashes in [flow regressions](../../assurance/audits/flow-regressions.json) | Real IPC, clean hosted build and full hosted suite on the published head |
| Requirements/design | 99 obligations across 60 parent IDs; structure, document links and implementation hashes checked | Independent semantic/coverage acceptance |
| Resource use | Previous-source native results retained; previous hosted resource job timed out | Complete current-model 100000-tick Compose runs with bounded RSS, final artifacts and repeat hashes |
| Calibration/usability | Measurement, uncertainty, holdout and critical-task procedures written | Actual measurements, representative-user evidence and approved operating envelope |
| Normative/security release | Engineering design and dependency inventory available | Full-text applicability, current image/advisory/static checks, classification, essential-performance/risk decisions and independent approvals |

The local coupled harness executes actual C++ plant equations and the actual Python
patient through pipes. It does not establish RPC behavior, container isolation,
clinical accuracy or independent acceptance. Unix-socket process tests are blocked
locally by EPERM; Docker and cppcheck are unavailable.

## Applicability of preceding evidence

The [preceding check record](../../project-log/audits/fda5058-checks.json) identifies
86 passing local tests, native core/GUI build and the preceding implementation.
The [case allocation](../../assurance/audits/obligation-results.json) belongs to
that selection; it is not a claim that every method was rerun after this model change.
Unchanged C++ workflow/wire/GUI code retains that engineering support. Coupled
patient results, resource use and Python module inventories require reassessment.
The numerical equations have not changed in the CI update. The flow regression
report retains its preceding source hashes; it is supporting solver evidence, not
an execution claim for the changed runner diagnostics and CI tooling. The preceding
[check record](../../project-log/audits/2332ee6-checks.json) preserves that identity.

The preceding [native resource report](../../assurance/audits/resource-native.json)
and [repeat comparison](../../assurance/audits/resource-comparison.json) recorded two
identical 100000-record trajectories and peak RSS 18.74/18.82 MiB. Those measurements
are for the identified preceding model, not the revised transport implementation.
The preceding [native build](../../assurance/audits/native-build.json) and
[SBOM](../../assurance/audits/native-application.cdx.json) likewise identify their own
source. The [static-analysis report](../../assurance/audits/static-analysis.json)
is blocked, not a clean scan.

Hosted run [38353153658](https://github.com/pmasala/DialysisLab/actions/runs/38353153658)
on `fda5058f7648a323c74dd4e2c20cf46f92daed83` passed `verify`. Its separate
`dynamic-resources` job timed out after 2400 seconds. Retained collection diagnostics
show `compose_exit_code=124`, no reported OOM flag, successful artifact extraction
and only the initial `running` manifest. `completed_ticks=0` in that initial manifest
is not a measurement of progress at timeout. No completed resource run is claimed.
The current head's hosted result must be inspected separately.

## Reproduction

- `python3 tools/flow_refinement.py --output build/flow-new.json` executes the
  current numerical protocol; output must not exist beforehand.
- `PYTHONPATH=python:tools:tests python3 -m unittest -v test_flow_refinement`
  executes its five focused regression methods.
- `python3 tools/audit_campaign.py --mode resource --ticks 100000 --output build/resource-new.json`
  executes a native resource run and retains its identity and failures.
- `python3 tools/verify_integrated.py --group dynamic-long --compose` executes the
  separate maximum-size service campaign; native results cannot replace it.

Historical evidence bytes and recorded test statuses remain unchanged in the
[Project Log](../../project-log/README.md). Structural success is distinct from
release acceptance and standards conformity.
