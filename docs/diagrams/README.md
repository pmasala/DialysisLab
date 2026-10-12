# Hydraulic drawings

These original SVG drawings use engineering schematic conventions rather than
software blocks. Read them alongside [How the simulation works](../SIMULATION.md).
They are deliberately simplified; no ISO/IEC symbol-conformance claim is made.

| Drawing | Purpose |
| --- | --- |
| [Extracorporeal circuit](extracorporeal-reference.svg) | Treatment reference: blood withdrawal, pump, dialyzer, return and alternative HDF injection sites |
| [Hydraulic equivalent](hydraulic-equivalent.svg) | Actual default pressure network, including compliance and water-removal sink |
| [Fluid preparation](fluid-preparation.svg) | Mixing, heating, filter resistance and substitution delivery |
| [Dialyzer transport](dialyzer-transport.svg) | Membrane separation, diffusion and convection |

## Symbol legend

| Symbol | Meaning here |
| --- | --- |
| Solid line with arrow | Fluid connection and indicated positive flow direction |
| Filled dot | Connected junction; crossings without dots are not junctions |
| Circle with filled triangle | Pump or imposed flow source; the label defines its limits |
| Open vessel with liquid surface | Reservoir; the patient reference is a pressure boundary, not patient anatomy |
| Small circle with pointer | Pressure observation at the connected node |
| Narrow in-line rectangle, marked R | Lumped hydraulic resistance |
| Parallel plates, marked C | Lumped compliance: elastic fluid storage, using the hydraulic/electrical analogy |
| Three diminishing bars below compliance | Zero-pressure reference; no fluid drains through it |
| Diamond with dashed diagonal | Filter; modeled resistance and contamination penetration |
| Zigzag inside the preparation vessel | Heater, represented by the tank temperature equation |
| Parallel membrane lines / separator inside cartridge | Blood and dialysate remain separate; water and solutes may cross |
| Dashed purple line | Alternative HDF inlet, not a second simultaneously active substitution route |

Blood lines are red, dialysate/water lines blue and substitution lines purple.
Text labels and arrow directions also identify the streams. The compliance plates
are a numerical storage symbol, not a physical chamber design. The UF sink symbol
represents a calculation of removed water, not an additional implemented pump.

The preparation drawing illustrates fluid routing. Its spent-fluid outlet terminates
at a reference/sink symbol; it does not represent a modeled drain-pressure network.
The dialyzer drawings show opposed ports for orientation, but the solver does not
resolve countercurrent hollow-fibre geometry or axial concentration gradients.

## Match the diagrams to code

- `scenarios/machine_hdf_pre.json`: one compliant node, one dialyzer edge to node 0,
  pump placement, dialyzer parameters and predilution configuration.
- `src/circuit.hpp`: network pressure/flow calculation, finite pump head, compliance,
  ultrafiltration limits and instantaneous dialyzer transfer estimates.
- `src/online.hpp`: mixed-tank composition/temperature, filter pressure losses and
  pressure-dependent delivered substitution.
- `python/dialysislab/compartments.py`: authoritative patient/circuit water and solute balances.

Paths above are relative to the repository root. The reference schematic does not
introduce extra arterial/venous pressure states, air traps or tubing submodels.

## Edit and regenerate

Edit `tools/render_hydraulic_diagrams.py`, then run from the repository root:

```bash
python3 tools/render_hydraulic_diagrams.py
```

The generator uses only the Python standard library and writes self-contained SVG
with no fonts, images, scripts or stylesheets loaded from external locations.
Text uses the viewer's local sans-serif font. Inspect all four rendered drawings
after editing, update their registered hashes in `publication_manifest.json`, and
refresh affected current implementation hashes in `assurance/traceability.json`.
Historical test evidence must remain unchanged.
