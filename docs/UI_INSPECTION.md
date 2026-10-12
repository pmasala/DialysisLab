# Inspect a treatment visually

DialysisLab has two views of a treatment. The **device UI** displays measurements
available to the simulated machine operator. The **external console** can also
inspect the patient's internal state, individual circuit quantities and numerical
balances. Their permissions remain separate.

## Machine interface

The default interactive scenario now uses the [guided treatment screen](GUIDED_TREATMENT.md):
home follows the treatment phase; extracorporeal and hydraulic circuits have separate tabs.
The monitor described below remains available for historical scenarios without `guided`.

The LVGL monitor opens on a blood/fluid synoptic. The pump markers change orientation
with reported flow and virtual time. They are illustrative flow activity, not a
measurement of rotor speed. Invalid or missing measurements display `--`; stale
observations are labelled and animation stops.

Select **Circuits** to switch between the schematic and the measurement view.
**Next trend** opens the charts and cycles through upstream/downstream pressure,
blood flow, gross UF, substitution flow, temperature, conductivity, filter pressure,
metered UF and net metered removal. The monitor retains 120 observed samples and
shows the sensor-time interval and value range. It never labels metered removal
as patient weight loss.

Prescribing, confirmations, STOP, alarm acknowledgement and protection reset use
the existing device-service commands. Patient parameters and fault injection are
still unavailable from this interface.

## External experiment console

Start the broker and console using the [running guide](QUICKSTART.md). Open
**Experiment setup** to load and validate a preset. The Start/Pause/Resume/Stop
controls remain above the inspection pages during live operation.

- **Live circuits:** blood route and fluid preparation, measured/model values,
  active treatment mode, machine state, protective mask and patient water balance.
  Click the blood pump, dialyzer, tank or filters to set the Inspector filter.
- **Trends:** six independently selectable quantities. Each has its own units,
  autoscaled value range and a virtual-time axis. Hover to inspect a sample's
  timestamp, sequence and value. Change the time-window slider to zoom the latest
  retained history. Select pressures, flows, conductivity, temperature, weight,
  fluid loss, solutes or any other numeric field reported by the current scenario.
- **Inspector:** filter the complete set of reported numeric fields, then inspect
  state/validity/boolean fields below. Click a numeric field to place it in the
  first trend. Array indices identify individual nodes, edges, species and patient
  compartments; the on-screen legend gives the species/compartment ordering.
- **Configuration / history:** edit the scenario, inspect the full status JSON,
  replay an experiment, compare runs or export artifacts.

The schematic is a functional treatment route, not a graph-layout editor. For a
custom multi-node circuit, its individual pressures and edge flows are available
in the Inspector and plot selectors; the synoptic does not redraw its topology.
The fluid-preparation route is the implemented lumped model, not a complete
machine plumbing model.

## Open a saved trajectory without running services

```bash
build/gui/sim-console --recorded /absolute/path/to/trajectory.jsonl
```

This opens the same inspection pages in **RECORDED / READ ONLY** mode. Records are
read sequentially, one per 100 ms of wall time; plot timestamps remain their
original virtual times. **Hold recording** freezes playback so you can inspect a
sample; **Continue recording** resumes it. The file stops at EOF. This is visual
playback, distinct from replaying a simulation through the broker.

No broker client thread is started in this mode, live machine commands are not
shown, and administrative actions in the history page cannot submit a request.
A missing metric stays unavailable instead of becoming zero. Malformed or oversized
records stop playback with an error.

## Sampling and precision

The live console observes the existing broker STATUS stream (approximately 5 Hz).
It is not a recorder of every simulation tick. It retains at most 300 samples and
1024 numeric truth fields per sample; old samples are evicted. The complete run
remains in `trajectory.jsonl`. Run/epoch changes and time rollback clear history.
Disconnections and stale periods break plotted continuity. A paused experiment
freezes virtual time and pump animation, while service liveness remains separate.

Patient weight is the model's `weight_kg`; patient water loss is
`net_patient_loss_mL`. Neither is substituted with the machine's net-fluid meter.
Pump motion uses the reported flow and virtual clock, is qualitative, and does not
invent additional sensor data. The console labels internal model data explicitly.

## Typography and verification

Both interfaces use Roboto Medium from the already pinned ImGui source archive.
Its Apache-2.0 notice and selection assessment are in
[ROBOTO_NOTICE.md](dependencies/ROBOTO_NOTICE.md). No new application library was
added. The UI is not a validated clinical interface.

Current implementation verification is recorded in
[the inspection report](../assurance/evidence/ui-inspection/README.md).
That report distinguishes successful builds and recorded-data rendering from live
process/WSLg/Compose checks that still require an environment permitting Unix sockets.
