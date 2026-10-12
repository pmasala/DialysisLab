# Terms, units and conventions

| Term | Meaning in this simulator |
| --- | --- |
| HD | Haemodialysis: blood and dialysate exchange solutes through a membrane, with prescribed fluid removal. |
| HDF PRE / POST | Haemodiafiltration with substitution entering before the filter / into the venous chamber after the filter. |
| UF | Ultrafiltration: water crossing the membrane. Gross UF and prescribed net removal are different quantities. |
| Net meter | Cumulative gross UF minus substitution. It is not the patient's measured weight change. |
| Priming | Flushing the isolated modeled circuit with external fluid to a volume target. It is not proof that real air was removed. |
| Rinseback / return | Saline-driven return of circuit contents to the patient model, with a delivered-volume endpoint. |
| Dialysate | Fluid on the other side of the dialyzer membrane. Substitution fluid enters the blood path instead. |
| TMP | Transmembrane pressure: a reported blood-side versus dialysate-side pressure difference; oncotic pressure is handled separately in filtration. |
| Hct | Hematocrit: red-cell volume divided by whole blood-compartment volume. |
| Cp | Protein concentration per plasma volume, expressed in g/dL. |
| KoA | Effective solute transfer conductance, mL/min. The fitted coefficient depends on the numerical discretization. |
| KUF | Water permeability coefficient, mL/min/mmHg in code. Catalogue mL/h/mmHg values must be divided by 60. |
| Compliance | Stored-volume change per pressure change, mL/mmHg. |
| Gauge pressure | Pressure relative to the chosen ambient reference. Chamber gas equations convert to absolute pressure. |
| Observation | Modeled sensor sample with validity, sequence and virtual timestamp. |
| Truth | Internal simulation state available to experiment tools, not an extra device sensor. |
| Intent | Requested or confirmed operation that has not necessarily taken effect. |
| Latch | Retained protective restriction; acknowledgement does not clear it. |
| RPC | Request/reply exchange between processes over a local Unix socket. |
| Virtual time | Integer milliseconds used by equations and phase progression. Wall time governs transport deadlines and liveness. |
| Oracle | Independently justified calculation or observation used to decide whether a test passed. |
| SBOM | Software bill of materials: identified dependencies, versions and relationships. |
| Verification / validation | Evidence that specified behavior is implemented / evidence of suitability for the declared use. Neither means certification. |

Flows are mL/min, volumes mL, pressures mmHg, temperature degrees Celsius and
conductivity mS/cm. Solutes are mmol/L in the fixed order urea, sodium, potassium,
chloride, bicarbonate, calcium. Solute inventories are mmol: multiply concentration
by volume and divide by 1000. The model's apparent whole-compartment concentrations
do not represent a resolved red-cell intracellular chemistry model.

One step of `dt_ms` milliseconds is `dt_ms / 60000` minutes. A water-volume change
of 1000 mL corresponds to 1 kg in the water-only weight model. These unit conversions
are exact conventions; physiological accuracy is a separate question.
