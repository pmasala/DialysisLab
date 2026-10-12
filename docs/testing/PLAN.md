# Master verification and validation plan

Document ID SVP-01; revision 1; status: proposed protocol, not an execution report.
Owner roles: verification lead and independent reviewer (appointments outstanding).
Previous: [Interaction design](../design/INTERACTION.md). Next: [Test catalogue](CATALOG.md).

## Purpose and scope

Verify the simulator's requirements, numerical behavior, component interfaces,
operator workflow, deployment and evidence integrity. Separately assess whether it
is suitable for its stated research/education/reference use. Clinical validity and
finished medical-device conformity require additional evidence and responsibility.
Current criteria are specified here and in the topic protocols. Earlier strategies
are available only as historical context through the separate Project Log.

Use [Requirements](../REQUIREMENTS.md) for obligations and the
[Catalogue](CATALOG.md) for all 65 registered test records and concrete Python test
methods. The catalogue is an inventory, not a claim of complete requirement coverage.

## Test levels and allocation

| Level | Scope | Executable entry point / procedure |
| --- | --- | --- |
| Document/static | Requirement links, current generated documents, publication, dependency policy | `documentation.py`, `check_traceability.py`, `check_standards.py`, `check_publication.py` |
| Unit/numerical | Parsers, state guards, equations, limiting cases and atomic patient rejection | [Model protocol](MODELS.md), discovered `tests/test_*.py` |
| Process integration | Real sockets, arbitration, failure timing, three treatment routes and ledgers | [Failure protocol](FAILURES.md), `verify_m1.py`, `verify_models.py` |
| Device/console | Actual widget input, phase visibility, confirmation, stale/reconnect state and inspection | [Workflow protocol](WORKFLOW.md), `verify_device_ui.py`, `verify_console.py` |
| Container/system | Actual isolated roles, volumes, resource limits, repeated/recovered runs | `verify_compose.py`, `verify_experiments_compose.py`, `verify_models.py --compose` |
| Sustained/package | Long-run memory, replay integrity, source archive build and dependency identity | [M9 acceptance](../M9_INTEGRATION.md), `verify_integrated.py`, `package_release.py` |
| Independent validation | Declared model operating envelope and representative-user tasks | Measurement/user protocols to approve; currently open |

## Entry conditions

Freeze requirement/protocol revision, source commit/tree, complete scenario, seed,
solver step/grid, toolchain, binary/image IDs, OS and deployment profile. Use a fresh
output directory. Confirm necessary display/socket/Docker permissions before assigning
a process/UI case. A missing prerequisite is BLOCKED; it is not a passed or silently
skipped acceptance case. Unit tests may run without those facilities but cannot
replace the blocked system case.

Record whether the case is legacy, guided, physical or dynamic and whether interaction
is scripted or manual. For numerical work, identify fluid composition, temperature,
measurement uncertainty, fitted data and independent holdout data before execution.

## Common execution and evidence rules

For each case record the requirement/risk IDs, initial state, exact inputs and fault
timing, stimulus steps, expected observations, independent oracle, quantitative
criterion, actual results and deviations. Include the command, start/end UTC times,
exit status, logs and artifact hashes. Preserve original failed runs before rerunning.
Do not change tolerances after seeing a result without a separately reviewed protocol
revision. Record physiological limits separately from input-parser bounds.

A successful software run is insufficient if required artifacts are missing, identities
contradict, coverage was skipped, or an oracle was not independent enough for the claim.
A failed STEP must be tested after submission as well as before it, because lost replies
can leave a plant command accepted. Patient post-commit failure needs separate evidence.

## Acceptance and release decision

| Claim | Required evidence |
| --- | --- |
| Code regression passed | Executed test result for identified code and declared scope, with no hidden failures/skips |
| Requirement verified | Each acceptance obligation covered, results reviewed and deviations dispositioned |
| Model calibrated | Identified measurement set, units/conditions, fit method and uncertainty/identifiability assessment |
| Model validated | Independent validation data and acceptance within a declared operating envelope |
| Reference release accepted | Reviewed requirements/risks, dependency findings, supported profiles and remaining limitations accepted by responsible owners |
| Downstream device conformity | Product-specific normative, physical, usability, clinical and quality-system evidence outside this simulator-only decision |

The 1e-6 integrated water/solute tolerance is a numerical ledger criterion, not a
clinical allowable error. Legacy cases can have stricter predeclared tolerances.
Protective virtual-time response is assessed from the first unsafe frozen sample;
wall watchdog response is measured on a wall clock. Do not conflate fault injection
time, threshold crossing time and output restriction time.

## Execution commands and change impact

From repository root:

```bash
python3 tools/documentation.py --check
python3 tools/check_traceability.py assurance/traceability.json
python3 tools/check_standards.py
python3 tools/check_publication.py
python3 tools/ci_verify.py --output build/ci-reviewed
```

The last command requires the actual build/container environment and runs the broad
software pipeline. Its valid blocked release gates are reported separately from
software failures. It does not supply a standards approval. For targeted tests use
the exact method names in the catalogue; record all skips and scope reductions.

After a model change rerun conservation, limiting/transient/convergence cases,
all affected modalities and deployment paths. After a UI change rerun actual
widgets plus server guards, confirmations and observation freshness. After an
interface change rerun both encoders/decoders, malformed frames, lost replies,
capacity limits and compatibility. Documentation-only changes need structural,
link, generation and publication checks; a full hardware/physiology run does not
validate prose. CI may still execute the existing broad pipeline.

Coverage reporting, independent model validation, complete guided boundary matrices
and representative-user acceptance are open audit items. No arbitrary coverage
percentage is invented as an IEC requirement. A named reviewer must justify test
adequacy and dispositions before acceptance.

## Completing the current evidence package

Use the [atomic allocation matrix](COVERAGE.md) to select concrete test methods,
then apply the [closure protocol](CLOSURE.md) for missing state/boundary/security
cases and the named-review record. Collect calibration data under the
[measurement protocol](MEASUREMENTS.md), which separates fitting from independent
validation and requires an accuracy budget before judging results. These protocols
are prepared now; their prospective cases have no fabricated execution result.
