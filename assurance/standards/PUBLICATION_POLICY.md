# Publication and licensed-source policy

The project owner authorizes use of the supplied standards for analysis and original explained checklists, and explicitly prohibits publishing the standards on GitHub.

Keep licensed standards, purchased report forms, raw extracts, OCR, screenshots, copied tables and figures outside the repository and all public packages. This also applies to commit history, issues, pull-request attachments, wikis, logs, CI artifacts and container build contexts/layers. Private analysis is not an approved publication source. Do not embed the supplied archive into another archive.

Public project material may contain bibliographic identifiers, clause references, source hashes and independently written explanations, project requirements, test designs and evidence for which redistribution is authorized. A project license does not relicense third-party standards, datasets, assets or manufacturer documents. The project's own MIT license is recorded in LICENSE; its grant does not extend to licensed standards or other third-party material.

The package builder uses an explicit reviewed file list and accepts only supported text formats. It rejects symlinks, out-of-root paths, source-file hashes and unlisted input formats. This prevents accidental inclusion of source PDFs; it does not prove that every sentence in a permitted text file is free of copied material. A human content review remains required when adding or materially changing public files.

The current `.gitignore` is an accident-prevention aid, not an access control or a history scrubber. It does not remove already tracked files. Before publication, review the complete proposed commit and history, repository license and notices. If licensed material is ever staged, stop publication and remove it from the proposed commit/history and derived artifacts through a reviewed correction.

Only aggregate errors and identifiers should appear in public checks. Never print private source passages or local license-holder watermarks into CI logs. Collaborators obtain their own authorized source access; this project provides no download or license bypass.
