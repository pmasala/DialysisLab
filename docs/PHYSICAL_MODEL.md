# Blood, dialyzer and dialysate preparation

The default guided session now uses a generic physical model. Blood properties,
needle geometry and infusion position affect the calculated pressures. The model
also consumes acid concentrate and bicarbonate and heats the prepared fluid with
a power-limited heater. These are synthetic engineering profiles, not a replica
of a commercial machine or a calibrated patient prediction.

![Physical blood and fluid paths](images/physical-circuit.svg)

## Try it

Build as described in [Quickstart](QUICKSTART.md), then run a short complete cycle:

```bash
PYTHONPATH=python python3 -m dialysislab.runner --local --build-dir build/core --config scenarios/physical_hdf_post.json --output build/physical-post
```

Use `physical_hd.json` or `physical_hdf_pre.json` for the other modalities. These
short examples include the operator sequence; their one-minute treatment is for
software checks. The interactive `device_guided.json` keeps a four-hour treatment
and waits for the operator to confirm connection, start, return and disconnection.

Open the machine's **Prescription** tab to change blood or active substitution
flow. Inspect pressures and flow limits in the machine UI. The external experiment
console shows patient hematocrit, proteins, every filter segment and remaining
fluid supplies under **Inspector**; each numeric field can be selected as a trend.
The complete values are retained in `trajectory.jsonl`.

## Set up the patient and disposable

Edit the scenario file before launching a run. `patient.hemodynamics` contains
initial hematocrit (a fraction: `0.35` means 35%), vascular volume, plasma protein
concentration, blood temperature and the tissue-refilling coefficient. There is
no device-UI control to set hematocrit during therapy.

The patient model tracks red-cell volume and protein mass in the vascular and
extracorporeal pools. Removing fluid concentrates them; refilling and infusion
dilute them. Priming starts with no red cells in the circuit. Saline return moves
retained cells back to the patient; cells subsequently sent to waste remain in a
loss ledger. A return-volume target therefore does not imply that every cell has
been recovered. Refilling redistributes fluid; it does not create body water.

`physical.blood` defines each needle's **internal diameter and length** in mm,
tube geometry, arterial/venous chamber blood volumes and dialyzer blood volume.
Nominal needle gauge alone is insufficient. The sum of these fluid volumes must
match `patient.prime_mL`; a mismatch is rejected. Chamber volumes are fixed in this
version and contribute to transit/mixing volume. Gas interfaces and chamber-level
control are not modeled; unused air-volume parameters have been removed.

The physical profile supplies filter resistance, hydraulic permeability, pump-head
capacity and dialysate-pressure bounds. The older `circuit` graph remains a
transport configuration for existing scenarios; its resistance/compliance solver
is replaced when `physical` is present. Use `physical.blood` for this model's
geometry. Legacy graph-edge/resistance fault injections are rejected for physical
scenarios instead of silently producing no effect.

## What happens along the dialyzer

The blood side is divided into 12 segments. Each segment computes water removal,
hematocrit, protein concentration, viscosity, oncotic pressure and blood pressure.
Cells and proteins do not cross the membrane in this reduced model.

- In **HD**, gross filtration is the requested net fluid removal.
- In **HDF PRE**, substitution joins the blood before the first segment. This
  increases inlet flow and dilutes blood entering the filter.
- In **HDF POST**, blood enters undiluted. Gross filtration removes net fluid loss
  **plus** substitution volume. The substitution enters only after the last segment.

The post-infusion mixture cannot reduce viscosity upstream inside the filter.
Pressure losses are calculated from local flow and viscosity; pre/post pressures
are not adjusted to make a graph look plausible. Needles and tubing use the
Poiseuille diameter-to-the-fourth relationship. The blood viscosity relation is
an explicit synthetic high-shear suspension law, dependent on hematocrit,
temperature and protein concentration; it is not a validated rheology fit.

A pressure-limited pump drives the circuit. Arterial pressure is measured before
the pump and can be negative. Venous pressure is set by return-path resistance and
access pressure. TMP includes blood-side and dialysate-side pressures. Local
filtration uses blood pressure minus dialysate pressure minus oncotic pressure.

A reduced volumetric controller solves the dialysate pressure needed for the
requested gross UF. Higher venous pressure can change the necessary dialysate
pressure without changing the achieved net UF. If the configured hematocrit,
plasma-filtration fraction or pressure bounds prevent delivery, substitution is
reduced first; unattainable net UF is reported separately. The UI distinguishes
requested and measured flow and displays the limiting condition. Sustained net-UF
shortfall remains detectable by the independent fluid-balance protection.

## Where conductivity and temperature come from

`physical.fluid` defines two separate sources: a finite acid-concentrate volume
and finite dry sodium bicarbonate. Installation flags, dosing fractions and a
maximum bicarbonate dissolution rate affect preparation. Depletion affects
composition and the supply/quality protections. Water completes the mixing flow.
The acid profile specifies the tracked ionic composition; it does not simulate
acid dissociation or carbonate/CO2 reaction kinetics.

Conductivity sums the contributions of Na, K, Cl, bicarbonate and Ca, applies a
configurable non-ideal-mixture factor and a temperature coefficient. The reported
conductivity is compensated to 25 C; raw temperature-dependent conductivity is
also available. Ion-mobility coefficients and the correction factor are synthetic
model inputs requiring calibration, not a validated assay of fluid composition.

The heater has maximum power in watts, thermal capacity, ambient heat loss and
incoming-fluid heat demand. Feed-forward plus proportional feedback controls its
power. Temperature follows an energy balance; inadequate heater power cannot
instantaneously achieve the setpoint. The two substitution ultrafilters and their
existing integrity/quality protections remain in the fluid path.

## What the evidence demonstrates

Tests check needle scaling, pressure/viscosity response, segmented cell flux and
UF equations, 648 operating points, pump/filtration limits, heater saturation,
source depletion, patient hemoconcentration/refill and RBC/protein/water/solute
conservation through complete HD and HDF cycles. Real-process tests also verify
retained trajectories independently. Local in-process results and hosted results
are recorded separately; passing software tests is not clinical validation.

Important remaining model boundaries: segment hydraulics are quasi-steady,
forward filtration only; the dialysate-side pressure field is reduced, not a full
valve/balance-chamber network. The extracorporeal solute and cell inventories use
a mixed pool, so segmented hematocrit is a steady-flow estimate, not a plug-flow
startup prediction. Protein deposition, clotting, hemolysis, red-cell deformation,
backfiltration, CO2 chemistry and disinfection efficacy are not modeled.

## Equations and sources

The model uses `mu = 1.2 exp(-0.025(T-37)+0.04(Cp-7))/(1-Hct)^2.5`
(mPa s), and `pi = 2.1 Cp + 0.16 Cp^2 + 0.009 Cp^3` (mmHg, Cp in g/dL).
Each segment obeys `UF_i = max(0, KUF/12 * (Pb_i-Pd_i-pi_i))`.
The first viscosity relation is a chosen synthetic constitutive law. The oncotic
polynomial is a commonly used approximation; the papers below inform model
structure and limitations, and do not calibrate this implementation:

- [Mathematical model to characterize internal filtration (2005)](https://pubmed.ncbi.nlm.nih.gov/15876825/): axial blocks with local blood properties.
- [Determinants of Hemodialysis Performance (2019)](https://pmc.ncbi.nlm.nih.gov/articles/PMC8673592/): coupled filtration, hematocrit and oncotic effects.
- [Correlation of standardized serum protein determinations with calculated and measured colloid osmotic pressure (1983)](https://pubmed.ncbi.nlm.nih.gov/6881091/): polynomial approximation and its empirical assessment.
