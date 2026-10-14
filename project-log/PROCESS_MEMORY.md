# Project process memory

## 2026-10-14: PR #11 publication-manifest drift

Incident: commit c89e2d9, GitHub Actions run 38599749725, job 115975627047.
The hosted merge candidate was 65fe8c512ca873c79984cc7c03c65cea78e3d3db.
The trace checker rejected the implementation hashes for `publication_manifest.json`
under M8-REQ-006 and M9-REQ-004. The change added the Trama screenshot and its
provenance, while those two references still described the previous manifest.

This was an implementation/publication process error by the coding assistant.
The statement that all local structural checks passed was not valid evidence for
the published candidate. Matching an uploaded file to a local file establishes
transfer integrity only; it does not establish consistency of the evidence graph.
The checker behaved correctly. There is no evidence that a transient runner fault
caused this failure. The precise timing of the earlier local checks was not retained.

The run passed 211 native and 211 sanitizer tests, UI/console, integrated models,
Compose, dependency and package checks. The separate short HDF resource job passed.
Those results do not override the failed structural gate. Historical result records
remain unchanged, and independent approvals remain open.

Required prevention, also linked from AGENTS.md:

1. Finish source, documentation, image/provenance and allowlist edits before final checks.
2. Inspect the actual delta. Update only affected current implementation references;
   never refresh historical test evidence or all hashes to silence a failure.
3. Stage the complete candidate and record `git write-tree`. Run dependency,
   documentation, traceability, standards structure and publication gates after the
   final edit. Ensure staged and working bytes agree and no intended file is omitted.
4. A later edit invalidates the final check. Recheck before committing and compare
   committed and published tree identities with the checked tree.
   Execute commit/push only after inspecting successful gate exits; a shell newline
   does not stop a subsequent commit when the preceding check fails. Regenerate the
   test catalogue after adding a test, then rerun the complete structural sequence.
5. Report a failing gate as failing. CI now retains all inexpensive structural
   diagnostics and stops before expensive build/download work on any such failure.

Regression: `tests/test_ci.py::CITests.test_actual_manifest_drift_stops_before_build`
mutates a real manifest copy, invokes the production trace checker and checks that
CI stops with both offending requirement IDs and a recoverable diagnostic artifact.
It must not repair the mutated hash or relax the checker.
