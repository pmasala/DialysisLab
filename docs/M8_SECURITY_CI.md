# M8 security, dependencies and continuous verification

Phase base: `4a1c366acd0050df4c744c2d1eb7d066890d5df4` (M7 corrected publication).
Status: the single M8 review is consumed; its four P2 corrections are under final verification.
Simulation-only technical controls; no clinical, regulatory or hardware-independence
claim. Existing release prerequisites remain open.

## Requirements and predeclared acceptance

| Requirement | Design and acceptance | Risks / test |
| --- | --- | --- |
| M8-REQ-001 | Separate writable control/protection device endpoint volumes; clients retain read-only access to both. Actual containers cannot replace the other producer's socket or access simulation administration from the UI. | HAZ-001/004/005; M8-TEST-001 real mount/spoofing probes and UI regressions. |
| M8-REQ-002 | Terminate native role children after abrupt owner death without automatic restart, preserve partial artifacts and report unknown outputs unless independently observed. | HAZ-002/003/004; M8-TEST-002 real broker SIGKILL and PID/record checks. |
| M8-REQ-003 | Reject duplicate, deeply nested, nonfinite, oversized and incomplete JSON/protocol input; retain fixed deadlines/resource bounds and independently enforced protection. | HAZ-001–006; M8-TEST-003 malformed/trickle/concurrency and real plant watchdog tests. |
| M8-REQ-004 | Produce versioned application SBOM plus separately identified native/container package inventories, pins, selected transitive licenses/notices and build identity. Fail integrity/license omissions rather than silently approving exceptions. | HAZ-001/004; M8-TEST-004 inventory tampering and reproducible generation. |
| M8-REQ-005 | Run available static/dependency analyses, retain exact coverage/findings/dispositions and limits. An unavailable analyzer or advisory service is BLOCKED, not a clean scan. | HAZ-001–006; M8-TEST-005 actual analyzer/advisory reports. |
| M8-REQ-006 | CI builds and exercises real processes, headless widgets, Compose, assurance and publication checks with minimal permissions and pinned assessed tools. Retain actual results separately from intentionally blocked release gates. | HAZ-001–006; M8-TEST-006 workflow checks and real hosted run when available. |

## Trust boundaries and threat assumptions

The host, kernel, Docker daemon, broker and same-UID native development account are
trusted administrators. Compromised UI/console/service processes are considered at
their container mount boundaries; local denial of service and malformed traffic
remain relevant. Control and protection share protocol code and the modeled plant;
this is not physical independence. No network listener or Docker socket is exposed.
X11 remains a trusted optional desktop boundary, unsuitable for hostile tenants.

Device producer endpoints move behind distinct owned directories/volumes while
legacy device client paths remain immutable aliases. Administrative role sockets
remain unavailable to device UI. The broker's random credential is per incarnation,
filesystem protected, never exported; restart rotates it and invalidates old clients.
No custom encryption or remote authentication is introduced for local Unix IPC.

Native children use a small Linux parent-death exec guard with parent PID recheck;
no unsafe threaded Python pre-exec callback. Process exit is resource cleanup, not
proof of observed actuator output. Plant watchdog and terminal arbitration remain
authoritative while alive. Repeated malformed clients may cause a protective stop:
availability loss is documented, not concealed by accepting unsafe inputs.

## Execution and evidence steps

1. Implement endpoint ownership, parent-death handling and bounded strict input;
   run real negative/process tests and affected numerical/UI regressions.
2. Assess selected dependency/tool artifacts, generate inventories/SBOM, execute
   available static and advisory scans with findings and coverage recorded.
3. Add minimal-permission CI and explicit publication entries; run equivalent local
   commands and actual hosted jobs if origin/runner access permits.
4. Commit candidate; invoke exactly one read-only review against the frozen base;
   disposition all findings, correct and regress without a second review.
5. Record clean build/configuration/artifact evidence, update traceability/status,
   commit/push and proceed automatically to M9 integration/package verification.

Memory limit remains 128 MiB per container; message deadlines remain wall-clock,
virtual treatment timing stays deterministic. No risk acceptance, calibrated model,
licensed-standard access or human approval is inferred from CI or AI review.

## Implemented interface migration and early findings

Deployment profile M8 preserves device DL1 v5/v6 and client paths
`device/control.sock`, `device/protection.sock`. These are immutable image aliases
of `device/<role>/service.sock`; each producer mounts only its own writable child
directory. UI and runner mount both read-only. Repeated-run supervisors own only
`device/<role>/<run-id>/service.sock` and their current-service alias. Native
fixtures use the same hierarchy but retain the documented same-UID trust boundary.
JSON accepts at most 1 MiB (DX1 additionally limits 256 KiB), depth 32 and integer
literals 128 characters; duplicate keys/nonfinite values are rejected at ingress.
No virtual-time, physical equation, threshold or wire-version change is implied.

Pre-candidate verification found and preserved one integration failure: the initial
parent-death guard rejected parent PID 1, which is valid for a container supervisor.
All four children exited 64 and the experiment aborted before any tick; artifacts
were collected successfully. Permit positive PID 1 with the same parent recheck;
re-run the actual supervised Compose workflow. This is not a weakened owner check.
Cppcheck also requested an explicit listener-role bound before array indexing;
the actual dispatcher supplies only three listeners, but the bound is now local.

## Reproducible checks and CI

```bash
python3 tools/dependency_report.py --build-dir build/gui --output build/dependencies-new --images dialysislab-m1:local dialysislab-ui:local
python3 tools/security_scan.py --output build/security-new --inventory-dir build/dependencies-new --advisories
python3 tools/ci_verify.py --output build/ci-new
python3 tools/ci_verify.py --output build/ci-new --report-only
```

Use fresh output directories. Scanner exit 1 means findings, 3 means incomplete
coverage/BLOCKED, and 0 means no matches in the declared scope, never proof of
security. Inspect the JSON, upstream references and dispositions. CI uses actual
processes/widgets/Compose, retains bounded logs and identified JSON in its job log,
and reports deliberately incomplete release gates separately. No unassessed upload
or checkout action is used; public Git fetch is checked against the event SHA.
The hosted Ubuntu toolchain is identified, while runtime builds pin the Docker
base/snapshot. Raw hosted workspaces expire; download logs for durable evidence.

An RSS regression exposed Linux `getrusage` inheriting a parent's pre-exec maximum:
a child with VmHWM 11028 KiB reported its parent's 112693248-byte high-water value.
The probe now uses per-executable `/proc/self/status` VmHWM, retains getrusage as
a separate diagnostic and keeps the unchanged 64 MiB test/128 MiB Compose budgets.
The 96 MiB-parent regression and original failing probe are retained; this does
not substitute Python allocator estimates or relax memory acceptance.

## Review corrections: evidence contract version 2

CI report schema 2 retains original bytes using `DIALYSISLAB_ARTIFACT_V2`
base64 envelopes: name, byte count, SHA-256, ordered 3072-byte chunks and end marker.
Every artifact is limited to 16 MiB; oversize/missing/changed output fails retention,
never silently truncates. Registered dependency output explicitly includes native
and per-image SBOMs, platform inventories, build records and adopted dependencies.
No recursive workspace upload is permitted. Recover downloaded job logs with:

```bash
gh run view RUN_ID --log > build/hosted-ci.log
python3 tools/ci_artifacts.py --log build/hosted-ci.log --output build/recovered-ci
```

The reader rejects traversal, duplicates, bad chunk order, length/hash mismatch
and incomplete envelopes. It preserves an unfinished `.partial` file without
presenting it as verified. Schema-1 logs cannot recover original JSON formatting.
Release checker exit 1 is exempt from software failure only with structurally
valid explicit outstanding obligations; crashes, timeouts and malformed or
contradictory results fail CI. Release approval remains separate.

Each immutable image is inspected for actual executable/module hashes, its build
record and selected dependency lock. Declared source inputs must match the checkout;
runtime Python/scenario/GUI-lock bytes must match those inputs. Stale images fail.
The image SBOM includes its own application components and links its retained build
and application SBOM; native hashes are never substituted for container binaries.
Build metadata is trusted provenance, not a signed attestation or reproducible-build
proof. Effective filesystem inventories do not clear inherited layers or licenses.
