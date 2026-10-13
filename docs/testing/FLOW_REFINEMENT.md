# Verification of dialysate flow and valve changeover

Document ID STP-FLOW; revision 1; engineering verification, approval pending.
Allocations: DYN-REQ-001, SMOD-02/07/09/13, MOD-05/06/10 and CLOSE-NUM-01.
Read the [model design](../design/MODELS.md) first. This protocol separates a
measurement-window effect from a real transport defect. Neither a small mass
residual nor decreasing numerical differences establishes physical calibration.

## What the displayed flow represents

The plant reports the volume transferred during a simulation tick divided by that
tick's duration. A balancing valve pauses transfer for 30 ms. A short observation
can therefore lie entirely inside the pause, while a longer observation includes
flow before or after it. Comparing those two averages at the same end timestamp
does not compare the same quantity.

For a common window of duration W, calculate `mean flow = sum(tick volume)/W`,
with matching time units. We use 400 ms windows, exactly divisible by every tested
step, and also compare cumulative volume from the common starting instant. The
previous raw tick averages are retained as a diagnostic, not an accuracy criterion.

## The defect and its correction

Before this correction, a full HD preparation followed by therapy at 25 ms failed
after 3900 ms of therapy: the next patient transaction raised `reverse dialysate
flow`. The [before-source witness](../../assurance/audits/flow-before.json) records
the exact previous module hash, configuration and failure. This was a software
limitation, not evidence that the simulated fluid balance was impossible.

With the supply momentarily closed, unequal local membrane filtration and compliant
storage can move fluid between dialysate cells opposite to the normal counterflow.
For face j, the transferred volume towards the outlet is reconstructed as:

`q(j) = feed volume + sum(filtration in cells j..11) - (12-j)*cell volume change`.

The implicit donor-cell scheme now selects the donor from the sign of q. It adds
`abs(q)*new donor concentration` to the donor's outgoing mass and subtracts the
same term in the receiver equation. Internal transfers therefore cancel in the
whole-dialysate mass balance. Boundary feed/drain are still validated nonnegative;
invalid patient transactions still preserve the previously accepted state.

## Reproducible procedure

Run from the repository root with Python and a C++17 compiler:

```bash
python3 tools/flow_refinement.py --output build/flow-refinement-new.json
PYTHONPATH=python:tools:tests python3 -m unittest -v test_flow_refinement
```

Use a fresh output filename. The campaign retains source hashes, configurations
through their identified scenario and explicit overrides, initial observations,
30 common-window samples per run, residual maxima and valve-event time brackets.
It executes the actual C++ plant and Python patient through a pipe harness; it does
not exercise service RPC, container limits or real equipment.

| Campaign | Setup | Decision rule |
| --- | --- | --- |
| Analytic valve displacement | Constant 500 mL/min, 30 mL chamber, 30 ms hold; three initial valve states; steps 400/200/100/50/25/10/5/1 ms | Independent pulse-train formula; volume error <=1e-8 mL and event-time error <=1e-8 s; expected sample/event counts |
| Fresh workflow | HD/PRE/POST each independently prepared at 400/200/100/50/25 ms; observe 12 s from connection | Complete all runs without alarm; water/solute residuals <=1e-6 mL/mmol; measure differences without imposing monotonicity on unequal initial states |
| Identical checkpoint | Prepare at 100 ms, execute 40 therapy ticks, save full plant and patient state, restore for each step; three modalities | Same initial observation hash; decreasing adjacent-step RMS for common-window feed/drain and cumulative volumes, with 1e-9 absolute roundoff allowance |
| Transport regression | Closed two-cell analytic examples, 100 seeded multi-cell cases, external-port rejection, actual 25 ms HD/PRE/POST runs | Both transfer directions conserve mass; bounded/uniform concentrations preserved; rejection atomic; HD witness actually contains reversed internal faces |

Coupled runs step blood demand at 4800 and 8000 ms to 220 and 300 mL/min, with
net UF 5 mL/min and active HDF substitution 40 mL/min. PRE/POST at 25 ms complete
without internal reversal in these particular scenarios. They are compatibility
checks, not additional witnesses of the reversal defect. Coupled event times are
bounded by the observation tick; only the isolated constant-rate valve test has
an exact event-time oracle.

## Results and their limits

The [source-bound report](../../assurance/audits/flow-refinement.json) contains
24 analytic valve cases and 30 coupled runs. Maximum analytic errors are
2.51e-11 mL in volume and 3.84e-13 s in switch time. Across coupled runs, maximum
water and solute residuals are below 2.59e-11 mL and 1.19e-10 mmol respectively.
The corrected fresh HD run at 25 ms accepts 11 reversed internal-face transfers.

With identical checkpoints, adjacent-step RMS differences in drain flow averaged
over 400 ms decrease as follows (mL/min):

| Mode | 400 vs 200 ms | 200 vs 100 ms | 100 vs 50 ms | 50 vs 25 ms |
| --- | ---: | ---: | ---: | ---: |
| HD | 0.717 | 0.484 | 0.301 | 0.152 |
| HDF PRE | 1.357 | 0.881 | 0.520 | 0.285 |
| HDF POST | 1.356 | 0.879 | 0.515 | 0.286 |

Common-window feed and both cumulative-volume metrics also decrease. Raw tick
averages can still differ more at smaller steps because their windows differ.
At these checkpoints the feed pump has nearly settled; its small residual
differences do not establish accuracy over every pump startup transient.

Fresh-workflow differences are not all monotonic. Preparation and state transitions
are evaluated at tick boundaries, so changing the step changes the therapy starting
state and valve phase as well as numerical integration. Those runs remain in the
report. This campaign does not establish a global error bound, an order of
convergence, accuracy at every discontinuity, or measured physical fidelity.
Concentration/UF steps, mesh/coupling sensitivity, the wider operating envelope and
approved output budgets remain open under [CLOSE-NUM-01](CLOSURE.md).
