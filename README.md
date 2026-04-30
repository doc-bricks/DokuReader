# DokuReader - Dokumentenbibliothek

Eine einfache Desktop-Anwendung zur Verwaltung und Organisation von Dokumenten nach Themen mit Vorschau-Funktion und PDF-Export.

## Features

- **Themen-Organisation**: Themen fuer Dokumente erstellen, umbenennen und loeschen
- **Gelesen/Ungelesen**: Dokumente als gelesen markieren (gruen mit Haekchen)
- **Vorschau**:
  - Bilder (JPG, PNG, GIF)
  - PDF-Dokumente (erste Seite)
  - Textdateien (TXT)
  - Office-Dokumente (DOCX, ODT)
- **Drag & Drop**: Dateien einfach per Drag & Drop hinzufuegen (optional)
- **Doppelklick-Oeffnen**: Dokumente in der Standardanwendung oeffnen
- **Batch-PDF-Export**: Alle, gelesene oder ungelesene Dokumente als einzelnes PDF exportieren
  - Unterstuetzt: PDF, TXT, Bilder, DOC, DOCX, ODT, RTF
  - Automatische Konvertierung zu PDF (LibreOffice oder MS Word)
- **Windows-Icon**: Projekt-Icon fuer Fenster und PyInstaller-Builds
- **Plattformuebergreifend**: Windows, macOS, Linux

## Technische Details

- Python 3.10+ mit Tkinter
- Einzeldatei-Anwendung mit Tkinter-GUI
- JSON-basierte Speicherung im Home-Verzeichnis
- Nur Referenzen: Originaldateien bleiben unberuehrt

## Screenshots

![Hauptfenster](README/screenshots/main.png)

## Installation

### Erforderliche Abhaengigkeiten

```bash
pip install -r requirements.txt
```

### Optionale Abhaengigkeiten

Fuer volle Funktionalitaet:
- `pdf2image` oder `PyMuPDF` - PDF-Vorschau
- `tkinterdnd2` - Drag & Drop
- `python-docx` - DOCX-Vorschau
- `odfpy` - ODT-Vorschau
- `reportlab` - TXT/Bild zu PDF-Konvertierung
- `pypdf` oder `PyPDF2` - PDF-Zusammenfuehrung
- `pywin32` (Windows) - Word COM fuer Office-Konvertierung

### LibreOffice (fuer Office → PDF Konvertierung)

Fuer beste Unterstuetzung von DOC/DOCX/ODT/RTF → PDF:
- **Linux**: `sudo apt-get install libreoffice`
- **macOS**: `brew install --cask libreoffice`
- **Windows**: Download von https://www.libreoffice.org/

## Verwendung

```bash
python DokuReader.py
```

Oder via START.bat (Windows):
```bash
START.bat
```

### Optionaler Windows-Build

```bash
pyinstaller DokuReader.spec
```

## Datenspeicherung

Status wird gespeichert in: `~/.dokubibliothek_state.json`

## Unterstuetzte Dateiformate

- Dokumente: `.txt`, `.doc`, `.docx`, `.pdf`, `.odt`, `.rtf`
- Bilder: `.jpg`, `.jpeg`, `.gif`, `.png`

## Lizenz

AGPL v3 - Siehe [LICENSE](LICENSE)

Dieses Projekt verwendet PyMuPDF (AGPL-3.0), daher gilt die AGPL-Lizenz.

---

## English

# DokuReader - Document Library

A simple desktop application for managing and organizing documents by topic with preview functionality and PDF export.

### Features

- **Topic Organization**: Create, rename, and delete topics for your documents
- **Read/Unread**: Mark documents as read (green with checkmark)
- **Preview**:
  - Images (JPG, PNG, GIF)
  - PDF documents (first page)
  - Text files (TXT)
  - Office documents (DOCX, ODT)
- **Drag & Drop**: Easily add files via drag and drop (optional)
- **Double-Click Open**: Open documents in the default application
- **Batch PDF Export**: Export all, read, or unread documents as a single PDF
  - Supports: PDF, TXT, images, DOC, DOCX, ODT, RTF
  - Automatic conversion to PDF (LibreOffice or MS Word)
- **Windows icon**: Project icon for the app window and PyInstaller builds
- **Cross-Platform**: Windows, macOS, Linux

### Technical Details

- Python 3.10+ with Tkinter
- Single-file Tkinter application
- JSON-based persistence in the home directory
- Reference-only: Original files remain untouched

### Screenshots

![Main Window](README/screenshots/main.png)

### Installation

#### Required Dependencies

```bash
pip install -r requirements.txt
```

#### Optional Dependencies

For full functionality:
- `pdf2image` or `PyMuPDF` - PDF preview
- `tkinterdnd2` - Drag & Drop
- `python-docx` - DOCX preview
- `odfpy` - ODT preview
- `reportlab` - TXT/image to PDF conversion
- `pypdf` or `PyPDF2` - PDF merge
- `pywin32` (Windows) - Word COM for Office conversion

#### LibreOffice (for Office → PDF conversion)

For best support of DOC/DOCX/ODT/RTF → PDF:
- **Linux**: `sudo apt-get install libreoffice`
- **macOS**: `brew install --cask libreoffice`
- **Windows**: Download from https://www.libreoffice.org/

### Usage

```bash
python DokuReader.py
```

Or via START.bat (Windows):
```bash
START.bat
```

#### Optional Windows build

```bash
pyinstaller DokuReader.spec
```

### Data Storage

State is saved in: `~/.dokubibliothek_state.json`

### Supported File Formats

- Documents: `.txt`, `.doc`, `.docx`, `.pdf`, `.odt`, `.rtf`
- Images: `.jpg`, `.jpeg`, `.gif`, `.png`

### License

AGPL v3 - See [LICENSE](LICENSE)

This project uses PyMuPDF (AGPL-3.0), therefore the AGPL license applies.

---

## Haftung / Liability

Dieses Projekt ist eine **unentgeltliche Open-Source-Schenkung** im Sinne der §§ 516 ff. BGB. Die Haftung des Urhebers ist gemäß **§ 521 BGB** auf **Vorsatz und grobe Fahrlässigkeit** beschränkt. Ergänzend gelten die Haftungsausschlüsse aus GPL-3.0 / MIT / Apache-2.0 §§ 15–16 (je nach gewählter Lizenz).

Nutzung auf eigenes Risiko. Keine Wartungszusage, keine Verfügbarkeitsgarantie, keine Gewähr für Fehlerfreiheit oder Eignung für einen bestimmten Zweck.

This project is an unpaid open-source donation. Liability is limited to intent and gross negligence (§ 521 German Civil Code). Use at your own risk. No warranty, no maintenance guarantee, no fitness-for-purpose assumed.

