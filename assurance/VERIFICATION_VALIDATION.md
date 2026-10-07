# Verification and validation strategy

Status: proposed strategy. No dialysis application tests or model validation have been executed.

## Evidence contract

Before execution, each test defines linked requirement/control IDs, purpose, setup, initial state, inputs/faults, expected response, quantitative tolerance/deadline where relevant, oracle, environment, and pass/fail rules. Record actual software revision, binary/image identities, dependencies, scenario/configuration, model version, solver settings, seed, execution time, raw data, result, deviations, and reviewer decision.

Distinguish planned protocols, executed runs, reviewed reports and accepted residual risks. Never turn a protocol into a "passed" result without execution. Re-run or reassess evidence affected by changes.

## Verification levels

| Level | Required investigation |
| --- | --- |
| Requirements/design review | Completeness against intended use and full standards; measurable criteria; hazards/threats; interfaces and assumptions. |
| Unit | State transitions, boundary/range/units handling, arithmetic, parser failures, numerical kernels and error paths. |
| Integration | Commands/telemetry, control/protection arbitration, buffering, stale/reordered/duplicate messages, reconnects and process failures. |
| System | Full preparation, HD/HDF treatment, pre/post routing, online fluid preparation, interruptions, recovery and completion. |
| Fault/safety | Sensor/actuator faults, occlusion/leak/air surrogates, substitution failure, thermal/composition imbalance, protective timing, common causes. |
| Timing/resources | Virtual-time semantics separately from wall-clock behavior; deadline budgets, CPU/memory/storage stress and scheduling interference. |
| Security | Authorization/isolation, fuzzing, malformed/replayed messages, dependency findings, update integrity/recovery and availability under attack. |
| UI/alarms | Parameter entry/confirmation, units, stale indicators, priority/state transitions, audio/visual behavior, user errors and critical tasks. |
| Models | Conservation, analytic/limiting cases, timestep/solver convergence, calibration, independent validation, uncertainty and sensitivity. |
| Deployment | Reproducible builds, headless and graphical profiles, WSL2 and native Linux, clean-environment startup and replay. |
| Reference-use validation | Representative users complete intended education/research/engineering tasks with predefined success criteria. |

Use compiler diagnostics, static analysis, runtime sanitizers and coverage as complementary evidence. Choose coverage metrics/targets from the safety analysis and lifecycle plan; do not claim a universal IEC-mandated percentage or automatic SIL/MC/DC requirement. Explain uncovered code and test adequacy.

## Simulation independence and credibility

Avoid validating control logic with an oracle that simply repeats the same implementation. Use separately derived balances, analytic benchmarks, independently sourced measurements and peer-reviewed models where appropriate. Expose model assumptions, valid domains and calibrated parameters.

Separate calibration and validation data; assess source quality, measurement uncertainty, identifiability and sensitivity. A good numerical fit does not establish clinical predictive validity. Public demo datasets must have redistribution permission or be synthetic.

Physiology and hydraulics exchange conserved quantities with explicit units and conventions. Verify gross membrane fluid transfer, substitution, other inputs/outputs, circuit storage and patient mass consistently. Parameterize dialyzer-specific claims and validate them at documented conditions.

## Tool confidence

Assess tools used to generate code, requirements, stimuli, or pass/fail judgments for their ability to introduce or hide errors. Document intended use, versions, independent checks and validation measures proportionate to that risk. The included traceability checker has self-tests but is not a qualified compliance tool. Its structural pass does not prove the truth or completeness of entered evidence.

## External evidence obligations

For a downstream medical device, identify and retain obligations for real electrical safety, EMC, thermal/mechanical/fluid system behavior, actual sensors and actuators, fluid quality/materials, alarm audibility/visibility, representative-user validation, clinical/performance evidence as applicable, manufacturing controls and field monitoring. Simulation may inform those activities; it does not close them.

## Completion rule

Reference release requires reviewed results for all applicable requirements and risk/security controls, with justified dispositions for issues and documented model validity. A finished-device claim additionally requires its external evidence and responsible approvals. The project cannot become complete merely by creating this strategy or filling a trace matrix.
