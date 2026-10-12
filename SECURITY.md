# Security scope and maintenance

DialysisLab runs simulated patients/equipment only. It is not a deployed medical
product, remote clinical service or supported connection to real apparatus.
The current reference profile trusts the host, Docker daemon, same-UID native
account and experiment administrator. Use private local Unix endpoints, the
provided no-network/read-only/unprivileged Compose profiles, and explicitly
trusted desktop/X11 access. Do not expose these sockets over a network.

## Reporting and triage template

Report reproducible non-sensitive software defects in the repository issue tracker.
Do not put credentials, personal/clinical data, proprietary standards or exploitable
private deployment details in public issues/logs. For sensitive findings use an
already established private maintainer channel; availability of GitHub private
reporting is not assumed and this project does not invent a contact or SLA.

Record affected commit/build/dependency, configuration and entry point, observed
impact, reproduction and existing mitigations. Triage integrity/availability and
possible effects on modeled protective actions separately. Preserve original logs
without publishing secrets; link the threat, requirement and regression. Inspect
upstream fixes and exact selected versions/licenses before adoption. Patch on a
branch, test protective timing and failure paths, update inventory/SBOM/advisories,
then obtain required maintainer/risk decisions. Never relax TLS, role isolation,
release gates or evidence checks merely to install an update.

No guaranteed support lifetime, field patch deadline or product residual-risk
acceptance is established. Each evidence package describes its exact snapshot;
repeat advisory checks before reuse/distribution. Old snapshots can become unsafe.
A rollback must use a verified known snapshot and a fresh simulation session;
do not restore live actuator state or reuse stale confirmation/credential epochs.

## Available verification

`tools/dependency_report.py` checks selected pins/notices and produces application
and container SBOMs plus platform inventories. `tools/security_scan.py` runs
available Cppcheck and explicit OSV queries, retains pagination/errors and reports
findings or BLOCKED coverage. Read every finding; exit zero is not a safety claim.
See `docs/M8_SECURITY_CI.md`, `assurance/THREATS.json` and `assurance/STATUS.md`.
CI keeps identified reports in job logs/summary; raw hosted workspaces expire.
Licensed standards and secrets are excluded from public files and Docker contexts.
