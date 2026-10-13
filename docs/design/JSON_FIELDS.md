# Patient JSON field dictionary

Document ID ICD-03; technical review candidate. Read [Wire protocol](WIRE_PROTOCOL.md)
for INIT5/ADVANCE5/PATIENT5 envelopes. This is a maintained specification checked
against `compartments.py` and `distributed.py`; it is not a generated JSON Schema.
The snapshot validator is structural; the transaction checks also enforce balances.

All arrays below are ordered, not sets. `R` means finite real; `I` integer excluding
boolean; `[6]` means urea, sodium, potassium, chloride, bicarbonate, calcium. Body
`[2]` order is extracellular, intracellular. Snapshot `[3]` adds aggregate circuit.
Unknown keys are rejected by `keys`. Optional extensions are whole objects, not
permission to omit required members. Ranges are implementation domains, not a
validated physiology envelope. Examples must retain synthetic provenance.

## INIT5: base configuration

| Key | Shape / units | Accepted domain / meaning |
| --- | --- | --- |
| id | string | synthetic-baseline, synthetic-overload, synthetic-imbalance, synthetic-custom |
| provenance | string | Exactly synthetic; this API does not accept real-patient identities |
| volume_mL | R[2], mL | Each 100..100000; sum 1000..100000; matches scenario patient_volume_mL |
| concentration_mmol_L | R[2][6], mmol/L | 0..1000; extracellular vector equals configured blood transport vector |
| exchange_mL_min | R[6], mL/min | 0..2000; intercompartment solute transfer coefficient |
| partition | R[6], dimensionless | .001..1000; equilibrium concentration ratio in reverse exchange |
| refill_mL_min | R, mL/min | 0..5000; body water redistribution coefficient; distinct from vascular refill below |
| prime_mL | R, mL | 10..1000; initial circuit water inventory |
| initial_weight_kg | R, kg | 1..300; at least total initial body water / 1000 |
| pco2_mmHg | R, mmHg | 10..100; input to illustrative pH calculation, not acid–base validation |
| external_in_mL_min, external_out_mL_min | R, mL/min | 0..100 each; configured external water sources and sinks |
| external_mmol_L | R[6], mmol/L | 0..1000; concentration of external incoming water |
| generation_mmol_min | R[6], mmol/min | 0..10; endogenous source terms |

Optional `hemodynamics` contains exactly:

| Key | Units | Domain |
| --- | --- | --- |
| initial_hematocrit | volume fraction | .1.. .6 |
| vascular_mL | mL | 1000..10000; vascular plasma volume must be less than extracellular water |
| protein_g_dL | g/dL plasma | 1..15 |
| temperature_C | C | 30..42 |
| refill_mL_min | mL/min | 0..2000; vascular refill response coefficient |

Optional `extracorporeal` requires hemodynamics and contains exactly:

| Key | Shape / units | Domain |
| --- | --- | --- |
| volumes_mL | R[16], mL | .001..1000 each; sum equals prime_mL within 1e-7 mL |
| koa_mL_min | R[6], mL/min | 0..3000; total dialyzer coefficient, divided over 12 segments |
| dialysate_volume_mL | R, mL | 1..1000 at patient initialization; outer dynamic configuration and plant require the supported intersection 50..1000 |
| dialysate_mmol_L | R[6], mmol/L | 0..1000 |

## ADVANCE5: distributed extension

The base transaction's exact keys are in ICD-01. `distributed` has these exact
members; all water transfers describe the same committed tick:

| Key | Shape / units | Domain / relation |
| --- | --- | --- |
| volumes_mL | R[16], mL | .001..1000 each; sum − prime − stored within 1e-7 mL |
| filtration_mL | R[12], mL/tick | 0..3 each; sum − uf_mL within 1e-7 mL |
| dialysate_mL_min | R, mL/min | 0..1000; fresh inlet flow |
| dialysate_storage_mL | R, mL | -initial dialysate volume+1 ..1000; current excess inventory |
| dialysate_drain_mL_min | R, mL/min | 0..2000; actual outlet flow |
| membrane_open | boolean | False disables membrane diffusion; separately enforced hydraulic filtration is the committed value |

Local outgoing blood volumes are solved successively from incoming volume,
PRE/POST sources, filtration and volume change. Reverse outgoing transfer below
-1e-8 mL is rejected. The final outlet equals return + POST + flush waste within
1e-7 mL. Dialysate volume change equals inlet + UF − drain within 1e-6 mL.
Rejection must preserve the previous accepted patient state.

## PATIENT5: mandatory base snapshot

| Key | Shape / units | Decoder domain / interpretation |
| --- | --- | --- |
| sequence | I | 0..99999; initial snapshot also uses zero, so sequence alone does not prove advancement |
| time_ms | I, ms | 0..100000000; virtual accepted endpoint |
| volume_mL | R[3], mL | 1..100000 each |
| mass_mmol | R[3][6], mmol | 0..100000 each |
| concentration_mmol_L | R[3][6], mmol/L | 0..1000+1e-9; tiny ceiling slack, never mass clipping |
| gross_uf_mL | R, mL | 0..1e9 cumulative filtration |
| external_in_mL, external_out_mL | R, mL | 0..1e9 each; cumulative configured sources/sinks |
| net_patient_loss_mL | R, mL | -100000..100000; positive means body water lost |
| weight_kg | R, kg | 0..400; initial weight adjusted for modeled body water change |
| illustrative_pH | R or null | -400..400 decoder bound; null when unavailable; not a clinical plausibility range |
| mass_residual_mmol | R[6], mmol | -1e-6..1e-6; independent whole-system solute ledger residual |
| diffusive_mmol, convective_mmol | R[6], mmol | -1e9..1e9; cumulative membrane transfers, preserve signs |
| input_mmol, output_mmol | R[6], mmol | -1e9..1e9; cumulative external solute ledger terms |

Online snapshots add `substitution_mL` (R, mL, 0..1e9) and
`substitution_mmol` (R[6], mmol, 0..1e9). Lifecycle snapshots additionally contain
`flush_in_mL`, `flush_out_mL` (R, mL, 0..1e9) and `flush_input_mmol`,
`flush_output_mmol` (R[6], mmol, 0..1e9). Flush is a separate source/waste ledger;
it must not be relabeled patient loss. Rinseback transfers saline and circuit
contents to the patient as specified by the transaction.

## PATIENT5: hemodynamics object

| Keys | Units / domain |
| --- | --- |
| hematocrit | Vascular volume fraction, 0.. .7 |
| vascular_mL | Blood volume, 1..20000 mL |
| circuit_rbc_mL, vascular_rbc_mL, lost_rbc_mL | Red-cell volumes, 0..20000 mL each |
| rbc_residual_mL | Conservation residual, -1e-6..1e-6 mL |
| protein_g_dL | Vascular protein concentration, 0..30 g/dL plasma |
| temperature_C | 30..42 C |
| refill_mL | Signed cumulative vascular refill, -10000..10000 mL |
| circuit_hematocrit | Circuit volume fraction, 0.. .8 |
| circuit_protein_g_dL | 0..40 g/dL plasma |
| protein_residual_g | Conservation residual, -1e-6..1e-6 g |
| vascular_protein_g, circuit_protein_g, lost_protein_g | Protein inventories, 0..5000 g each |

## PATIENT5: distributed object

| Key | Shape / domain |
| --- | --- |
| compartments | 16 objects in flow order: arterial_tube, arterial_chamber, filter_01…filter_12, venous_chamber, venous_tube |
| dialysate_concentration_mmol_L | R[12][6], 0..1000+1e-9 mmol/L; indices align with membrane segments; fluid flows countercurrent |
| dialysate_volume_mL | R, 1..2000 mL; current inventory, not the initialization bound |
| dialysate_input_mmol, dialysate_output_mmol, dialysate_transfer_mmol | R[6], -1e9..1e9 mmol; cumulative input, effluent and membrane transfer |
| dialysate_residual_mmol | R[6], -1e-6..1e-6 mmol; separate dialysate-side ledger |

Each compartment contains exactly `name`, `volume_mL`, `concentration_mmol_L`,
`rbc_mL`, `protein_g`, `hematocrit`, `protein_g_dL`. Bounds are .001..1000 mL,
0..1000+1e-9 mmol/L for each of six solutes, red cells 0..0.8*volume,
protein 0..5000 g, Hct 0.. .8, protein concentration 0..40 g/dL.
Names above describe actual producer order; the snapshot decoder checks the key
but does not independently enforce the name string. Order validation is therefore
an additional consumer obligation if arbitrary external snapshots are admitted.

## Interpretation and review

Internal conservation is necessary but does not calibrate clearance, viscosity,
compliance, refill or temperature response. An aggregate circuit concentration
cannot replace the 12 local membrane concentrations in the distributed solve.
Read [measurement protocol](../testing/MEASUREMENTS.md) before interpreting fitted
values. For any change to keys, bounds or order, review both producer and consumer,
update this dictionary, add negative cases and rerun the applicable interface tests.
