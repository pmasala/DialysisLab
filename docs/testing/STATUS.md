# Current baseline: verification and acceptance

Document ID SVR-01; revision 3; prepared 2026-10-12; approval pending.
This is an applicability decision for the current corrective candidate, not a history
of development. Source identities and exact executed cases are in the
[audit check report](../../assurance/audits/checks.json). Git identifies its published
commit. Main `602e8dab8e65efdb0bc8db1051ce0006f0d3adfd` is the change base.

## What changed and which evidence applies

This candidate changes Python observation/metadata bounds, initial dynamic dialysate
inventory validation in Python and C++, and experiment preset discovery/defaults.
The current dynamic maximum-size campaign and its CI job are new. Earlier successful
CI on main is therefore insufficient for this candidate; a new hosted run is required.
The local evidence below covers actual source calculations through pipes and native
rendering. It does not claim Unix-socket transport or container isolation.

| Decision area | Current evidence and limitation | Remaining closure |
| --- | --- | --- |
| Core and GUI compilation | Native Release configuration/build succeeded | Hosted clean build and remaining platform gates |
| Requirements and design allocation | 99 detailed obligations across all 60 parent IDs; AST-checked test links | Independent semantic/coverage acceptance; partial scopes remain visible |
| State, endpoint and protection logic | Actual C++ matrix and actual coupled plant/patient fault tests executed | Wider process fault campaigns and independent oracle review |
| Wire consistency | Six actual C++/Python output families checked at/outside numeric bounds and malformed lengths; five plant configuration families checked for invalid fields | Legacy and composite semantic tests retain separate scopes; no exhaustive fuzzing claim |
| Guided preset usability | Default/catalogue/load validate physical HD/PRE/POST with complete scheduled workflows | Actual service launch test included in hosted suite; human validation separate |
| Numerical refinement | Nine actual coupled runs at 400/200/100 ms; conservation checked | Feed/drain pointwise refinement is nonmonotonic; approved accuracy budgets, wider transients and independent measurements absent |
| Maximum-size resource use | Two 100000-tick native runs; identical 1547821782-byte trajectories; peak RSS 18.74/18.82 MiB | Separate dynamic-resources CI job tests actual Compose limits, two identical runs, OOM state and evidence retention |
| Security/dependencies | Current threat/common-cause design; fresh native inventory of 31 application components | Docker/cppcheck unavailable locally; current image/advisory execution and responsible residual-risk disposition |
| Requirement acceptance | No independent acceptance recorded | Named competent reviewers and evidence decisions |
| Calibration and usability | Written measurement/holdout and critical-task procedures | Actual measurements, representative-user evidence and approved operating envelope |
| Normative/reference release | Blocked | Full-text applicability, classification, essential performance/risk decisions and independent approvals |

The [case results](../../assurance/audits/regressions.json) record 86 passed tests,
with no failures or skips in the declared local selection. The
[current result allocation](../../assurance/audits/obligation-results.json) maps
those methods to individual obligations and explicitly labels methods not executed
locally. Shared methods and supporting cases do not count as full parent acceptance.
The [native build](../../assurance/audits/native-build.json) and
[application SBOM](../../assurance/audits/native-application.cdx.json) identify the
built binaries/modules and selected dependencies. The
[static-analysis report](../../assurance/audits/static-analysis.json) records BLOCKED
because cppcheck is absent; it contains no clean-scan claim.

The [current native resource report](../../assurance/audits/resource-native.json)
records 99935 treatment ticks, 100000 retained records and no unexpected alarm.
The [repeat comparison](../../assurance/audits/resource-comparison.json) preserves
the exact configuration and distinguishes the earlier retention wrapper from the
final harness; actual trajectory bytes match. This is native repeatability evidence,
not independent clean-build reproducibility or a container-memory measurement.

## Reproduction and evidence boundaries

- `tests/test_audit_closure.py` executes state/mask/freshness/volume tests and checks
  guided preset configuration plus failed-resource-report retention.
- `tests/test_document_contracts.py` checks the controlled register and actual wire
  implementations. These are conformance witnesses; no test pass establishes clinical
  or regulatory adequacy of a numeric threshold.
- `python3 tools/audit_campaign.py --mode convergence --output build/refinement.json`
  regenerates the [refinement report](../../assurance/audits/convergence.json).
- `python3 tools/audit_campaign.py --mode resource --ticks 100000 --output build/resource.json`
  retains every record, configuration and result; failed runs preserve the written
  prefix and a failed report. Output directories must be fresh to avoid overwriting
  earlier evidence. The report records runtime and harness hashes at execution start.
- `tools/verify_integrated.py --group dynamic-long --compose` runs the separate
  current-model maximum-size container campaign. Hosted CI collects its diagnostic
  report/manifests even on failure. Its completion cannot be inferred from a native pass.

Full Unix-socket process tests are blocked locally by EPERM; Docker and cppcheck
are absent. These are environment limitations, not successful tests or reasons to
weaken protection. Current CI must be inspected on the exact published head before
changing this decision. Historical results stay in the separate
[Project Log](../../project-log/README.md); their recorded bytes and test statuses
are preserved, without inheriting their passes here.
