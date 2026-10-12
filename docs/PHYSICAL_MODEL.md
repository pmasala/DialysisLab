# Blood, dialyzer and dialysate preparation

DialysisLab simulates a generic dialysis machine connected to a synthetic patient.
Needles, tubing, chamber levels, blood properties and dialyzer filtration affect
its pressures and flows. HD, HDF PRE and HDF POST use distinct fluid paths.

![Blood and fluid paths](images/physical-circuit.svg)

## Run it

Build as described in [Quickstart](QUICKSTART.md), then run a short complete cycle:

```bash
PYTHONPATH=python python3 -m dialysislab.runner --local --build-dir build/core --config scenarios/physical_hdf_post.json --output build/physical-post
```

Use `physical_hd.json` or `physical_hdf_pre.json` for the other modalities. These
one-minute treatments exercise the workflow. The interactive `device_guided.json`
uses four hours and waits for operator confirmations.

The device UI follows the treatment phases. Its circuit tabs show machine flows,
pressures and chamber levels. The separate experiment console exposes the patient
and the contents of each circuit compartment. Initial hematocrit, needle geometry
and model coefficients are configured in the scenario before starting the run.

## What is modeled

Blood passes through arterial tubing and chamber, the pump, 12 dialyzer segments,
the venous chamber and return tubing. Chamber liquid volumes change as gas expands
or compresses and their level regulators act. Cells, proteins and solutes have
separate retained inventories, so saline and concentration changes take time to
travel along the circuit.

PRE infusion enters before the filter. POST infusion enters after it. Gross UF
removes net fluid loss plus substitution; a post-infusion cannot dilute the blood
upstream inside the filter. Local blood properties determine viscosity, pressure
loss and oncotic pressure. Needles and tubes use their internal diameter and length.

Fresh fluid is prepared from water, acid concentrate and bicarbonate. Stocks are
finite. The mixer has a power-limited heater and a thermal balance. Conductivity
is derived from ionic composition, a non-ideal-mixture correction and temperature.
Two serial substitution ultrafilters retain their quality/integrity protections.

The dialysate has countercurrent solute transport, compliant fluid storage, a feed
pump, alternating volumetric balancing chambers and an extra UF pump. Controller
and sensor response times mean actual removal can temporarily differ from target.
Independent protection still checks pressure, fluid quality and net-volume error.

Read [Dynamic model and reference checks](DYNAMIC_MODEL.md) for configuration,
conservation equations, the inspector and reproducible calibration commands.

## What the results mean

Software tests check the numerical laws, conservation and treatment workflow.
Selected public dialyzer data support a limited urea-transport fit with a separate
holdout measurement. That fit does not calibrate blood rheology, chamber mechanics,
patient refilling, all electrolytes or a complete machine.

The default viscosity law remains
`mu = 1.2 exp(-0.025(T-37)+0.04(Cp-7))/(1-Hct)^2.5`, a synthetic high-shear law
in mPa s. The oncotic approximation is
`pi = 2.1 Cp + 0.16 Cp^2 + 0.009 Cp^3`, in mmHg with Cp in g/dL.
Segment filtration uses `UF_i = max(0, KUF/12 * (Pb_i-Pd_i-pi_i))`.

Liquid momentum remains quasi-steady; chamber and solute inventories are dynamic.
Backfiltration, clotting, hemolysis, protein deposition, acid/CO2 reaction chemistry
and disinfection efficacy are not modeled. The dynamic guide describes the remaining
assumptions and what additional measurements would be needed.

## Sources informing the model

These papers inform structure and limitations; they do not validate this code:

- [Internal filtration model (2005)](https://pubmed.ncbi.nlm.nih.gov/15876825/): axial blocks and local blood properties.
- [Fluid and solute transport in hollow-fiber dialyzers (2019)](https://pmc.ncbi.nlm.nih.gov/articles/PMC8673592/): coupled pressure, filtration and oncotic effects.
- [Protein concentration and oncotic pressure (1983)](https://pubmed.ncbi.nlm.nih.gov/6881091/): empirical assessment of a polynomial approximation.
