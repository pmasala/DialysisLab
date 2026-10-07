# Explained standards checklist

Revision: 7 October 2026. **Draft for substantive review; no conformity finding.**

The project owner confirmed ISO 14971 and an EU-first, US-second adaptation target. Execution remains limited to simulated patients and equipment. LVGL device operation stays separate from the external patient/experiment application. These decisions do not assign a medical-device regulatory class to the simulator or a future product.

Start with [CHECKLIST.md](CHECKLIST.md), generated from [checklist.json](checklist.json). The register contains 184 original, grouped project actions. Each entry states the source clauses, interpretation for DialysisLab, evidence expected, responsible role, proposed applicability and current completion status. All entries are open. Roles are placeholders for actual assignments; no reviewer approval has been fabricated.

## How to use this register

1. A reviewer with authorized access confirms the exact edition, wording and applicability, including individual obligations within grouped references.
2. Resolve each conditional feature and distinguish reference evidence from downstream equipment evidence. Record rationale even for exclusions.
3. Derive complete, measurable requirements and link hazards, architecture, implementation, protocols and results. Existing links cover six starter roadmap requirements plus nine narrower synthetic M1 requirements; they are not full clause coverage. M1 evidence does not close any standards entry.
4. Record the tested build/configuration, evidence locations, reviewer, date and any residual limitations before proposing closure.
5. Reassess affected entries after a standards, component, software, model or intended-use change. A future schema supporting closure must verify evidence, not just accept a changed status field.

The current checker validates this draft register and its links, and rejects unsupported closure claims. Release mode deliberately fails while checklist entries and edition gaps remain open. It is neither an interpretation authority nor a certification tool.

## Coverage and boundaries

| Source | Coverage in this revision | Remaining work |
| --- | --- | --- |
| ISO 14971:2019 | Grouped actions across clauses 4–10 | Full applicability/interpretation review, actual risk file, EU A11 mapping and evidence |
| IEC 62304:2006+A1:2015 | Grouped actions across clauses 4–9, including conditional legacy work | Per-class allocation, detailed requirement derivation and lifecycle evidence |
| IEC 81001-5-1:2021, supplied copy | Grouped actions across clauses 4–9 and decisions for normative Annexes F/G | 2025 interpretation/corrected-copy reconciliation and substantive review |
| Supplied US general medical-equipment standard | Chapter screening, expanded programmable-system and software/system obligations | EU edition reconciliation, detailed physical subclauses and normative annex/test coverage |
| Supplied US adoption of IEC 60601-2-16:2018 | Dialysis performance, protective functions, interfaces, information and collateral screening | Full 2025 delta review, EU baseline and detailed final-equipment tests |
| IEC 60601-2-24:2012 | Scope screening only | Conditional component decision; full clause assessment if applicable |
| EU MDR | Eight adaptation workstreams | Complete current product-specific legal/GSPR assessment; not a full MDR checklist |
| Project-derived actions | Ten architecture, model, licensing and publication actions | Implementation, review and evidence |

Ranges are grouped navigation references, not statements that each numbered paragraph imposes a separate requirement. IEC 62304 7.3.2 is not used in the reviewed final text. Informative rationale and examples are not converted into normative requirements. General/particular/collateral precedence must be resolved against the chosen edition set.

This checklist intentionally does not reproduce standard paragraphs, tables, diagrams or prescribed test procedures. It is not a substitute for authorized copies. Numerical clinical/protective limits must be derived and reviewed against the chosen standards, device assumptions and risk analysis; examples in standards are not automatically project defaults.

## Source handling

[sources.json](sources.json) records identifiers, supplied-file hashes, interpretation notes and public catalog/regulatory references. The supplied material contained ten PDFs: nine standards-related files (including duplicate/redundant material) and one historical dialysis-temperature article. The two dialysis copies have identical extracted text after removing copy-specific watermark lines, although their PDF hashes differ. The consolidated IEC 62304 final English text was used rather than its preceding redline. The general-standard redline was cross-checked with the supplied amendment for programmable-system changes.

Only bibliographic metadata and original project writing are included here. The licensed PDFs, extracted text and page images remain outside the project. The research article is recorded as a possible background source, not a standard or validated calibration dataset.

Read [EDITION_GAPS.md](EDITION_GAPS.md) before treating any reference as the selected EU conformity baseline, and [PUBLICATION_POLICY.md](PUBLICATION_POLICY.md) before publication.
