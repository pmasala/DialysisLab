# Decisions and assumptions

| ID | Decision / reason | Limits and review trigger |
| --- | --- | --- |
| INT-001 | Start from clean `1999741`; use `feat/integrated-dialysis-roadmap`. Existing M1 corrections and evidence are retained. | Re-run affected tests as shared sources change. No M1 review rerun. |
| INT-002 | Preserve DL1 and `m1-hd-1`; extended model contracts are opt-in and explicitly versioned. | A compatibility regression blocks the dependent increment. |
| INT-003 | All new initial profiles and alarm thresholds are synthetic demonstration parameters. Use conservation laws and declared numerical approximations; do not invent commercial dialyzer specifications. | Physiological prediction requires independent calibration/validation datasets and review. |
| INT-004 | Keep standard-library numerical and service cores; select only pinned, policy-compatible GUI dependencies when required. | Record transitive libraries, fonts, notices, build/system packages and failure implications before adoption. |
| INT-005 | Preserve shared-kernel/plant/runner/protocol common-cause risks and existing release gaps. Automatic review is defect finding only. | Human risk acceptance, applicable standards, clinical/physical evidence cannot be supplied by software tests. |
| INT-006 | Use `assurance/STATUS.md` as the single progress/next-action checkpoint, this file for decisions, `MILESTONES.md` for the plan, and `assurance/REVIEWS.md` for reviews. | Re-read these checkpoints after context compaction. |

The WSL2 environment has an X11 socket (`/tmp/.X11-unix/X0`) but DISPLAY is
unset; desktop availability remains to be tested in M6. SDL development headers
are currently absent. No global environment, credential, certificate or permission
changes are authorized merely to bypass a block.
