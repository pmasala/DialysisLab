# Trama animated synoptic change

Change base: `b7c122f552e33d9aabe2f858bdbe67a2ed41c652` (2026-10-15).
Source of need: maintainer conversation requesting detailed machine-like components,
flow-dependent animation, filled icons with labels, central overview and touch/mouse layouts.
This is simulator presentation, not numerical verification or clinical validation.

## Requirements recorded before implementation

| ID | Requirement and proposed acceptance check |
|---|---|
| SYN-REQ-001 | Treatment home shall show a large simplified external dialyzer and extracorporeal circuit with directional flow and explicit HD / HDF PRE / HDF POST routing. Roller pumps, chamber detail, containers and full plumbing shall be available in dedicated Blood circuit and Hydraulics tabs. Render each mode and assert active branches and view allocation. |
| SYN-REQ-002 | Motion shall use current valid observed/model telemetry, never prescribed flow. Zero flow freezes phase; stale/invalid telemetry freezes motion and displays its status, without portraying unknown as zero. Changing flow preserves phase. Unit checks exercise zero, restart, rate changes and loss/recovery of freshness. |
| SYN-REQ-003 | Pump activity and fluid passage shall be distinguished. Concentrate drive and delivered liquid require separate versioned observations; older observations show unavailable fields. No mechanical RPM shall be claimed. Test C++/Python round trips and a dry-line fixture. |
| SYN-REQ-004 | Dialysate traversal, bypass and unknown route shall be distinguished with labels and valve/path geometry. Motion in a bypass shall not imply membrane traversal. Test bypass with positive feed and zero/unknown feed. |
| SYN-REQ-005 | Phase progress, phase/session time, net UF and substitution totals versus explicitly labelled current-prescription goals shall remain visible on home. Totals come from authoritative meters and survive pause/resume; no UI integration or invented target history. Test paused totals, HD, changed prescriptions and unavailable observations. |
| SYN-REQ-006 | Filled icons shall accompany text on navigation and actions. Guided controls shall have at least 48 logical pixels height; STOP shall remain visible outside scrollable content. Reflow shall support 800x890, 1100x890 and 1440x1000 without scaling hit targets. Test bounds, non-overlap and real LVGL rendering. |
| SYN-REQ-007 | Chamber fractions shall use measured fractions. Container bars shall be explicitly relative to first observed session inventory, with absolute quantities/units; missing baselines and unavailable telemetry shall not show fabricated capacity. Session changes reset presentation history. Test inventory depletion, stale data and reset. |
| SYN-REQ-008 | A reduced-motion toggle shall freeze decorative motion without hiding numerical values, route, status or progress. Motion limits shall be visible and documented. Verify freeze and continued value updates. |
| SYN-REQ-009 | The rendered dialysate outlet and bypass shall remain outside the venous chamber and lead only to the effluent circuit. POST substitution shall terminate at a dedicated venous-chamber inlet, PRE before the filter; blood shall enter the chamber from above and leave below. Non-joining crossings shall have visible clearance. Check production-drawn segment endpoints and exclusion regions in HD/PRE/POST, bypass and stale captures at every supported test size. |
| SYN-REQ-010 | Home shall prioritize the filter and extracorporeal flow with a simplified overview, animated fluid-direction cues and measured acid/bicarbonate liquid, dialysate feed, drain, membrane UF and substitution quantities in mL/min. Mechanical roller motion, tanks and full valve plumbing shall be confined to the Blood circuit and Hydraulics tabs. PRE/POST destination, bypass, zero/unknown flow, freshness and reduced motion remain explicit. Test distinct render modes, actual tab events, source-to-value mapping and simplified topology at all three fixture sizes. |

## Progressive detail requested on 2026-10-16

The maintainer found the home circuit too complex. SYN-REQ-010 refines the visual
allocation of SYN-REQ-001: the realistic mechanical assembly belongs in detail
tabs; home retains a simplified external filter, blood path and venous chamber.
The existing Blood circuit and Hydraulics tabs are the dedicated synoptic views,
with the same persistent phase/time/meters and STOP outside their content.
Concentrates feed a labeled preparation boundary, never the blood side. Only the
selected PRE or POST infusion connection is shown on home; HD shows infusion off.

Quantities are observed liquid outputs (not concentrate drive), observed dialysate
feed and drain, membrane UF (`q.blood.uf`), and substitution (`q.replacement`).
UF-pump flow remains separately named in Hydraulics. Drain must never be inferred
as feed plus UF: transient storage can change that equality. No new integration,
sensor, controller or physical equation is introduced. Visual flow speed keeps
the existing declared clamps and unavailable signals display `--`.

Proposed acceptance before implementation: home draws no mechanical rollers,
valves or stock containers; each requested quantity is independently mapped to
telemetry with units and availability; HD/PRE/POST and bypass endpoints remain
unambiguous; existing touch sizes and permanent meters still pass. Detail-tab
navigation must be exercised through real LVGL pointer events. This is an
engineering candidate, not independent usability acceptance.

Execution: the final overview report records 13 passing UI/guided/protocol checks,
including actual SDL finger navigation even before the first telemetry sample.
Home draws zero mechanical pumps, Blood circuit one, and Hydraulics five. The
quantity fixture deliberately separates feed 500, drain 543, membrane UF 65 and
UF-pump 72 mL/min. Final captures were checked after moving the bypass line below
the UF value. Earlier successful captures and development defects remain history.

## Topology correction requested on 2026-10-16

The maintainer identified that the spent-dialysate line crossed the venous chamber
silhouette and that the POST connection was ambiguous in the demonstration video.
This is a presentation defect under SYN-REQ-009 (HAZ-004, HAZ-005), not evidence of
a fluid connection in the solver. The correction must show distinct ports and
bridges at non-joining crossings. Proposed geometric acceptance is exact endpoint
coincidence for intended ports and no dialysate-segment intersection with the closed
venous-chamber rectangle; captures must confirm the bridges remain legible.

The dynamic implementation already adds POST liquid and solute to compartment 14,
the venous chamber, before compartment 15 and patient return
(`python/dialysislab/distributed.py`). Its hydraulic continuity includes substitution
in the chamber inflow (`src/dynamics.hpp`). The chamber is a well-mixed numerical
volume with a gas pocket and level control. It does not model entrained-bubble
transport, capture efficiency, degassing or a calibrated air detector. Therefore a
correct inlet and level-alarm regression cannot establish bubble-trap performance
or predict mixing-induced air alarms. Those need separately specified gas/liquid
physics, detection thresholds and bench evidence. Legacy lumped patient mode still
uses its documented direct-body POST approximation; this UI fix does not upgrade it.

The intended POST inlet is consistent with the manufacturer's schematic in
[Fresenius Medical Care, Annual Medical Report 2024, Figure 2](https://freseniusmedicalcare.com/content/dam/fresenius-medical-care/global/en/04_media/pdf/AMR_2024_Full_Final.pdf).
This reference supports schematic topology only, not model validation.
Status: implemented; the source-bound topology report records execution. Independent acceptance remains open.
The model cross-check uses a 1 mL POST pulse containing a synthetic 1 mmol/L
tracer, zero initial tracer and zero upstream transport/UF/membrane exchange.
For fixed chamber volume V, implicit well-mixed concentration must be 1/(V+1)
mmol/L, then pass through the venous-tube balance. Proposed algebraic tolerance
is 1e-12 mmol/L (round-off for this small isolated balance); upstream tracer stays
zero and whole-system residual remains below the existing 1e-6 mmol criterion.

Acceptance limits are proposed engineering checks, not independently approved usability
criteria. The 48 px target must still be assessed on actual display density and touch
hardware. Render fixtures do not establish task success or clinical usability.

## Design constraints

- Atlantico palette: night blue `#142D4E`, turquoise `#087F8C`, ice `#EFF6F8`,
  aqua `#E0F1F4`. Reserve red/amber for protective status; identify circuits by labels.
- Motion is a flow/activity cue, not particle transport, elapsed simulation time or RPM.
  Use linear flow scaling with a declared lower/upper visual clamp. Display actual
  numbers independently. Freeze stale/invalid data; never extrapolate accumulators.
- Retain the Trama observed/prescribed distinction, existing eligibility and confirmations.
- Own LVGL vector primitives; no added third-party icon/font dependency.
- This change cannot close `CLOSE-NUM-01`. Numerical model accuracy, experimental
  validation and clinical validation remain separate obligations.

## Verification status

Requirements specified and implemented. Thirteen selected UI/guided/protocol tests
and eighteen preparation regression tests executed successfully on the input hashes
in the [verification record](../testing/SYNOPTIC.md). Independent acceptance remains
open; Unix-socket integration is blocked locally. No prior pass is inherited.

## Implemented presentation rules

`flow_motion.hpp` owns display phases; `animated_synoptic.hpp` draws original LVGL
vectors. `vector.hpp` supplies filled button icons. `guided.hpp` lays out the
surrounding observed/reference tiles, permanent meters and guarded actions.
`device_ui.cpp` handles SDL resize, mouse wheel and single-finger input. Extra
fingers are ignored and focus loss releases the pointer. The legacy screen keeps
its original layout; the new responsive contract applies to guided operation.

For positive flow, display speed is `clamp(Q / Qref, 0.12, 1.5)` cycles per wall
second; at zero it is exactly zero. Reference rates (mL/min) are blood 300,
dialysate 500, concentrate drive/liquid 30, UF pump and membrane UF 10, observed drain 500 and substitution 60.
Consequently speed ratios are proportional only between the clamps. The live
legend declares the range and explicitly says this is not RPM. Phase increments
are capped at 100 ms per frame, are accumulated rather than recomputed from
absolute time, and do not catch up across stale intervals. Simulation pacing
therefore changes observed values, not a claimed particle transit time.

OBS12 preserves the OBS11 prefix and appends acid/bicarbonate model drive,
acid/bicarbonate sensed liquid outlet flow, and concentrate-sensor freshness.
The existing preparation guard accepts sensor age at most 0.5 s. These delayed,
filtered liquid observations differ from model drive; a dry line can have drive
with zero liquid. Old formats remain accepted and expose unavailable concentrate
fields. No controller, solver equation, protection threshold or actuator command
is changed. Generic pump rotation is a flow activity cue: mechanical RPM is not
modeled. Dialysate routing uses observed bypass, never the prescribed state.

Blood and dialysate paths remain separate at the opaque dialyzer shell. Motion is
shown in connectors; valve barriers and text distinguish bypass from traversal.
HDF PRE and POST use the observed infusion route. The hydraulic detail retains thin inactive paths for
context; home shows only the selected infusion branch. Unknown paths are dashed. Detailed geometry is an educational diagram,
not a manufacturer drawing or a physical hydraulic assembly specification.

Container bars in Hydraulics are remaining quantity divided by the first valid session reading,
clamped to [0,1]. Absolute acid mL and bicarbonate g stay visible. This is neither
nominal container capacity nor an estimate of remaining treatment time. Fractions
in the blood chambers come directly from dynamic observations. Session change
clears visual baselines/history; pause and reconnection to the same service epochs do not. No displayed volume is integrated
in the UI. Net UF = gross UF meter minus substitution meter; it is not weight loss.
Targets are explicitly labelled **current Rx goal** (current rate times total
prescribed treatment duration). They can change after prescription edits; historical
prescription integration and independently editable volume targets are not claimed.
HD displays substitution off. Bar fill clips at 100%; the absolute number can exceed
the goal. Stale/invalid totals show `--` and a muted, unavailable bar.

At widths >=1050 px, six Trama tiles surround the central circuit. Below that
breakpoint they follow it in a scrollable home area. Native supported bounds are
800–2560 by 890–1600 logical pixels. Phase, session time, both volume meters, alarms
and STOP remain outside that scroll. Navigation/actions use 48–52 px high targets,
with filled icons and text. The fixed eight-step strip is replaced by the current
phase heading and percentage; detailed lifecycle transitions are unchanged.
