# CI tooling assessment

The workflow uses system Git on an identified GitHub Ubuntu 24.04 hosted runner,
with HTTPS verification and an exact `GITHUB_SHA` comparison before checkout.
Only this public repository is accepted; no token, persisted credentials, LFS,
submodule, cache/upload action, pull_request_target or workflow_run is used.
Git (GPL-2.0), compiler, Python and runner OS are build/test tools, separately
inventoried under DEPENDENCY_POLICY.md; they are not claimed to be permissive
application libraries. Actual versions are retained per job. The hosted runner
image can evolve, so reproducible runtime builds use the pinned Docker profile.

## Candidates inspected and not adopted

`actions/checkout` 7.0.1, commit
`3d3c42e5aac5ba805825da76410c181273ba90b1`, has MIT core and 24 runtime entries
(21 MIT, two ISC, one Apache-2.0). Its locked undici 6.27.0 has six OSV advisory
matches; current upstream commit `f548e57e544e1ff5a4c46bf1e1b8685f8e4a348a`
retains that same lock. Avoiding this action removes that selected CI dependency;
no claim is made about the hosted runner's own Node runtime or all system Git bugs.

`actions/upload-artifact` 7.0.2, commit
`cf430e030ddbb5b0abf93d22962f4752f3646cd9`, includes buffers 0.1.1 without a license
declaration/text in its verified tarball metadata/README. It is not adopted.
No ambiguous license or dependency exception is implicitly approved.
The inspected metadata/hashes remain in local `build/m8-dependency-preparation/`.

CI reports and bounded command logs are retained in job logs/step summaries and
can be downloaded for local evidence; raw job workspaces expire. Truncated log
middles are explicitly marked with original sizes/hashes. There is no recursive
workspace upload. Public source packages use the reviewed local allowlist.

Sources: https://github.com/actions/checkout/releases/tag/v7.0.1,
https://github.com/actions/upload-artifact/releases/tag/v7.0.2,
https://github.com/nodejs/undici/security/advisories,
https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax.
