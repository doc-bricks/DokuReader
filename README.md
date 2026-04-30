# DokuReader - Dokumentenbibliothek

DokuReader ist eine lokale Desktop-Anwendung zum Verwalten, Vorschauen und Bündeln von Dokumenten nach Themen.
Originaldateien bleiben an ihrem Speicherort; die Anwendung speichert nur Verweise und Lesestatus in einer lokalen JSON-Datei.

## Funktionen

- Themen für Dokumente erstellen, umbenennen und löschen
- Dokumente als gelesen oder ungelesen markieren
- Vorschau für Bilder, PDFs, Textdateien sowie DOCX/ODT-Dokumente
- Dateien per Drag & Drop hinzufügen, wenn `tkinterdnd2` installiert ist
- Dokumente per Doppelklick in der Standardanwendung öffnen
- Batch-PDF-Export für alle, gelesene oder ungelesene Dokumente
- Office-zu-PDF-Konvertierung über LibreOffice oder Microsoft Word
- Windows-Icon und PyInstaller-Spec für lokale Windows-Builds

## Datenschutz und lokale Daten

- DokuReader arbeitet lokal und lädt keine Dokumente in externe Dienste hoch.
- Originaldateien werden nicht kopiert oder verändert.
- Der Status wird in `~/.dokubibliothek_state.json` gespeichert.
- Lokale Build-Artefakte, Release-Dateien, interne Aufgabenlisten und Konvertierungsnotizen sind per `.gitignore` ausgeschlossen.

## Screenshots

![Hauptfenster](README/screenshots/main.png)

## Installation

### Voraussetzungen

- Python 3.10+
- Tkinter, normalerweise in Standard-Python-Installationen enthalten

### Python-Abhängigkeiten

```bash
pip install -r requirements.txt
```

`requirements.txt` enthält die unterstützten Python-Integrationen für Vorschau, Drag & Drop und PDF-Export. Fehlende optionale Pakete deaktivieren nur die jeweilige Zusatzfunktion.

### Optionale Systemabhängigkeiten

Für volle Vorschau- und Exportfunktionalität:

- LibreOffice für DOC/DOCX/ODT/RTF zu PDF
- Poppler für `pdf2image`, falls diese Vorschau-Variante genutzt wird
- Microsoft Word unter Windows für die optionale Word-COM-Konvertierung

## Verwendung

```bash
python DokuReader.py
```

Unter Windows kann alternativ die Startdatei verwendet werden:

```bash
START.bat
```

## Optionaler Windows-Build

```bash
pyinstaller DokuReader.spec
```

Build-Ausgaben unter `build/`, `dist/` und `releases/` bleiben lokal und gehören nicht in das Git-Repository.

## Unterstützte Dateiformate

- Dokumente: `.txt`, `.doc`, `.docx`, `.pdf`, `.odt`, `.rtf`
- Bilder: `.jpg`, `.jpeg`, `.gif`, `.png`

## Projektdateien

- `DokuReader.py` - Hauptanwendung
- `requirements.txt` - Python-Abhängigkeiten
- `DokuReader.spec` - PyInstaller-Konfiguration
- `locales/translations.json` - Übersetzungsdaten
- `SECURITY.md` - Hinweise zum Melden von Sicherheitslücken
- `CONTRIBUTING.md` - Beitragsrichtlinien

## Lizenz

Dieses Projekt steht unter der [GNU Affero General Public License v3.0](LICENSE).
Die AGPL-3.0 ist passend, weil DokuReader optional PyMuPDF nutzt, das ebenfalls AGPL-3.0-lizenziert ist.

## Haftung

Dieses Projekt wird ohne Gewährleistung bereitgestellt. Nutzung, Tests und Verarbeitung eigener Dokumente erfolgen auf eigenes Risiko.
Es gilt die Haftungs- und Gewährleistungsausschlussregelung der AGPL-3.0.

---

## English

# DokuReader - Document Library

DokuReader is a local desktop application for organizing, previewing, and bundling documents by topic.
Original files remain where they are; the application stores only references and read status in a local JSON file.

## Features

- Create, rename, and delete document topics
- Mark documents as read or unread
- Preview images, PDFs, text files, and DOCX/ODT documents
- Add files via drag and drop when `tkinterdnd2` is installed
- Open documents in the default application by double-clicking
- Export all, read, or unread documents as a combined PDF
- Convert Office documents to PDF through LibreOffice or Microsoft Word
- Windows icon and PyInstaller spec for local Windows builds

## Privacy and Local Data

- DokuReader runs locally and does not upload documents to external services.
- Original files are not copied or modified.
- State is stored in `~/.dokubibliothek_state.json`.
- Local build artifacts, release files, internal task notes, and conversion scratch files are excluded via `.gitignore`.

## Screenshots

![Main window](README/screenshots/main.png)

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
- Poppler for `pdf2image`, if that preview backend is used
- Microsoft Word on Windows for optional Word COM conversion

## Usage

```bash
python DokuReader.py
```

On Windows, the start file can be used instead:

```bash
START.bat
```

## Optional Windows Build

```bash
pyinstaller DokuReader.spec
```

Build output under `build/`, `dist/`, and `releases/` stays local and does not belong in the Git repository.

## Supported File Formats

- Documents: `.txt`, `.doc`, `.docx`, `.pdf`, `.odt`, `.rtf`
- Images: `.jpg`, `.jpeg`, `.gif`, `.png`

## Project Files

- `DokuReader.py` - main application
- `requirements.txt` - Python dependencies
- `DokuReader.spec` - PyInstaller configuration
- `locales/translations.json` - translation data
- `SECURITY.md` - vulnerability reporting guidance
- `CONTRIBUTING.md` - contribution guidelines

## License

This project is licensed under the [GNU Affero General Public License v3.0](LICENSE).
AGPL-3.0 is appropriate because DokuReader can optionally use PyMuPDF, which is also licensed under AGPL-3.0.

## Liability

This project is provided without warranty. Use, testing, and processing of your own documents are at your own risk.
The warranty and liability disclaimers of AGPL-3.0 apply.
