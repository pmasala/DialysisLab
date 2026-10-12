# Inspect a treatment as it evolves

Start the usual guided session. The default scenario now runs the dynamic model.
The **Extracorporeal** tab shows the two chamber levels. The **Hydraulics** tab
shows balancing displacement, valve phase and the UF pump. **Trends** adds chamber
levels, effluent flow and UF-pump flow. The external experiment console exposes
each blood and dialysate compartment, including its solute concentrations.

![Generic hydraulic circuit](images/physical-circuit.svg)

The patient settings still belong in the scenario file. Initial hematocrit is
never a device control. Blood-pump and active substitution setpoints remain
editable during treatment, through the existing confirmation workflow.

## What changes when a pump starts

The pump approaches its commanded flow with a finite response time. The arterial
chamber can temporarily supply more fluid to the pump than the needle draws from
the patient. Its liquid level falls and the gas pocket expands. On the return
side, the venous chamber can briefly accumulate fluid. Consequently, pump flow,
flow drawn from the patient and flow returned to the patient need not be equal.
Their difference is recorded as circuit storage, not lost fluid.

Each chamber has a liquid volume, a gas inventory and a pressure. The pneumatic
level controller adds or removes gas at a bounded rate. It cannot reset the liquid
level. Independent protection reads the level signals and raises the existing air
alarm below 15% or above 90%; these are synthetic engineering thresholds.
Stopping or isolating the circuit freezes these inventories and closes the modeled
paths. Restarting continues from those inventories.

## Where the blood and solutes travel

There are 16 blood compartments: arterial tubing, arterial chamber, 12 dialyzer
segments, venous chamber and venous tubing. Cells, proteins and each tracked solute
move between neighbours. A change at the patient or saline inlet therefore reaches
the filter and return line progressively.

PRE substitution enters the first dialyzer segment. POST substitution enters the
venous chamber, after the filter. Neither route adds fluid directly to the patient
without passing through its modeled downstream compartments. RBC and proteins stay
on the blood side; UF removes water and sieved solutes. The local retained Hct and
protein concentration feed the next hydraulic step's viscosity and oncotic pressure.
The model uses an explicit one-tick coupling between transport and hydraulics.

Twelve dialysate cells flow in the opposite direction. Each exchanges solutes with
its corresponding blood segment. Effluent contains what entered with fresh fluid
plus what crossed from blood, minus the inventory still inside the dialyzer.
Separate water and solute ledgers check this balance.

## How net fluid removal is controlled

The blood hydraulics calculates the pressure associated with a feasible UF target.
That pressure is a controller setpoint, not the applied physical pressure.

A feed pump has a response time. The generic duplex balancing unit delivers matched
fresh and spent volumes through alternating valves; each changeover holds flow for
30 ms. A separate, limited UF pump withdraws extra effluent. Pressure feedback is
filtered and controls that pump. Fluid accumulating in the compliant dialysate
circuit changes its pressure, which in turn changes membrane filtration. The
membrane pressure and water balance are solved together at each step.

This creates a real transient: actual UF can differ from its target after startup
or a setpoint change. The independent net-volume protection remains active. If no
bounded solution exists, the model isolates the membrane and reports a limitation;
it does not manufacture the requested water removal.

## Configure an experiment

`physical.dynamics` configures the two initial air volumes, level-control gain,
air-actuator capacity, dialysate compliance and initial volume, pump and pressure
sensor response times, UF-pump capacity and balancing-chamber displacement.
`physical.blood` still defines liquid priming volumes and geometry. The scenario's
`patient.prime_mL` must equal their sum. Runtime storage may be positive or negative;
individual compartment volumes must always remain positive.

A smaller needle increases the pressure drop. A slower pneumatic actuator produces
larger level excursions. A slower UF pump produces a longer fluid-removal transient.
Use the external inspector to compare setpoints, flows, levels, inventories and
conservation residuals. All those measurements are retained in the trajectory.

## Compare with public reference measurements

Run this from the repository root:

```bash
python3 tools/calibrate_models.py --output /tmp/dialysis-reference-fit --profile reference-fx80
```

The output contains a comparison report and an optional ready-to-run `scenario.json`.
Use a new output directory for each experiment. The source register is
[references/dialyzer_benchmarks.json](../references/dialyzer_benchmarks.json).

The tool fits effective urea KoA at blood flow 300 mL/min and checks the separate
400 mL/min point. It uses three publicly reported dialyzer profiles. Their stated
priming volumes and KUF are converted explicitly; KUF in mL/h/mmHg is divided by 60.
The fitted KoA belongs to this 12-cell numerical model, so it differs from a
manufacturer's reported KoA and must be refitted after changing discretization.
Only urea KoA, blood volume and KUF change in the exported scenario. The other
solute coefficients and all patient/controller parameters remain synthetic.

The reference source specifies flow and temperature but does not fully describe
test-fluid composition or measurement uncertainty for the selected clearance
points. Thus this is a **conditional in-vitro comparison**, not validated device
or patient equivalence. The report lists parameters still needing independent
bench measurements. No such measurements or treatment datasets have been supplied
in this session; the project does not invent them.

## Numerical and interface details

- Chamber pressure follows `(760 + P) * Vgas = gas_inventory`, with gauge pressure
  in mmHg. An implicit liquid-continuity solve couples this to needle/tube resistance.
- Dialysate storage is `C * (P - P_initial)`; its change equals feed plus membrane
  UF minus effluent. The matched part of effluent follows balancing displacement.
- Implicit finite-volume balances transport solutes, RBC and proteins. The default
  transport grid has 16 blood and 12 dialysate cells. Solute concentrations retain
  the project's apparent whole-compartment convention; intracellular RBC solute
  partition and membrane kinetics are not added by this change.
- `DYNAMICS10` configures the model on the administrator channel. `INVENTORY10`
  supplies timestamped local blood properties from the patient service. `OBS10`
  exposes measured levels and actuator states to control, protection and device UI.
- Distributed patient replies have an explicit 32 KiB limit. Other RPC frames keep
  their 4 KiB limit. The external console retains at most 300 samples and 1024
  numeric metrics per sample, preserving the previous sample-times-metric budget.
- Tests check whole-system water, RBC, protein and six-solute conservation, as well
  as a separate dialysate-solute ledger. They also check transit delay, step responses,
  isolation, malformed transactions and bounded message handling.

The balancing mechanism is an ideal displacement coupling with a modeled valve
changeover delay, not a manufacturer's mechanical assembly. Liquid inertia and
pressure-wave propagation are still omitted. Filtration is forward-only; the model
does not add backfiltration, clotting, hemolysis, protein deposition, acid/CO2 chemistry
or a validated disinfection-efficacy model. These boundaries remain visible because
adding dynamic inventories does not establish those separate physiological effects.
