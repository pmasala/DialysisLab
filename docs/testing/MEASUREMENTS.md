# Model calibration and independent measurement protocol

Document ID STP-CAL; proposed protocol. This plan defines work that can be prepared
now; it does not claim that bench measurements have been collected. Only simulated
patients/equipment are connected to DialysisLab. Acquisition on a separate bench
requires its own approved procedure and competent operator.

## What calibration can and cannot establish

Calibration estimates coefficients from measured input/output pairs. Validation
then challenges the frozen coefficients with independent observations. Fitting and
validating on the same records cannot establish predictive accuracy. A conservative
solver can balance water perfectly while predicting the wrong pressure or clearance.

Current executable scope is the conditional urea fit in
[calibration.py](../../python/dialysislab/calibration.py) and
[calibrate_models.py](../../tools/calibrate_models.py). It fits selected public
clearance points and reports a separate holdout. Chamber, rheology, sensor, thermal,
electrolyte and patient refill fits below are **prospective**. No general Excel importer
or automatically validated all-model calibration file is claimed by this protocol.

## Record template and acquisition rules

Each dataset needs: dataset ID and revision; permission/source URL and redistribution
terms; device/component model and lot where available; operator; UTC timestamp;
raw-file hash; units; instrument identity, calibration date and uncertainty; geometry;
fluid composition, viscosity/Hct/protein where applicable; temperature; input settings;
measured inputs and outputs; sampling frequency and synchronization uncertainty;
steady/transient flag; replicate ID; exclusions with reason; fit/validation partition.
Do not publish patient identifiers or proprietary specifications without authorization.

Before acquisition, freeze the factors and their low/nominal/high values **inside the
approved bench envelope**, using the model operating domain and available component
specifications. Do not take a parser's broad upper bound as a safe bench setting.
Use at least three independent repeat acquisitions per selected steady condition
as a proposed repeatability design; the responsible model reviewer must justify
sample size from the uncertainty target. Record all repeats, including failed runs.

Define settling as a measured stability rule over a stated window, not simply a
fixed wait. Choose sample rate from the fastest phenomenon to identify; a 30 ms
modeled valve event needs time resolution substantially below 30 ms to resolve its
shape. Retain unsmoothed data and any filter settings. If the available instrument
cannot resolve that event, mark the response unidentifiable instead of fitting noise.

## Measurement checklist by model

| ID / model | Required conditions and simultaneous measurements | Identification and independent challenge |
| --- | --- | --- |
| CAL-HYD / lines and needles | For each geometry: zero, low, nominal and high positive flow; pressure at both ends, measured flow, temperature and fluid viscosity; repeat with each intended needle/tube set | Estimate resistance from ΔP/Q and assess nonlinear residuals; reserve an intermediate flow and a separate assembly. Compare diameter and length effects separately |
| CAL-PUMP / blood pump | Command steps up/down, steady points, increasing backpressure and stall approach within approved bench limits; actual flow, inlet/outlet pressure, time and pump command | Estimate response delay/time constant and head/flow limitation; reserve a new step amplitude and backpressure sequence; do not equate commanded and measured flow |
| CAL-CHAM / arterial and venous chambers | Separate chambers: slow pressure–volume sweep and inflow/outflow imbalance steps at several initial air volumes; liquid level/volume, gas pressure, liquid pressure, actual gas actuation and both boundary flows | Fit compliance/gas-law parameters with absolute pressure and measured ambient pressure; reserve another initial air volume. Resolve level sensor and geometry separately |
| CAL-FILT / membrane hydraulics | Each dialyzer: measured blood and dialysate inlet/outlet pressures, four boundary flows, UF by independent mass/volume, temperature, viscosity/Hct/protein; low/nominal/high flows and multiple TMP points | Estimate KUF and axial pressure losses separately; account for oncotic terms if using protein-containing fluid. Reserve another run/lot and an unfit TMP; a water KUF does not validate blood behavior |
| CAL-SOL / exchange | HD, PRE and POST separately; measured blood/dialysate/substitution flows, UF, all inlet/outlet concentrations for six solutes, synchronized sampling, initial volumes, temperature, dialyzer type | Estimate species KoA and sieving only where the experiment identifies them. Use zero-UF diffusion and suitable filtration contrasts to separate effects. Reserve flow/modality conditions and report residual mass balances |
| CAL-DIAL / dialysate control | Feed/UF/drain demand steps, balance-chamber changeovers and bypass; actual feed, drain, UF, chamber positions, pressure, inventory and timestamps | Identify delay, controller response and storage. Validate fresh disturbance sequences including zero demand. Integrate independent measured water balance with sensor uncertainty |
| CAL-PREP / fluid preparation | Concentrate dilution changes, initial reservoir states, flow changes and stock depletion; water/concentrate masses, reservoir volume, six-solute assays, temperature, conductivity and mixing flows | Fit mixing/stock model; identify conductivity mapping with measured composition and temperature. Same conductivity does not uniquely identify six electrolytes; reserve composition combinations |
| CAL-HEAT / thermal | Inlet temperature and flow steps at several heater demands; electrical/thermal power distinction, inlet/outlet/tank temperature, reservoir volume and ambient temperature | Fit heat capacity/loss/response using an energy ledger; reserve combined flow/temperature disturbance. State whether electrical efficiency is estimated or assumed |
| CAL-SENS / observations | Reference pressure, flow, temperature, conductivity and level sweeps plus steps, stale/disconnected indications where bench procedure permits | Estimate bias, noise, delay and saturation separately; reserve sweep direction and step shape. Software fault injection alone does not validate sensor performance |
| CAL-PAT / patient coefficients | Authorized de-identified observations or identified published aggregates: elapsed treatment time, measured modality/flows/UF/substitution, weight/fluid balance, serial electrolytes/urea, Hct/protein and relevant intake/output | Predeclare what is observable; separate vascular refill from intercompartment exchange. Split by patient/treatment rather than adjacent samples. Record confounding and missing inputs; no clinical claims from a synthetic profile |

A row is complete only when conditions, raw files, uncertainties and validation
partition are present. An unavailable measurement remains explicitly missing.
Manufacturer typical values with unspecified uncertainty are reference targets,
not a substitute for traceable bench uncertainty.

## Fit, uncertainty and acceptance worksheet

For every fitted parameter record symbol, units, equation/source, prior bound,
estimate, confidence/uncertainty method, sensitivity, correlations, and which raw
records identify it. Freeze solver version, mesh, time step, objective weights and
optimizer seed/options. Do not fit two strongly confounded parameters without an
additional discriminating measurement or a documented fixed assumption.

For observation i, report residual eᵢ = prediction − measurement, mean bias, RMSE,
maximum absolute error, and signed residual plots against flow, pressure, time and
composition. Report absolute error near zero; relative error alone is undefined or
misleading there. Include measurement uncertainty, repeatability and numerical
error; state covariance assumptions when combining them.

Before examining validation outcomes, the model owner and independent reviewer
must complete one acceptance row per claimed output/domain:

| Required field | Decision to record |
| --- | --- |
| Output and operating domain | Quantity, unit, modality, geometry, composition and time range |
| Intended simulation use | Which engineering decision depends on this accuracy |
| Error allowance E | Justified maximum absolute error, plus relative rule if meaningful |
| Uncertainty U | Expanded uncertainty, coverage factor and calculation/source |
| Numerical allowance | Bound from time-step/mesh/coupling convergence |
| Decision rule | Proposed conservative rule: absolute validation error + U <= E at every required condition, with separate bias/transient limits if justified |
| Dataset independence | Held-out assembly/run/patient identities and hashes |
| Result and exception | Actual metrics, failures, approved limitation or corrective action |

There is no defensible universal numerical E for all these models. An unfilled E
blocks acceptance of that output; it must not become an arbitrary percentage after
seeing results. The existing urea demonstration uses 5% relative holdout error as
an engineering example, not an approved all-solute or clinical limit.

## Calibration delivery and review

A future general calibration artifact must identify model/schema version, parameter
names/units, valid operating domain, dataset hashes/rights, fit/holdout partition,
uncertainty and acceptance status. Import must reject unknown/missing parameters,
wrong units, nonfinite/out-of-domain values and model-version mismatch atomically.
The effective configuration and artifact hash must be retained in every run.
Until implemented and tested, users configure supported coefficients through the
existing scenario schema and the limited current fit tool.

Closure requires independent reproduction on the frozen validation partition,
reviewed error plots and a named approval of the declared domain. A fitted parameter
file alone cannot close DOC-08 or establish physiological accuracy.
