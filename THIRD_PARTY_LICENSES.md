# DokuReader — Third-Party Dependency & License Audit

**Status:** Audited & Verified (Pfad B Discoverability & Compliance Re-Audit)<br>
**Date:** 2026-09-25<br>
**Project License:** [GNU Affero General Public License v3.0 (AGPL-3.0)](LICENSE) · [NOTICE](NOTICE)<br>
**Security & Isolation Model:** 100% Local-First · Zero-Egress · RunAsInvoker Non-Elevation  

---

## 1. Executive Summary & Compliance Posture

DokuReader is engineered as a local-first, offline document management and topic-based PDF bundling desktop application.

- **Attribution & Notice:** Canonical project attribution, authors, and open-source umbrella relations are declared in the [NOTICE](NOTICE) file in the repository root.
- **Zero Network Egress (INV-LOCAL-01):** None of the runtime dependencies bundle background telemetry, analytics collectors, or cloud update dispatchers. All parsing and preview operations execute entirely within the local host environment.
- **Unprivileged Execution (INV-RUNAS-02):** All dependencies operate safely within standard user privilege mode (`RunAsInvoker`). No administrative elevation, root daemon execution, or privileged OS hooks are required or requested.
- **License Compatibility:** The project is licensed under AGPL-3.0. Runtime and development dependencies are distributed under permissive open-source licenses (MIT, BSD-3-Clause, Apache-2.0, PSF-2.0) or compatible reciprocal licenses (PyMuPDF AGPL-3.0), ensuring 100% OSI compliance without proprietary lock-in.

---

## 2. Direct Runtime Dependencies

| Package | Version Range | License | Type | Role in DokuReader | Egress / Privilege Posture |
|:---|:---|:---|:---|:---|:---|
| **PyMuPDF** (`fitz`) | `>=1.20.0` | AGPL-3.0 / Artifex Commercial | Reciprocal / Permitted | High-performance PDF page rendering, text extraction, thumbnail generation | 100% Local / In-process |
| **Pillow** (`PIL`) | `>=9.0.0` | MIT-CMU | Permissive | Image thumbnail generation, image format decoding, and image-to-PDF pipeline | 100% Local / In-process |
| **pypdf** | `>=3.0.0` | BSD-3-Clause | Permissive | Deterministic PDF concatenation, outline preservation, and multi-file merging | 100% Local / In-process |
| **reportlab** | `>=3.6.0` | BSD-3-Clause | Permissive | Text-to-PDF compilation engine with typographic formatting and page budgeting | 100% Local / In-process |
| **python-docx** | `>=0.8.11` | MIT | Permissive | Optional Office Open XML (.docx) structural inspection and text extraction | 100% Local / In-process |
| **odfpy** | `>=1.4.0` | Apache-2.0 / LGPL-2.1+ | Permissive | Optional OpenDocument (.odt) parsing and content previewing | 100% Local / In-process |
| **tkinterdnd2** | `>=0.3.0` | MIT | Permissive | Optional native drag-and-drop integration for desktop document import | 100% Local / GUI Event Hook |
| **pywin32** | `>=300` | PSF-2.0 | Permissive | Optional Windows COM automation bridge for local Microsoft Word PDF export | 100% Local / Standard COM |
| **pdf2image** | `>=1.16.0` | MIT | Permissive | Optional secondary PDF rasterization backend using local Poppler binaries | 100% Local / CLI Subprocess |

---

## 3. Web Companion & PWA Dependencies

The mobile/PWA companion (`web_companion/`) is architected with **zero third-party npm runtime dependencies**:
- **Offline Shell:** Pure vanilla HTML5, CSS3 (Safe-Area insets for iOS/Android), and ES6 JavaScript.
- **Service Worker:** Native CacheStorage API scoped strictly to the `dokureader-companion-` namespace.
- **Test Suite:** Native Node.js test runner (`node:test` and `node:assert`, Node >= 18). Zero third-party npm packages.

---

## 4. Development, Linting & QA Tooling

| Tool / Framework | License | Primary Purpose |
|:---|:---|:---|
| **pytest** | MIT | Automated Python test runner and metadata contract validation |
| **ruff** | MIT / Apache-2.0 | Extremely fast Python linter, code quality validator, and style checker |
| **setuptools** | MIT | Standard PEP 517 / PEP 621 Python packaging backend |
| **PyInstaller** | GPL-2.0 with runtime exception | Local standalone Windows executable compilation (`build_exe.bat`) |

---

## 5. Optional External System Tools (Not Bundled)

DokuReader can interface with locally installed system utilities if present on the host PATH:
- **LibreOffice:** Headless document conversion (`soffice --headless --convert-to pdf`). Executed as a bounded subprocess with strict timeout guards.
- **Poppler (`pdftoppm`):** Backend utility for `pdf2image`.
- **Microsoft Word:** Local Windows COM server.

*None of these external tools are bundled in the repository or required for core operation.*

---

## 6. Governance & Invariant Cross-Reference Matrix

All 10 architectural and runtime invariants are verified continuously across local test suites and CI workflows:

| Invariant | Category | Description | Primary Verification Target |
|:---|:---|:---|:---|
| `INV-LOCAL-01` | Local-First & Zero Egress | 100% offline operation, zero telemetry, zero analytics, zero external network requests | `tests/test_metadata.py`, `SECURITY.md` |
| `INV-RUNAS-02` | Non-Elevation User Mode | Unprivileged user-mode execution under `RunAsInvoker` principles; no admin rights required | `tests/test_metadata.py`, `SECURITY.md` |
| `INV-INPLACE-03` | In-Place File Safety | Original documents are strictly read-only; files are never modified, moved, or deleted | `tests/test_ui_accessibility.py` |
| `INV-SCHEMA-04` | Deterministic Schema | Library metadata exports adhere to versioned `dokureader-library-v1` JSON specification | `tests/test_export_format.py` |
| `INV-ISOLATION-05` | State & Cache Isolation | Isolated local JSON state in `~/.dokubibliothek_state.json`; scoped PWA cache | `tests/test_metadata.py`, `web_companion` |
| `INV-SANDBOX-06` | Safe Subprocess Execution | Headless LibreOffice and Word COM bridges execute with strict timeout and directory bounds | `tests/test_bug_regressions.py` |
| `INV-PARITY-07` | Tri-Platform Source Support | Core source runs across Windows, macOS, and Linux with cross-platform path handling | `.github/workflows/ci.yml` |
| `INV-A11Y-08` | Accessibility & Usability | Full keyboard accessibility, semantic names/roles/states, and readable color contrast | `tests/test_accessibility_contract.py` |
| `INV-DISCOVERY-09` | Multimodal Transparency | Full bilingual documentation (EN/DE), machine-readable `llms.txt`, dual Mermaid diagrams | `tests/test_metadata.py`, `llms.txt` |
| `INV-SLA-10` | Vulnerability Response SLA | Binding 48-hour response SLA and 5-business-day triage commitment for security advisories | `tests/test_metadata.py`, `SECURITY.md` |

### Unprivileged Execution & Compliance Statement
All build commands (`build_exe.bat`), test suites (`pytest`, `node --test`), and runtime execution (`python DokuReader.py`) operate purely in unprivileged user space under `RunAsInvoker` principles. Verification gates:
- Automated metadata and contract validation: `pytest -ra -v`
- Whole-repository bytecode compilation: `python -m compileall -q .`
- Linting and static analysis: `ruff check .`
- Mobile PWA companion verification: `cd web_companion && node --test`
