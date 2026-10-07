# Dependency policy

Status: adopted project policy, 7 October 2026.

## Principle

**Prefer MIT, BSD, Apache-2.0, or zlib application libraries, and review exceptions explicitly.**

Use exact SPDX license identifiers when recording dependencies. For BSD licenses, record the exact variant; do not treat the word "BSD" as a sufficient license finding. A preferred license is not automatic approval: its terms, provenance, transitive dependencies, and compatibility with the eventual project license must still be checked.

## Scope

Apply this policy to device software, simulation services, external tools, and their direct and transitive application dependencies. Include optional plugins, codecs, generated runtimes, bundled fonts, icons, example assets, and copied code.

Track build/test tools and container operating-system packages separately. They can have different licenses from application libraries. The goal is a preference for permissively licensed application dependencies, not a claim that the entire Linux image contains only permissively licensed software. Distribution obligations still apply to shipped system packages and images.

## Before introducing or updating a dependency

1. State its purpose, consuming component, and whether it is needed at build time, test time, or runtime.
2. Record its official source, exact version/commit, artifact integrity information where available, and the license of that selected artifact.
3. Review relevant transitive dependencies, optional features, bundled assets, and separate tooling licenses. Disable unnecessary features.
4. Assess technical suitability, maintenance status, known issues, security concerns, and the effect of failure on the consuming component.
5. Record redistribution obligations: license texts, copyright notices, attribution/NOTICE content, source delivery, relinking, or installation information where applicable.
6. Obtain explicit maintainer review before merging an exception. Use docs/templates/DEPENDENCY_EXCEPTION.md. Routine preferred-license additions can be reviewed through the normal change process.

Prefer minimal dependencies in control and protection. Keep GUI frameworks out of those components. Reuse shared protocol definitions deliberately; assess the common failure modes introduced by shared executable logic.

## Exceptions

Any application dependency outside the preferred families, with unknown/ambiguous terms, or with additional restrictions requires a documented decision before adoption. This includes copyleft, source-available, commercial-only, and custom-licensed components. Their presence is not automatically prohibited; approval must identify the exact artifact, reason, alternatives, distribution implications, owner, and review triggers.

Approval is limited to the reviewed version, features, and use. Review it again if those change, the project license changes, or a material licensing/security issue arises. Do not assume an editor, testing extension, or asset pack shares the core library's license.

## Reproducible releases and evidence

- Pin releases or immutable commits and container base-image digests; avoid floating branches/tags in release builds.
- Maintain a dependency inventory and a Software Bill of Materials for released application/container artifacts.
- Ship required notices and license texts; do not describe a source-only inventory as a complete shipped-image inventory.
- Link risk-relevant third-party components to requirements, known anomalies, and verification evidence. Where IEC 62304 terminology applies, record the rationale for software of unknown provenance classification and handling.
- Plan automated checks for unpinned dependencies, unrecorded licenses, missing notices, and unreviewed exceptions. These checks are requirements for future implementation; this documentation package does not implement them.

## Initial decisions

- Device UI: LVGL open-source core, with UI definitions written in C/C++. A commercial visual editor is not a required dependency.
- Desktop backend: select the SDL version supported by the pinned LVGL version. Do not assume SDL3 compatibility merely because another UI library supports it.
- External simulation console: Dear ImGui and ImPlot are candidates, subject to exact-version and transitive-dependency review.
- The project uses the MIT license established in LICENSE. This does not change the separate licenses or redistribution conditions of dependencies, standards or other third-party material.
