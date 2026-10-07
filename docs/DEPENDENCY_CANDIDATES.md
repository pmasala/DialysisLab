# Dependency candidates

This is a design shortlist, not an installed-dependency inventory or release SBOM. Exact versions, checksums, enabled features, and transitive dependencies remain unselected.

| Component | Candidate | Upstream license summary | Decision |
| --- | --- | --- | --- |
| device-ui | LVGL core | MIT | Selected framework; exact artifact pending review/pinning. |
| device-ui desktop backend | SDL2 | zlib | Proposed, matching the currently inspected LVGL integration. |
| sim-console | Dear ImGui | MIT | Proposed for the external engineering tool. |
| sim-console plots | ImPlot | MIT | Proposed. |
| sim-console backend | SDL | zlib | Version to be selected with compatible backends. |
| Patient numerical solver | Not selected | Not reviewed | Select after numerical requirements are established. |
| Interprocess transport | Not selected | Not reviewed | Select after timing, failure, and message contracts are defined. |
| Fonts/icons/assets | Not selected | Not reviewed | Review each asset independently. |

Upstream references are listed in ARCHITECTURE.md. These summaries do not establish a complete dependency license assessment. Commercial LVGL editor tooling and separately licensed test extensions are not implied by selection of the corresponding open-source core.
