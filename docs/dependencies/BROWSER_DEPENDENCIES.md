# Browser runtime dependency review candidate

Profile browser-candidate-1. This is a separate prototype profile, not an implicit
extension of the accepted linux-software-ui-1 application inventory.

| Component | Exact selection | Use and terms |
|---|---|---|
| Emscripten | 4.0.15, release b412b6307e541b93dd93f01b61181e15c17302ec | Build tool and generated JS/runtime; MIT OR NCSA. LLVM/libc++ and system-library terms also apply to generated artifacts. |
| LVGL | 9.6.0, existing gui_dependencies.json | Existing MIT UI source, compiled to Wasm. |
| SDL | 2.32.10, existing gui_dependencies.json | Existing source; Emscripten video/input backend; Zlib with bundled MIT/BSD components. |
| Pyodide | 0.27.7 | Unmodified browser Python runtime, MPL-2.0. Five exact downloaded artifacts pinned by SHA-256 in browser_dependencies.json. |
| CPython | 3.12.7, as shipped in Pyodide | PSF-2.0 and historical terms in CPYTHON_LICENSE.md. Existing Python model executes without translation. |
| Roboto | Existing pinned project font | Apache-2.0; ROBOTO_NOTICE.md retained. |

Pyodide corresponding source and build recipes are available at
https://github.com/pyodide/pyodide/tree/0.27.7 (including the selected runtime and
Python build dependencies). CPython source: https://github.com/python/cpython/tree/v3.12.7.
No Pyodide files are modified, no micropip packages are installed, and no optional
scientific packages are fetched. The standard runtime still contains dependencies
such as its C libraries and standard-library extensions; absence of extra package
installation is not a complete binary SBOM or license audit. A complete generated
runtime/transitive-notice inventory remains a release obligation.

## Exception decision, pending

MPL-2.0 and PSF-2.0 are outside the repository's preferred application-license list.
The prototype is implemented for the maintainer's requested feasibility test.
**No exception is recorded as approved. Explicit maintainer review is required
before merge**, as specified in DEPENDENCY_POLICY.md. The reason for the candidate
is to execute the existing Python patient and distributed solute model unchanged.
Reimplementing those equations in C++ would create a separate numerical-verification
burden. A server-side Python runtime is the alternative that avoids distributing
Python to clients, but does not meet the requested fully local execution.

Risks: larger download/startup, browser memory/CPU, single-worker fault domain,
runtime-version drift, and stale UI on suspension. Hash checks, local-only assets,
explicit clock pause, fail-stop handling and native/Wasm record comparisons provide
bounded engineering evidence. They do not establish a security certification,
independent protection or production-hosting readiness. Re-review on any runtime,
Python, compiler, GUI dependency, feature or distribution change.

The static candidate includes project, GUI, font, Pyodide and Python notices.
Public release remains subject to the exception and complete transitive review;
a source draft PR and local prototype do not assert those decisions are complete.
