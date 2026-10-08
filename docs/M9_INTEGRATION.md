# M9 integrated acceptance and source package

Frozen phase base: `eb290dee95ac078ca3485fe1088161558dccbe59`.
M8 implementation and local regressions are verified. Its corrected hosted log
recovery and additional long Docker regressions run concurrently; retain their
actual outcomes before final closure. M9 has exactly one automatic review after
its candidate commit, covering the whole diff against this base.

## Requirements, risks and predeclared acceptance

| ID | Behavior and acceptance | Risks |
| --- | --- | --- |
| M9-REQ-001 | Run the 18-case Cartesian matrix below twice natively and twice in Compose; exact same-build trajectory hashes, no unexpected alarms, complete lifecycle, independent water/six-species residuals at most 1e-6 mL/mmol. Re-run existing fault fixtures with declared response bounds. | HAZ-002/003/004/006 |
| M9-REQ-002 | Two native/two Compose 100000-tick sustained HDF runs; sequence 0..99999, more than 99000 treatment ticks, gross UF above 100000 mL, positive compartments, the same conservation/hash criteria. Actual runner RSS at most 64 MiB inside the unchanged 128 MiB container; no OOM. | HAZ-003/004 |
| M9-REQ-003 | Actual LVGL device UI and ImGui console share authoritative role services. Verify virtual pause and stale data, epoch change on replay, scheduled request restrictions, UI STOP while paused with observed plant stop and aborted retained evidence within 2 wall seconds locally / 5 seconds including Docker CLI observation. Headless and WSLg/X11 deployments must execute real widgets. | HAZ-001/002/004/005 |
| M9-REQ-004 | Build two byte-identical explicit-allowlist source archives; unpack, build and execute the real tests/widgets from packaged sources. Record archive/source/toolchain identities without inventing a Git revision for an unpacked tree. | HAZ-001/004 |
| M9-REQ-005 | Publish usable Linux/WSL2 commands, model limits, dependency/anomaly records and requirement/design/risk/test evidence links. Preserve all outstanding standards, calibration and human release obligations; recover corrected hosted CI bytes and verify every registered digest. | HAZ-001–006 |

## Matrix and numerical assumptions

The short matrix combines HD, HDF_PRE and HDF_POST; synthetic baseline, overload
and electrolyte imbalance patients; and two explicitly synthetic dialyzers.
Use the existing M5 lifecycle calendar (400 ticks, 100 ms). Body profiles retain
their declared water/species values; extracorporeal prime is 20 mL for this compact
lifecycle fixture. Transport inlet composition equals initial extracellular
composition. All full configurations and seed 42 are persisted, never inferred
from a profile name.

Small profile uses M5's R=1 mmHg min/mL, KUF=1 mL/min/mmHg. Large uses the existing
doubled KoA values, R=0.5 and KUF=0.8, named `synthetic-integration-large`. The latter
resistance gives this fixture enough transmembrane pressure/UF capacity for replacement
plus net removal. These are demonstration parameters, not commercial specifications,
clinical prescriptions or calibrated validity ranges. The hydraulic solver and
transport equations remain unchanged; their documented limits still apply.

Long HDF_POST uses 100000 ticks of 1000 ms, blood demand 300 mL/min, net UF 5,
replacement demand 100, R=1/KUF=1 and baseline body water 40000 mL. PRIME at 4,
CONFIGURE at 90, START at 94, FINISH at 99990, CLEAN at 99994. It tests roughly
27.8 virtual hours as a numerical stress case, not validated treatment duration.
Expected net removal is approximately 8325 mL, separately measured from gross UF,
replacement and circuit storage. No tolerance or protective threshold is widened.

## Integration decisions and execution

1. Preserve existing contracts; monitor the existing scheduled-control CHECK7
   during a broker pause so a device STOP is observed without advancing virtual
   time or requiring the console to resume. Communication loss uses terminal HALT.
2. Extend the real Compose console harness to optionally launch the LVGL device
   client at the same time, retaining both transcripts/captures and failed results.
3. Add matrix and long-run execution with incremental verification and optional
   lossless gzip storage of completed owned trajectories. Verify decompressed
   byte hashes before removing raw duplicates; retain explicit recovery commands.
4. Run full regressions, actual deployment matrix, graphical workflows and package
   rebuild; record findings. Commit candidate, invoke the sole read-only review,
   fix applicable findings, regress and publish the branch without rewriting it.

Compressed trajectory storage is an archival wrapper around unchanged JSONL v1;
restore with `gzip -dc trajectory.jsonl.gz > trajectory.jsonl` before existing
readers. Process-interruption recovery is not power-loss durability. Calibration,
model validation, sterile-fluid claims and standards conformity remain excluded.

Preliminary fixture finding M9-V2: the first proposed large KUF=2 was rejected
by the existing supported maximum 1 before simulation. Keep that input bound.
Use the existing large KUF=0.8 and explicit synthetic R=0.5 instead, producing
sufficient UF head while retaining lower resistance/doubled KoA versus small.
The first failed matrix report remains retained; no failed acceptance is counted.
