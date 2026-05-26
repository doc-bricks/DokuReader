# Changelog / Änderungsprotokoll

Alle wesentlichen Änderungen an diesem Projekt werden hier dokumentiert.
Format basiert auf [Keep a Changelog](https://keepachangelog.com/de/1.1.0/).

## [Unreleased]

### Hinzugefügt / Added
- Windows-App-Icon und PyInstaller-Spec für lokale Windows-Builds.
- `PORTIERUNGSPLAN.md` mit Plattformentscheidung für Windows Store, macOS/Linux-Smokes und Web/PWA-Companion auf Basis von `dokureader-library-v1.json`.

### Geändert / Changed
- README um die Plattformstrategie und den Verweis auf den Portierungsplan ergänzt.
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

## [1.0.0] - 2026-02-24

### Hinzugefügt / Added
- Erstveröffentlichung / Initial release
