<img src="assets/banner.svg" width="100%" alt="DokuReader Banner">

# DokuReader — Dokumentenbibliothek

**[🇬🇧 English](README.md)** · **🇩🇪 Deutsch**

> Dokumente nach Themen verwalten, vorschauen und bündeln — nur Verweise und Lesestatus, Originale bleiben am Platz.

[![Lizenz: AGPL-3.0](https://img.shields.io/badge/License-AGPL--3.0-green)](LICENSE)
[![Version](https://img.shields.io/badge/Version-1.0.1--dev-blue)](CHANGELOG.md#unreleased)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](pyproject.toml)
[![Plattform: Windows](https://img.shields.io/badge/Platform-Windows-blue?logo=windows)](#einstieg)
[![Tests: 36 passed](https://img.shields.io/badge/Tests-36%20passed-success?logo=pytest)](pyproject.toml)
[![LLM-Ready: llms.txt](https://img.shields.io/badge/LLM--Ready-llms.txt-success)](llms.txt)
[![Ökosystem: doc-bricks](https://img.shields.io/badge/%C3%96kosystem-doc--bricks-purple)](https://github.com/doc-bricks)
[![Dachorganisation: open-bricks](https://img.shields.io/badge/Dachorganisation-open--bricks-blue)](https://github.com/open-bricks)


> [!NOTE]
> DokuReader ist Teil der **doc-bricks** Suite für lokales Dokumentenmanagement. Es ergänzt [LitZentrum](https://github.com/doc-bricks/LitZentrum) (Literatur- & Zitationsverwaltung), [CleanMarkdown](https://github.com/doc-bricks/CleanMarkdown) (Markdown-Lese- & Editierumgebung) und [UniversalDocsGrabber](https://github.com/doc-bricks/UniversalDocsGrabber) (Mail-Anhang-Import). DokuReader ist für KI/LLM-Entwicklungsassistenten über [`llms.txt`](llms.txt) indexiert.

DokuReader ist eine lokale Desktop-Anwendung zum Verwalten, Vorschauen und Bündeln von Dokumenten nach Themen. Originaldateien bleiben an ihrem Speicherort; die Anwendung speichert nur Verweise und Lesestatus in einer lokalen JSON-Datei.

DokuReader eignet sich für private Dokumentenbibliotheken, Forschungsordner, PDF-Sammlungen und thematische Leseablagen, die bewusst lokal und nachvollziehbar bleiben sollen.

## Einstieg

| Ziel | Einstieg |
|---|---|
| Desktop-App starten | `python DokuReader.py` oder `START.bat` |
| Exportformat verstehen | `EXPORTFORMAT.md` |
| Desktop-Quellstand testen | `python tests/source_platform_smoke.py` |
| Mobile/PWA-Companion prüfen | `web_companion/README.md` |
| Windows-Store-Readiness prüfen | `python _WARTUNG/check_store_readiness.py --allow-blockers` |
| WACK-Reports vorbereiten oder parsen | `python _WARTUNG/run_windows_wack.py --dry-run` |
| Windows-Store-Texte vorbereiten | `STORE_LISTING.md`, `PRIVACY_POLICY.md`, `SUPPORT.md` |
| LLM-Tools Projektkontext geben | `llms.txt` |

## Versions- und Release-Status

Die Versionsrollen sind bewusst getrennt und aus dem aktuellen Quellstand
abgelesen: Die Entwicklungs-Runtime ist `1.0.1-dev` (`DokuReader.py` und
`pyproject.toml` `1.0.1.dev0`), die Windows-Store-Metadaten stehen auf `1.0.1.0`
(`store_package.json`), und ein öffentlich belegtes Release-Artefakt liegt in
diesem Repository nicht vor. Der ignorierte `releases/`-Baum, Signierung, MSIX,
WACK und Store-Einreichung bleiben externe Gates; das Badge `1.0.1-dev` ist kein
Release-Claim. Siehe [RELEASE_STATUS.md](RELEASE_STATUS.md) und
[PORTIERUNGSPLAN.md](PORTIERUNGSPLAN.md).

## Auffindbarkeit

DokuReader ist am treffendsten als lokale Dokumentenbibliothek, themenbasierter PDF-Organizer, Lesestatus-Tracker und Metadaten-Exportwerkzeug beschrieben. Es ist kein Cloud-Dokumentenmanager, gehosteter OCR-Dienst, allgemeines Notizprogramm oder vollständiges Literaturverwaltungs-/Zitationssystem.

Nützliche Suchphrasen sind `local-first document library`, `topic based PDF organizer`, `document read status tracker`, `metadata-only document export`, `Tkinter document manager` und `offline PDF bundling desktop app`.

## Einsatz und Abgrenzung

| Bedarf | DokuReader eignet sich für |
|---|---|
| Leseablage aufbauen | PDFs, Office-Dateien, Texte und Bilder nach Themen gruppieren, ohne Originale zu verschieben |
| Bearbeitungsstand verfolgen | Dokumente als gelesen oder ungelesen markieren und Exporte danach filtern |
| Bibliotheksübersicht teilen | `dokureader-library-v1.json` mit Pfaden, Metadaten, Themen und Lesestatus exportieren |
| Lokales PDF-Bündel erstellen | Aus gelesenen, ungelesenen oder allen Dokumenten ein Sammel-PDF erzeugen |

Innerhalb der doc-bricks-Familie ist DokuReader die private Lese- und Dokumentenbibliothek. `LitZentrum` deckt Literaturverwaltung und Zitation ab, `CleanMarkdown` ist für Markdown-Lesen und -Bearbeitung zuständig, und `UniversalDocsGrabber` übernimmt den Mail-Anhang-Import.

## Systemarchitektur

```mermaid
graph TD
    subgraph Desktop ["Desktop Client (Python / Tkinter)"]
        UI["DokuReader.py"]
        State["State Manager (~/.dokubibliothek_state.json)"]
        Preview["Dateivorschau (PDF, Bilder, Text, Office)"]
        Exporter["Export Engine (PyMuPDF / reportlab / LibreOffice)"]
        UI --> State
        UI --> Preview
        UI --> Exporter
    end

    subgraph Output ["Daten-Exporte & Weitergabe"]
        Exporter --> PDFBundle["Sammel-PDF (Merged PDF)"]
        Exporter --> JSONExport["dokureader-library-v1.json (Metadaten & Lesestatus)"]
    end

    subgraph Companion ["PWA / Mobile Companion (web_companion)"]
        JSONExport -. Import / Sync .-> CompanionPWA["Offline PWA / Mobile Web App"]
        CompanionPWA -. Export aktualisierter Lesestatus .-> JSONExport
    end
```

## Funktionen

- Themen für Dokumente erstellen, umbenennen und löschen
- Dokumente als gelesen oder ungelesen markieren
- Vorschau für Bilder, PDFs, Textdateien sowie DOCX/ODT-Dokumente
- Textvorschau und TXT-zu-PDF-Export mit UTF-8- und Latin-1-Fallback
- Dateien per Drag & Drop hinzufügen, wenn `tkinterdnd2` installiert ist
- Originaldokumente per Doppelklick in der Standardanwendung öffnen
- Batch-PDF-Export für alle, gelesene oder ungelesene Dokumente
- JSON-Export der gesamten Bibliothek als `dokureader-library-v1.json`
- Office-zu-PDF-Konvertierung über LibreOffice oder Microsoft Word
- Lokaler Windows-Build über die PyInstaller-Spec

## Datenschutz und lokale Daten

- DokuReader arbeitet lokal und lädt keine Dokumente in externe Dienste hoch.
- Originaldateien werden nicht kopiert oder verändert.
- Der Status wird in `~/.dokubibliothek_state.json` gespeichert.
- Der Standardexport enthält Themen, Pfade, Dateimetadaten und Lesestatus, aber keine Dokumentinhalte.
- Lokale Build-Artefakte, Release-Dateien, interne Aufgabenlisten und Konvertierungsnotizen sind per `.gitignore` ausgeschlossen.

## Screenshot

![DokuReader-Hauptfenster](README/screenshots/main.png)

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
- Poppler für die optionale `pdf2image`-Vorschau
- Microsoft Word unter Windows für die optionale Word-COM-Konvertierung

## Verwendung

```bash
python DokuReader.py
```

Unter Windows kann alternativ die Startdatei verwendet werden:

```bash
START.bat
```

Für den Companion-Export kann in der App rechts der Bereich `Bibliothek (JSON)` genutzt werden. Er schreibt Themen, Pfade, Dateimetadaten und Lesestatus in `dokureader-library-v1.json`, ohne Dokumentinhalte zu kopieren. Das Format ist in `EXPORTFORMAT.md` dokumentiert.

## Optionaler Windows-Build

```bash
build_exe.bat
```

Build-Ausgaben unter `build/`, `dist/` und `releases/` bleiben lokal und gehören nicht in das Git-Repository. Der Build nutzt einen lokalen Arbeitsordner unter `C:\_Local_DEV\codex_build\dokureader` und aktualisiert `dist\DokuReader.exe`.

## Windows-Store-Readiness

```bash
python _WARTUNG/check_store_readiness.py --allow-blockers
```

Der Check prüft Store-Metadaten, öffentliche Privacy-/Support-URLs, Pflichtdokumente, Store-Assets, generierte Screenshots, eine lokale EXE sowie die verbleibenden MSIX-/WACK-Artefakte. `--allow-blockers` ist für lokale Pre-Submission-Läufe gedacht, bei denen Partner Center, MSIX-Signierung oder der erhöhte WACK-Lauf noch externe Gates sind.

Der WACK-Runner macht den erhöhten Zertifizierungsschritt reproduzierbar:

```bash
python _WARTUNG/run_windows_wack.py --dry-run
```

Der Dry-Run zeigt den erwarteten MSIX-Pfad, den XML-Reportpfad, gefundenes `appcert.exe` und den exakten Zertifizierungsbefehl. Der echte Lauf muss nach einem frisch signierten MSIX in einer erhöhten PowerShell ausgeführt werden. Vorhandene XML-Reports lassen sich in die JSON-Zusammenfassung umwandeln, die das Readiness-Gate auswertet:

```bash
python _WARTUNG/run_windows_wack.py --parse-report releases/windowsstore/test_reports/wack_YYYYMMDD_HHMMSS.xml
```

## Plattformstrategie

Die Desktop-App bleibt die autoritative lokale Bibliothek. Windows Store ist der erste Distributionskanal; macOS und Linux werden als Source- und Smoke-Test-Ziele aus derselben Tkinter-Codebasis geführt. Für Android, iOS und Browser ist ein späterer Web/PWA-Companion auf Basis von `dokureader-library-v1.json` sinnvoller als ein nativer Voll-Clone, weil mobile Sandboxes keinen freien Zugriff auf die lokalen Desktop-Dokumentpfade haben.

Der reproduzierbare Desktop-Source-Smoke liegt in `tests/source_platform_smoke.py`. Er prüft App-Start, `open`-/`xdg-open`-Aufrufe, Text- und PDF-Vorschau, simulierte LibreOffice-Konvertierung und Sammel-PDF-Export, ohne echten Nutzerstatus zu berühren.

Für den mobilen Pfad gibt es jetzt zusätzlich einen reproduzierbaren PWA-Smoke
unter `web_companion/`: `npm test` prüft Manifest, Offline-Shell und die
Demo-Bibliothek für Android-/iOS-nahe Installationsläufe, ohne eine native
Doppel-App aufzubauen.

## Unterstützte Dateiformate

- Dokumente: `.txt`, `.doc`, `.docx`, `.pdf`, `.odt`, `.rtf`
- Bilder: `.jpg`, `.jpeg`, `.gif`, `.png`

## Projektdateien

- `DokuReader.py` - Hauptanwendung
- `requirements.txt` - Python-Abhängigkeiten
- `DokuReader.spec` - PyInstaller-Konfiguration
- `EXPORTFORMAT.md` - Schema für `dokureader-library-v1.json`
- `_WARTUNG/check_store_readiness.py` - Windows-Store-Readiness-Gate
- `_WARTUNG/run_windows_wack.py` - WACK-Dry-Run, echter Lauf und XML-zu-JSON-Zusammenfassung
- `web_companion/README.md` - PWA-/Mobile-Smoke für Android und iOS
- `STORE_LISTING.md` - Store-Texte für Windows Store (DE/EN)
- `PRIVACY_POLICY.md` - Datenschutzhinweise für den Store-Release
- `SUPPORT.md` - Support- und Kontaktwege
- `llms.txt` - maschinenlesbarer Projektkontext
- `locales/translations.json` - Übersetzungsdaten
- `THIRD_PARTY_LICENSES.txt` - Drittanbieter-Lizenzübersicht
- `SECURITY.md` - Hinweise zum Melden von Sicherheitslücken
- `CONTRIBUTING.md` - Beitragsrichtlinien

## Lizenz

Dieses Projekt steht unter der [GNU Affero General Public License v3.0](LICENSE). Die AGPL-3.0 ist passend, weil DokuReader optional PyMuPDF nutzt, das ebenfalls AGPL-3.0-lizenziert ist.

## Haftung

Dieses Projekt wird ohne Gewährleistung bereitgestellt. Nutzung, Tests und Verarbeitung eigener Dokumente erfolgen auf eigenes Risiko. Es gilt die Haftungs- und Gewährleistungsausschlussregelung der AGPL-3.0.
