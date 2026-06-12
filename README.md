# DokuReader - Local Document Library

[Deutsch](README_de.md)

DokuReader is a local desktop application for organizing, previewing, and bundling documents by topic. Original files stay where they are; the application stores only file references and read status in a local JSON state file.

It is designed for private document libraries, research folders, PDF collections, and topic-based reading queues that should remain local and inspectable.

## Start Here

| Goal | Entry point |
|---|---|
| Run the desktop app | `python DokuReader.py` or `START.bat` |
| Understand the export format | `EXPORTFORMAT.md` |
| Test the desktop source build | `python tests/source_platform_smoke.py` |
| Check the mobile/PWA companion smoke | `web_companion/README.md` |
| Prepare Windows Store copy | `STORE_LISTING.md`, `PRIVACY_POLICY.md`, `SUPPORT.md` |
| Give LLM tools project context | `llms.txt` |

## Discovery Context

DokuReader is best described as a local-first document library, topic-based PDF organizer, reading-state tracker, and metadata-only document export tool. It is not a cloud document manager, hosted OCR service, general note-taking app, or full literature-citation suite.

Useful search phrases include `local-first document library`, `topic based PDF organizer`, `document read status tracker`, `metadata-only document export`, `Tkinter document manager`, and `offline PDF bundling desktop app`.

## Features

- Create, rename, and delete document topics
- Mark documents as read or unread
- Preview images, PDFs, text files, and DOCX/ODT documents
- Text preview and TXT-to-PDF export with UTF-8 and Latin-1 fallback
- Add files via drag and drop when `tkinterdnd2` is installed
- Open original documents in the default application with a double-click
- Export all, read, or unread documents as a combined PDF
- Export the full library as `dokureader-library-v1.json`
- Convert Office documents to PDF through LibreOffice or Microsoft Word
- Build a local Windows executable through the PyInstaller spec

## Privacy And Local Data

- DokuReader runs locally and does not upload documents to external services.
- Original files are not copied or modified.
- State is stored in `~/.dokubibliothek_state.json`.
- The standard JSON export contains topics, paths, file metadata, and read status, but no document contents.
- Local build artifacts, release files, internal task notes, and conversion scratch files are excluded via `.gitignore`.

## Screenshot

![DokuReader main window](README/screenshots/main.png)

## Installation

### Requirements

- Python 3.10+
- Tkinter, usually included with standard Python installations

### Python Dependencies

```bash
pip install -r requirements.txt
```

`requirements.txt` includes the supported Python integrations for preview, drag and drop, and PDF export. Missing optional packages only disable the related extra feature.

### Optional System Dependencies

For full preview and export functionality:

- LibreOffice for DOC/DOCX/ODT/RTF to PDF conversion
- Poppler for the optional `pdf2image` preview backend
- Microsoft Word on Windows for optional Word-COM conversion

## Usage

```bash
python DokuReader.py
```

On Windows, the start file can be used instead:

```bash
START.bat
```

For companion export, use the `Bibliothek (JSON)` section on the right side of the app. It writes topics, paths, file metadata, and read status to `dokureader-library-v1.json` without copying document contents. The format is documented in `EXPORTFORMAT.md`.

## Optional Windows Build

```bash
build_exe.bat
```

Build output under `build/`, `dist/`, and `releases/` stays local and does not belong in the Git repository. The build uses a local work directory under `C:\_Local_DEV\codex_build\dokureader` and updates `dist\DokuReader.exe`.

## Platform Strategy

The desktop app remains the authoritative local library. Windows Store is the first distribution target; macOS and Linux are tracked as source and smoke-test targets from the same Tkinter codebase. For Android, iOS, and browser use, a later Web/PWA companion based on `dokureader-library-v1.json` is more appropriate than a full native clone because mobile sandboxes cannot freely access local desktop document paths.

The reproducible desktop source smoke lives in `tests/source_platform_smoke.py`. It covers app start, `open`/`xdg-open` dispatch, text and PDF preview, simulated LibreOffice conversion, and merged PDF export without touching real user state.

The mobile companion now also has a reproducible PWA smoke under
`web_companion/`: `npm test` validates manifest metadata, offline-shell assets,
and the demo library for Android/iOS-style install flows without introducing a
native duplicate app line.

## Supported File Formats

- Documents: `.txt`, `.doc`, `.docx`, `.pdf`, `.odt`, `.rtf`
- Images: `.jpg`, `.jpeg`, `.gif`, `.png`

## Project Files

- `DokuReader.py` - main application
- `requirements.txt` - Python dependencies
- `DokuReader.spec` - PyInstaller configuration
- `EXPORTFORMAT.md` - schema for `dokureader-library-v1.json`
- `web_companion/README.md` - PWA/mobile smoke workflow for Android and iOS
- `STORE_LISTING.md` - Windows Store copy in German and English
- `PRIVACY_POLICY.md` - privacy notes for the Store release
- `SUPPORT.md` - support and contact paths
- `llms.txt` - machine-readable project context
- `locales/translations.json` - translation data
- `THIRD_PARTY_LICENSES.txt` - third-party license summary
- `SECURITY.md` - vulnerability reporting guidance
- `CONTRIBUTING.md` - contribution guidelines

## License

This project is licensed under the [GNU Affero General Public License v3.0](LICENSE). AGPL-3.0 is appropriate because DokuReader can optionally use PyMuPDF, which is also licensed under AGPL-3.0.

## Liability

This project is provided without warranty. Use, testing, and processing of your own documents are at your own risk. The warranty and liability disclaimers of AGPL-3.0 apply.
