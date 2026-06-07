# Changelog / Änderungsprotokoll

Alle wesentlichen Änderungen an diesem Projekt werden hier dokumentiert.
Format basiert auf [Keep a Changelog](https://keepachangelog.com/de/1.1.0/).

## [Unreleased]

### Geändert / Changed
- PDF-Merge von `PdfMerger` auf `PdfWriter` migriert (pypdf 4.x/5.x-kompatibel). `PdfMerger` wurde in pypdf 4.0.0 entfernt. Versions-Pin `pypdf<4.0.0` aufgehoben → `pypdf>=4.0.0`.

### Build / Release
- EXE neu gebaut 2026-06-01 (PyInstaller, `DokuReader.spec` → `C:\_Local_DEV\codex_build\dokureader`); 5/5 Tests grün, Smoke-Test bestanden. Vorherige EXE: 2026-05-22, Anlass: DokuReader.py 2026-05-26.

### Hinzugefügt / Added
- GitHub Actions CI-Workflow `source-platform-smoke.yml`: führt `tests/source_platform_smoke.py` auf `ubuntu-latest` (mit Xvfb) und `macos-latest` bei jedem Push/PR auf main aus.

### Behoben / Fixed
- Windows-App-Icon und PyInstaller-Spec für lokale Windows-Builds.
- `PORTIERUNGSPLAN.md` mit Plattformentscheidung für Windows Store, macOS/Linux-Smokes und Web/PWA-Companion auf Basis von `dokureader-library-v1.json`.
- `EXPORTFORMAT.md` für das stabile Austauschformat `dokureader-library-v1.json`.
- GUI-Export `Bibliothek (JSON)` für Themen, Dokumentpfade, Dateimetadaten und Lesestatus ohne Dokumentinhalte.
- Windows-Store-Unterlagen mit `STORE_LISTING.md`, `PRIVACY_POLICY.md`, `SUPPORT.md` und `store_package.json`; Screenshots werden lokal unter dem ungetrackten `releases/windowsstore/` erzeugt.
- Reproduzierbare Store-Medien via `_WARTUNG/generate_store_media.py` für Screenshots und Basis-Store-Assets.
- `tests/source_platform_smoke.py` als reproduzierbarer macOS/Linux-Desktop-Smoke für Start, Dateiaufruf, Vorschau, LibreOffice-Fallback und Sammel-PDF.
- `README_de.md` als deutsche Root-Dokumentation und `llms.txt` als maschinenlesbarer Projektkontext.
- `web_companion/package.json`, `web_companion/README.md` und `web_companion/tests/pwa_mobile_smoke.test.mjs` für einen reproduzierbaren Android-/iOS-nahen PWA-Smoke.
- Mobile PWA-Icons und Manifest-Metadaten für installierbare Add-to-Home-Screen-Läufe.

### Geändert / Changed
- README um die Plattformstrategie und den Verweis auf den Portierungsplan ergänzt.
- README um den JSON-Export und die Exportformat-Dokumentation ergänzt.
- README auf English-first GitHub-Dokumentation ausgerichtet; die deutsche Fassung bleibt separat erhalten.
- `PORTIERUNGSPLAN.md` auf den neuen Store-Readiness-Stand synchronisiert.
- README und README_de dokumentieren jetzt den neuen Desktop-Source-Smoke für macOS/Linux.
- `web_companion/index.html`, `manifest.webmanifest`, `style.css` und `sw.js` für mobile Safe-Areas, PWA-Install-Metadaten und Offline-Shell-Caching nachgezogen.
- Öffentliche README-Verweise auf den lokal gehaltenen, nicht getrackten Portierungsplan entfernt.
- Windows-Build über `build_exe.bat` auf lokalen Arbeitsordner außerhalb von OneDrive umgestellt; `START.bat` startet bevorzugt die gebaute EXE mit Python-Fallback.
- README-Screenshotpfad auf `README/screenshots/main.png` vereinheitlicht.
- README um Encoding-Fallback und Drittanbieter-Lizenzübersicht ergänzt.
- `.gitignore` um lokale Build-Artefakte, Secrets und interne Steuerungsdateien erweitert.
- `.gitattributes` für stabile Zeilenenden und Binärdateien ergänzt.
- README, Security Policy und Beitragsrichtlinie auf aktuellen Repository-Hygiene-Stand gebracht.
- Welcome-Workflow um Hinweis auf nicht öffentliche Sicherheits- und Privatdaten ergänzt.

### Behoben / Fixed
- Text-Fallback für Vorschau und TXT->PDF-Export korrigiert, damit Latin-1-Dateien nicht als Ersatzzeichen angezeigt werden.
- Veraltete Beitrags- und Startanweisungen in `CONTRIBUTING.md` korrigiert.
- Direkte Kontakt-E-Mail aus dem Code of Conduct entfernt; GitHub-Kanäle werden genutzt.
- Fehlende Store-Beschreibung, Screenshot-Basis und AGPL-/PyMuPDF-Hinweise für den geplanten kostenlosen Windows-Store-Release ergänzt.

## [1.0.0] - 2026-02-24

### Hinzugefügt / Added
- Erstveröffentlichung / Initial release
