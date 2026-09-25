<img src="assets/banner.svg" width="100%" alt="DokuReader Banner">

# DokuReader — Local Document Library & PDF Organizer

<p align="center"><strong>🇬🇧 English</strong> · <a href="README_de.md">🇩🇪 Deutsch</a></p>

> Organize, preview, and bundle local documents by topic — references and read status only, originals stay put.

[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL--3.0-green)](LICENSE)
[![Version](https://img.shields.io/badge/Version-1.0.1--dev-blue)](CHANGELOG.md#unreleased)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](pyproject.toml)
[![UI: Python / Tkinter](https://img.shields.io/badge/GUI-Python%20%2F%20Tkinter-blue)](DokuReader.py)
[![Platform: Windows | macOS | Linux](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-blue?logo=windows)](#getting-started--installation)
[![Pytest: 65 tests, 0 failed](https://img.shields.io/badge/Pytest-65%20tests%2C%200%20failed-success?logo=pytest)](pyproject.toml)
[![Web Companion: 37 passed](https://img.shields.io/badge/Web%20Companion-37%20passed-success?logo=nodedotjs)](web_companion)
[![Privacy: 100% Offline](https://img.shields.io/badge/Privacy-100%25%20Offline-success)](PRIVACY_POLICY.md)
[![Security: Local--First](https://img.shields.io/badge/Security-Local--First-blue)](SECURITY.md)
[![Security SLA: 48h / 5d](https://img.shields.io/badge/Security%20SLA-48h%20%2F%205d-orange)](SECURITY.md)
[![RunAsInvoker: Non--Elevated](https://img.shields.io/badge/RunAsInvoker-Non--Elevated-success)](SECURITY.md)
[![Third-Party Licenses: Audited](https://img.shields.io/badge/Third--Party%20Licenses-Audited-green)](THIRD_PARTY_LICENSES.md)
[![Marketing Log: Active](https://img.shields.io/badge/Marketing%20Log-Active-blue)](MARKETING-LOG.txt)
[![LLM-Ready: llms.txt](https://img.shields.io/badge/LLM--Ready-llms.txt-success)](llms.txt)
[![Ecosystem: doc-bricks](https://img.shields.io/badge/Ecosystem-doc--bricks-purple)](https://github.com/doc-bricks)
[![Umbrella: open-bricks](https://img.shields.io/badge/Umbrella-open--bricks-blue)](https://github.com/open-bricks)
[![Audit: 2026--09--25](https://img.shields.io/badge/Audit-2026--09--25-informational)](#quality-gates--automated-test-suites)
[![Attribution: NOTICE](https://img.shields.io/badge/Attribution-NOTICE-blue)](NOTICE)

> [!NOTE]
> DokuReader is part of the **doc-bricks** local document management suite. It works seamlessly alongside [LitZentrum](https://github.com/doc-bricks/LitZentrum) (citation & literature management), [CleanMarkdown](https://github.com/doc-bricks/CleanMarkdown) (Markdown reading & editing), and [UniversalDocsGrabber](https://github.com/doc-bricks/UniversalDocsGrabber) (mail attachment intake). DokuReader is fully indexed for AI/LLM coding assistants via [`llms.txt`](llms.txt).

---

### Quick Navigation
1. [Overview & Core Value](#overview--core-value)
2. [Key Capabilities & Feature Matrix](#key-capabilities--feature-matrix)
3. [Interactive Architecture Flowchart](#interactive-architecture-flowchart)
4. [Target Personas & High-Intent Discoverability Queries](#target-personas--high-intent-discoverability-queries)
5. [Comparative Matrix vs. Alternatives](#comparative-matrix-vs-alternatives)
6. [Document Lifecycle & Privacy Sequence](#document-lifecycle--privacy-sequence)
7. [Getting Started & Installation](#getting-started--installation)
8. [Supported Formats & System Dependencies](#supported-formats--system-dependencies)
9. [Windows Store & Standalone Build](#windows-store--standalone-build)
10. [Mobile & PWA Companion](#mobile--pwa-companion)
11. [Governance & Runtime Invariants](#governance--runtime-invariants)
12. [Sibling Tools & Ecosystem Matrix](#sibling-tools--ecosystem-matrix)
13. [Privacy & Security Posture](#privacy--security-posture)
14. [Quality Gates & Automated Test Suites](#quality-gates--automated-test-suites)
15. [Machine-Readable Context (`llms.txt`)](#machine-readable-context-llmstxt)
16. [Third-Party Licenses & Transparency](#third-party-licenses--transparency)
17. [Marketing & Discoverability Strategies / Log](#marketing--discoverability-strategies--log)
18. [Statutory Notice, Liability Limitation & License](#statutory-notice-liability-limitation--license)

---

## Overview & Core Value
<a id="sec-01"></a>
<a id="overview--core-value"></a>
<a id="overview"></a>

DokuReader is an unprivileged desktop application for organizing, previewing, and bundling documents by topic. Original files stay exactly where they are; the application indexes only file path references and read status in a local JSON state file (`~/.dokubibliothek_state.json`).

It is engineered specifically for private document libraries, academic research collections, confidential legal discovery sets, and topic-based reading queues that must remain 100% offline, inspectable, and secure.

| Goal | Entry Point |
|---|---|
| Run the desktop application | `python DokuReader.py` or `START.bat` |
| Understand the export specification | [EXPORTFORMAT.md](EXPORTFORMAT.md) |
| Test the desktop source build | `python tests/source_platform_smoke.py` |
| Check the mobile/PWA companion smoke | [web_companion/README.md](web_companion/README.md) |
| Check Windows Store readiness | `python _WARTUNG/check_store_readiness.py --allow-blockers` |
| Prepare or parse WACK reports | `python _WARTUNG/run_windows_wack.py --dry-run` |
| Prepare Windows Store listings | [STORE_LISTING.md](STORE_LISTING.md), [PRIVACY_POLICY.md](PRIVACY_POLICY.md), [SUPPORT.md](SUPPORT.md) |
| Provide LLM tools project context | [`llms.txt`](llms.txt) |

### Version and Release Status

The version roles are intentionally separate and read back from the current source tree:
- **Development Runtime:** `1.0.1-dev` (`DokuReader.py` and `pyproject.toml` `1.0.1.dev0`)
- **Windows Store Package Metadata:** `1.0.1.0` (`store_package.json`)
- **Release Verification:** There is no verified public release artifact in this repository. Signing, MSIX generation, WACK validation, and Store submission remain external gates. The `1.0.1-dev` badge indicates development status, not a public store release claim. See [RELEASE_STATUS.md](RELEASE_STATUS.md) and [PORTIERUNGSPLAN.md](PORTIERUNGSPLAN.md).

---

## Key Capabilities & Feature Matrix
<a id="sec-02"></a>
<a id="key-capabilities--feature-matrix"></a>
<a id="key-capabilities"></a>

- **In-Place File Protection (INV-INPLACE-03):** Original documents are never copied, moved, modified, or overwritten.
- **Dynamic Topic Organization:** Create, rename, sort, and delete document topics on the fly.
- **Read / Unread Queue Management:** Toggle read status with one click; filter exports by read, unread, or all.
- **Multi-Format Instant Preview:** In-app visual preview for PDFs, text files, images (JPG, PNG, GIF), and Office documents (DOCX, ODT).
- **Text Preview & Latin-1 Fallback:** Robust text rendering with UTF-8 primary and Latin-1 secondary decoding.
- **Desktop Drag-and-Drop:** Intuitive document intake when `tkinterdnd2` is installed.
- **External App Dispatch:** Double-click opens any document in the system default application.
- **Consolidated PDF Bundling:** Merge selected read, unread, or all documents into a single consolidated PDF bundle.
- **Clean JSON Metadata Export:** Export the entire library outline as schema-compliant `dokureader-library-v1.json` without copying or embedding binary document content.
- **Office Conversion Pipeline:** Seamless conversion of Office formats via headless LibreOffice or Windows Word COM.
- **Offline PWA Companion:** Zero-egress mobile web application for reviewing libraries and toggling read status on smartphones and tablets.

---

## Interactive Architecture Flowchart
<a id="sec-03"></a>
<a id="interactive-architecture-flowchart"></a>
<a id="architecture"></a>

```mermaid
flowchart TD
    subgraph Host ["Local Workstation Environment (Windows · macOS · Linux)"]
        subgraph App ["DokuReader Application Layer"]
            UI["Tkinter Desktop UI (DokuReader.py)"]
            StateManager["Local State Manager"]
            PreviewEngine["Preview Engine"]
            ExportEngine["Export & Bundling Engine"]
        end

        subgraph Backends ["Processing & Preview Backends"]
            MuPDF["PyMuPDF (PDF Render Engine)"]
            PIL["Pillow (Image Processing)"]
            OfficeConv["LibreOffice / MS Word (COM / Subprocess)"]
            PDFMerger["pypdf / reportlab (PDF Generation)"]
        end

        subgraph Storage ["Local Storage & Privacy Boundary"]
            Originals[("Original Documents (Read-Only In-Place)")]
            StateFile[("~/.dokubibliothek_state.json")]
            ExportFile[("dokureader-library-v1.json")]
            PDFOutput[("Consolidated PDF Bundle")]
        end
    end

    subgraph Companion ["PWA Mobile Companion (web_companion)"]
        PWA["Local PWA Client (Offline Cache)"]
    end

    UI --> StateManager
    UI --> PreviewEngine
    UI --> ExportEngine

    StateManager <--> StateFile
    PreviewEngine --> MuPDF
    PreviewEngine --> PIL
    PreviewEngine --> OfficeConv
    PreviewEngine -. Read-Only .-> Originals

    ExportEngine --> PDFMerger
    ExportEngine --> ExportFile
    PDFMerger --> PDFOutput

    ExportFile -. Offline JSON Import / Sync .-> PWA
```

---

## Target Personas & High-Intent Discoverability Queries
<a id="sec-04"></a>
<a id="target-personas--high-intent-discoverability-queries"></a>
<a id="target-personas"></a>

DokuReader serves four distinct user personas requiring deterministic, local-first document curation:

- **`[PERSONA-01]` Academic Researchers & Literature Curators:**
  - *Need:* Curation of preprints, journal PDFs, whitepapers into topic-based reading queues without duplicating or modifying local filesystem storage.
  - *High-Intent Queries (EN):* "offline local document organizer pdf research library", "desktop pdf manager read status topics", "academic paper queue local first python"
  - *High-Intent Queries (DE):* "lokale dokumentenverwaltung pdf forschungsbibliothek", "desktop pdf organizer lesestatus themen", "wissenschaftliche artikel offline lesen"

- **`[PERSONA-02]` Legal Counsel & Compliance Officers:**
  - *Need:* Confidential discovery dossier organization, litigation case reading, zero cloud egress under GDPR/HIPAA/professional secrecy mandates.
  - *High-Intent Queries (EN):* "confidential legal discovery document viewer offline", "zero egress local pdf bundle case management", "gdpr compliant document organizer desktop"
  - *High-Intent Queries (DE):* "vertrauliche aktenverwaltung anwalt offline", "zero egress dokumentenleser bündeln datenschutz", "dsgvo konforme dokumentenbibliothek lokal"

- **`[PERSONA-03]` Technical Writers & Knowledge Engineers:**
  - *Need:* Multi-format document inspection (Markdown, PDF, DOCX, ODT, images), in-place topic indexing, consolidated PDF bundling for handbook reviews.
  - *High-Intent Queries (EN):* "multi format document preview bundling tool", "markdown docx pdf reading list desktop", "technical documentation bundle generator local"
  - *High-Intent Queries (DE):* "multi format dokumenten vorschau sammlung", "markdown docx pdf leseliste desktop", "technische dokumentation bündeln offline"

- **`[PERSONA-04]` Autonomous AI Agents & Developers:**
  - *Need:* Clean schema-compliant `dokureader-library-v1.json` metadata exports for agentic indexing and local RAG pipelines without file copying.
  - *High-Intent Queries (EN):* "local document library metadata json export schema", "clean json document catalogue ai agents", "offline document reader llm ready"
  - *High-Intent Queries (DE):* "lokale dokumentenbibliothek json export schema", "metadaten katalog dokumente llm agenten", "offline dokumentenleser llms txt"

---

## Comparative Matrix vs. Alternatives
<a id="sec-05"></a>
<a id="comparative-matrix-vs-alternatives"></a>
<a id="comparative-matrix"></a>

Evaluation of DokuReader against common alternative approaches across 10 architectural and operational dimensions:

| Dimension / Requirement | DokuReader | Calibre (E-Book Manager) | Zotero (Reference Manager) | DEVONthink / Commercial DMS | Ad-Hoc Filesystem Folders |
|:---|:---|:---|:---|:---|:---|
| **D1: In-Place Safety (`INV-INPLACE-03`)** | **Strictly in-place** (Zero file moves or modifications) | ❌ Copies all files into rigid internal directory structure | ⚠️ Copies files by default (linked files complex) | ⚠️ Proprietary database vault ingestion | ✅ Files remain in place |
| **D2: Zero-Egress Privacy (`INV-LOCAL-01`)** | **100% Offline** (Zero outbound network traffic) | ⚠️ Integrates web content scraping and server daemons | ⚠️ Cloud sync account prompts and web integrations | ❌ Proprietary cloud sync & license verification | ✅ Local only |
| **D3: Unprivileged Execution (`INV-RUNAS-02`)** | **RunAsInvoker User Mode** (No admin elevation) | ⚠️ Installer often prompts for UAC elevation | ⚠️ Administrative install requirements | ❌ System kernel/driver extensions on macOS | ✅ Standard user mode |
| **D4: Deterministic Schema (`INV-SCHEMA-04`)** | **`dokureader-library-v1`** clean JSON export | ❌ Complex SQLite schema with heavy metadata blobs | ❌ Complex SQLite / CSL JSON exports | ❌ Proprietary binary database formats | ❌ No structured metadata schema |
| **D5: Multi-Format Preview (`INV-SANDBOX-06`)** | **PDF, TXT, DOCX, ODT, PNG, JPG** via safe bridges | ✅ Broad e-book format support | ⚠️ PDF focused; limited office format previews | ✅ Broad format support | ❌ Relies entirely on external OS apps |
| **D6: Consolidated PDF Bundling** | **One-click merged PDF** with read/unread filters | ❌ No native topic PDF merging workflow | ❌ Requires external plugins or PDF editors | ⚠️ Complex scripting required | ❌ Requires manual external PDF stitching |
| **D7: Mobile PWA Companion (`INV-ISOLATION-05`)** | **Offline PWA** with round-trip JSON sync | ⚠️ Built-in web server exposes open HTTP port | ⚠️ Proprietary iOS/Android mobile apps | ⚠️ Proprietary sync server and mobile apps | ❌ Manual file sync required |
| **D8: Tri-Platform Source Support (`INV-PARITY-07`)** | **Windows, Linux & macOS** native Python/Tkinter | ✅ Cross-platform desktop | ✅ Cross-platform desktop | ❌ Apple macOS/iOS proprietary lock-in | ✅ Universal |
| **D9: Automated Test Quality Gates** | **62+ Pytest + 37 Node tests** (100% green) | ⚠️ Large monolithic codebase | ⚠️ Complex integration harness | ❌ Closed-source proprietary verification | ❌ No test harness |
| **D10: Open Governance & SLA (`INV-SLA-10`)** | **AGPL-3.0, § 521 BGB disclaimer, 48h SLA** | ⚠️ GPL-3.0, no formal vulnerability SLA | ⚠️ AGPL-3.0, community forum triage | ❌ Closed-source commercial EULA | ❌ None |

---

## Document Lifecycle & Privacy Sequence
<a id="sec-06"></a>
<a id="document-lifecycle--privacy-sequence"></a>
<a id="document-lifecycle"></a>

```mermaid
sequenceDiagram
    autonumber
    actor User as User / Researcher
    participant UI as Desktop UI (DokuReader.py)
    participant State as Local State Manager
    participant Engine as Preview & Conversion Engine
    participant Disk as Local Storage (Original Files)
    participant Output as Export Generator

    User->>UI: Add File / Drag-and-Drop
    UI->>Disk: Inspect File Metadata (Stat only)
    Note over UI,Disk: Originals remain untouched (INV-INPLACE-03)
    UI->>State: Store Topic Reference & Unread Flag (INV-ISOLATION-05)
    State-->>UI: Update Topic Tree View

    User->>UI: Select Document for Preview
    UI->>Engine: Request Page 1 / Text Stream
    Engine->>Disk: Read-Only Stream
    Engine-->>UI: Rendered Thumbnail / Plaintext
    UI-->>User: Display In-App Preview

    User->>UI: Toggle Read Status
    UI->>State: Persist Read Status
    State-->>UI: Reflected in Library Overview

    User->>UI: Trigger Export (Consolidated PDF or JSON)
    UI->>Output: Generate Bundle (Filtered by Read/Unread)
    Output->>Disk: Write dokureader-library-v1.json or Merged PDF
    Note over UI,Disk: 100% Offline / Local-First — Zero Network Egress (INV-LOCAL-01)
```

---

## Getting Started & Installation
<a id="sec-07"></a>
<a id="getting-started--installation"></a>
<a id="installation"></a>

### Requirements

- Python 3.10+
- Tkinter (included with standard Python installations)

### Installation

```bash
git clone https://github.com/doc-bricks/DokuReader.git
cd DokuReader
pip install -r requirements.txt
```

### Quick Start

```bash
python DokuReader.py
```

On Windows, launch directly via:

```bat
START.bat
```

---

## Supported Formats & System Dependencies
<a id="sec-08"></a>
<a id="supported-formats--system-dependencies"></a>
<a id="supported-formats"></a>

### Supported Document Formats

- **Documents:** `.txt`, `.doc`, `.docx`, `.pdf`, `.odt`, `.rtf`
- **Images:** `.jpg`, `.jpeg`, `.gif`, `.png`

### Optional System Dependencies

For full preview rendering and external document conversion:
- **LibreOffice:** Required for headless DOC/DOCX/ODT/RTF to PDF conversion.
- **Poppler:** Required if using the optional `pdf2image` preview backend.
- **Microsoft Word:** Supported on Windows for direct COM-based document conversion.

---

## Windows Store & Standalone Build
<a id="sec-09"></a>
<a id="windows-store--standalone-build"></a>
<a id="windows-store"></a>

### Local Executable Build

```bat
build_exe.bat
```

Build output under `build/`, `dist/`, and `releases/` stays strictly local and is excluded from Git tracking via `.gitignore`. Set `DOKUREADER_BUILD_ROOT` to customize the local build scratch directory.

### Windows Store Readiness Gate

```bash
python _WARTUNG/check_store_readiness.py --allow-blockers
```

Validates Store metadata, privacy policy URLs, required support links, visual assets, screenshots, and MSIX packaging requirements.

### WACK Runner & Parser

```bash
python _WARTUNG/run_windows_wack.py --dry-run
```

Generates the exact certification command for elevated execution and parses resulting XML validation reports into structured JSON.

---

## Mobile & PWA Companion
<a id="sec-10"></a>
<a id="mobile--pwa-companion"></a>
<a id="pwa-companion"></a>

The companion web application under `web_companion/` provides an offline-first, mobile-optimized reading view:
- **Installable PWA:** Full Web App Manifest with iOS Safe-Area support (`viewport-fit=cover`).
- **Offline Shell:** Scoped Service Worker caching preserving external application caches.
- **Round-Trip Synchronization:** Imports `dokureader-library-v1.json` exported from the desktop app, allows toggling read states on mobile, and exports an updated JSON back to the desktop.
- **Zero Third-Party Dependencies:** Runs on pure vanilla JavaScript and Node.js built-in test runner (`37 passed, 0 failed`).

```bash
cd web_companion
node --test
```

---

## Governance & Runtime Invariants
<a id="sec-11"></a>
<a id="governance--runtime-invariants"></a>
<a id="governance"></a>

The following 10 invariants govern DokuReader's runtime architecture, privacy boundary, and security guarantees:

| Invariant | Principle | Guarantee & Verification Mechanism |
|:---|:---|:---|
| **INV-LOCAL-01** | 100% Local-First & Zero-Egress | Zero outbound HTTP/S, WebSocket, or telemetry traffic. All parsing and previews operate strictly offline. |
| **INV-RUNAS-02** | Unprivileged RunAsInvoker Execution | The application runs exclusively in standard user mode without administrative elevation requirements. |
| **INV-INPLACE-03** | In-Place Original File Safety | Original documents are strictly read-only. DokuReader never moves, modifies, or deletes imported files. |
| **INV-SCHEMA-04** | Deterministic Export Schema | Library metadata exports adhere strictly to the versioned `dokureader-library-v1` JSON specification. |
| **INV-ISOLATION-05** | Local State & Cache Isolation | State is isolated in `~/.dokubibliothek_state.json`. PWA companion caches only within `dokureader-companion-` scope. |
| **INV-SANDBOX-06** | Safe Subprocess Execution | External converters (LibreOffice, Word COM) run with constrained arguments, timeout guards, and isolated temp directories. |
| **INV-PARITY-07** | Tri-Platform Source Support | Core codebase runs across Windows, macOS, and Linux with platform-independent path handling and fallbacks. |
| **INV-A11Y-08** | Keyboard & Visual Accessibility | Full keyboard navigation support, high-contrast readability, and deterministic UI state reflection. |
| **INV-DISCOVERY-09** | Multimodal Transparency & LLM Ready | Complete bilingual documentation (DE/EN), machine-readable `llms.txt`, and interactive dual Mermaid diagrams. |
| **INV-SLA-10** | Security Vulnerability SLA | Formal 48h initial response SLA and 5-business-day triage commitment for reported security disclosures. |

---

## Sibling Tools & Ecosystem Matrix
<a id="sec-12"></a>
<a id="sibling-tools--ecosystem-matrix"></a>
<a id="ecosystem"></a>

DokuReader is a core component of the **doc-bricks** family under the **open-bricks** open-source initiative:

| Repository | Focus | Role in Desktop Workflow |
|:---|:---|:---|
| **[LitZentrum](https://github.com/doc-bricks/LitZentrum)** | Literature & Citations | Academic paper library, BibTeX export, and literature management |
| **[CleanMarkdown](https://github.com/doc-bricks/CleanMarkdown)** | Markdown Studio | Focused Markdown reader, editor, and typography cleaner |
| **[UniversalDocsGrabber](https://github.com/doc-bricks/UniversalDocsGrabber)** | Document Intake | Automated mail attachment extraction and local document sorting |
| **[UniversalInvoiceMail](https://github.com/doc-bricks/UniversalInvoiceMail)** | Invoice Mail Extraction | Deterministic invoice attachment detection and extraction |
| **[UniversalMailCleaner](https://github.com/doc-bricks/UniversalMailCleaner)** | Mail Hygiene | Local mail archive cleaning, duplicate removal, and sanitization |
| **[MailProcessor](https://github.com/doc-bricks/MailProcessor)** | Mail Processing | Rule-based local mail routing, filtering, and document triage |
| **[PDFtoPDFocr](https://github.com/doc-bricks/PDFtoPDFocr)** | PDF OCR Processing | Searchable sandwich PDF creation with local Tesseract OCR |
| **[MediaBrain](https://github.com/doc-bricks/MediaBrain)** | Media Asset Organizer | Visual media tagging, categorization, and metadata indexing |
| **[DokuZen](https://github.com/doc-bricks/DokuZen)** | Distraction-Free Docs | Minimalist zen reading and document inspection environment |
| **[ProFiler](https://github.com/file-bricks/ProFiler)** | Multi-Tool File Analysis | Deep file inspector, structural parser, and metadata profiler |
| **[ExplorerPro](https://github.com/file-bricks/ExplorerPro)** | Advanced File Explorer | High-performance multi-pane local file manager |
| **[DevCenter](https://github.com/dev-bricks/DevCenter)** | Developer Workspace | Central developer dashboard and project management hub |
| **[CodeBox](https://github.com/dev-bricks/CodeBox)** | Code Snippet Vault | Offline-first code snippet organizer with syntax highlighting |
| **[open-bricks](https://github.com/open-bricks)** | Umbrella Architecture | Master ecosystem coordination for desktop productivity |

---

## Privacy & Security Posture
<a id="sec-13"></a>
<a id="privacy--security-posture"></a>
<a id="privacy--security"></a>

- **Zero Network Egress:** The application contains no telemetry code, analytics libraries, or cloud sync background tasks.
- **In-Place File Safety:** Imported files are opened exclusively in read-only mode for thumbnail and text preview.
- **RunAsInvoker Least Privilege:** Operates entirely in unprivileged standard user mode.
- **Formal Security SLA:** Vulnerability disclosures receive initial acknowledgement within **48 hours** and triage within **5 business days**. Reports should be submitted to `security@open-bricks.org`, `security@ellmos.ai`, or via GitHub Security Advisories. See [SECURITY.md](SECURITY.md).

---

## Quality Gates & Automated Test Suites
<a id="sec-14"></a>
<a id="quality-gates--automated-test-suites"></a>
<a id="testing"></a>

Continuous quality is assured through independent, automated verification gates:

```bash
# Run Python unit and metadata contract tests (65 tests)
pytest

# Run static analysis and lint checks
ruff check .

# Validate whole-repository bytecode compilation
python -m compileall -q .

# Run cross-platform desktop smoke test
python tests/source_platform_smoke.py

# Run mobile PWA companion test suite (37 tests)
cd web_companion && node --test
```

---

## Machine-Readable Context (`llms.txt`)
<a id="sec-15"></a>
<a id="machine-readable-context-llmstxt"></a>
<a id="llm-context"></a>

For AI coding agents (Claude Code, Gemini / Antigravity, Codex, Kimi Code), DokuReader exposes complete architectural context via [`llms.txt`](llms.txt). It provides canonical repository paths, dependency boundaries, test commands, search keywords, and security invariants in an efficient format.

---

## Third-Party Licenses & Transparency
<a id="sec-16"></a>
<a id="third-party-licenses--transparency"></a>
<a id="third-party-licenses"></a>

DokuReader is licensed under the **GNU Affero General Public License v3.0 (AGPL-3.0)**. All third-party Python dependencies (Pillow, pypdf, reportlab, python-docx, odfpy, tkinterdnd2, pywin32, pdf2image) are distributed under permissive open-source licenses (MIT, BSD-3-Clause, Apache-2.0, PSF-2.0) or compatible AGPL-3.0 (PyMuPDF).

For the complete dependency audit, Level 1 SBOM invariant cross-reference matrix, and unprivileged runtime statements, see [THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md), [THIRD_PARTY_LICENSES.txt](THIRD_PARTY_LICENSES.txt), and [NOTICE](NOTICE).

---

## Marketing & Discoverability Strategies / Log
<a id="sec-17"></a>
<a id="marketing--discoverability-strategies--log"></a>
<a id="marketing-log"></a>

DokuReader maintains an active, traceable marketing, discoverability, and architecture audit log in [MARKETING-LOG.txt](MARKETING-LOG.txt).

Key discoverability pillars:
1. **GitHub Ecosystem Satiation:** Full 20/20 topics populated with high-intent keywords (`desktop-app`, `document-management`, `library`, `pdf`, `pdf-export`, `python`, `tkinter`, `local-first`, `privacy-first`, `reading-state`).
2. **LLM Context Integration:** Indexed via [`llms.txt`](llms.txt) for AI developer agents and search engines.
3. **Cross-Project Linkage:** Deep integration with doc-bricks sibling tools ([LitZentrum](https://github.com/doc-bricks/LitZentrum), [CleanMarkdown](https://github.com/doc-bricks/CleanMarkdown), [UniversalDocsGrabber](https://github.com/doc-bricks/UniversalDocsGrabber)).
4. **Bilingual Parity:** 100% documentation alignment between English ([README.md](README.md)) and German ([README_de.md](README_de.md)).

---

## Statutory Notice, Liability Limitation & License
<a id="sec-18"></a>
<a id="statutory-notice-liability-limitation--license"></a>
<a id="license--liability"></a>

### License & Attribution
DokuReader is licensed under the **[GNU Affero General Public License v3.0 (AGPL-3.0)](LICENSE)**. Full author and open-source umbrella attribution is declared in [`NOTICE`](NOTICE).

### Gesetzlicher Haftungsausschluss gem. § 521 BGB (Gefälligkeitsrecht)
> **Statutory Disclaimer pursuant to § 521 German Civil Code (BGB):**<br>
> Da diese Software und sämtliche zugehörigen Vorlagen unentgeltlich zur Verfügung gestellt werden, haften die Urheber, die Organisation `doc-bricks` sowie der Dachverband `open-bricks` nach den gesetzlichen Bestimmungen des deutschen Gefälligkeitsrechts (§ 521 BGB) ausschließlich für Vorsatz und grobe Fahrlässigkeit. Eine Gewährleistung für Sach- oder Rechtsmängel ist ausgeschlossen.<br>
> <br>
> *As this software and related templates are provided free of charge, the authors, the `doc-bricks` organization, and the `open-bricks` umbrella collective shall only be liable for intent and gross negligence in accordance with § 521 of the German Civil Code (BGB). Any warranty for defects of quality or title is excluded.*

### Binding 48-Hour Security Response SLA
> The maintainers commit to a **48-hour response SLA** for incoming security advisories and vulnerability notifications sent to **[security@open-bricks.org](mailto:security@open-bricks.org)**, **[security@ellmos.ai](mailto:security@ellmos.ai)**, or reported via [GitHub Security Advisories](https://github.com/doc-bricks/DokuReader/security/advisories/new). Initial triage is completed within **5 business days**. For details, see [SECURITY.md](SECURITY.md).
