# Changelog / Änderungsprotokoll

Alle wesentlichen Änderungen an diesem Projekt werden hier dokumentiert.
Format basiert auf [Keep a Changelog](https://keepachangelog.com/de/1.1.0/).

## [Unreleased]

### Hinzugefügt / Added
- Windows-Store-Readiness-Gate `_WARTUNG/check_store_readiness.py` ergänzt. Es prüft
  Store-Metadaten, öffentliche Privacy-/Support-URLs, Pflichtdokumente, Store-Assets,
  Screenshots, EXE, MSIX und WACK-XML und kann erwartete externe Store-Blocker per
  `--allow-blockers` transparent ausgeben.

### Behoben / Fixed
- **BUG-D4**: `_split_dnd_paths` — `{` in Dateinamen (z.B. `bericht{2026}.txt`) wurde fälschlicherweise als
  DnD-Klammer-Öffner gewertet; alles davor Akkumulierte ging verloren. Fix: `{` wird nur als DnD-Trennzeichen
  gewertet, wenn der aktuelle Token noch leer ist.
- **BUG-D5**: `_split_dnd_paths` — `}` ohne vorherige öffnende Klammer spaltete den Token in zwei Teile.
  Fix: `}` schließt nur dann eine Klammer, wenn `in_brace=True`.
- **BUG-W1** (web_companion): `sw.js` `fetch`-Handler hatte keinen `.catch()`-Fallback — bei Netzwerkfehler
  warf der Service Worker unbehandelt, statt eine 503-Antwort zu liefern. Fix: `.catch()` gibt
  `new Response("Offline", { status: 503 })` zurück; CACHE-Version auf `v5` gebumpt.
- `manage_translations.py`: Fehler beim Lesen von `translations.json` (korrupte Datei / OS-Fehler) wurde nicht
  abgefangen — `json.JSONDecodeError` und `OSError` werden jetzt behandelt; Fallback auf leeres Dict.

### Geändert / Changed (Härtung / Hardening)
- `State.save()`: JSON-Serialisierung (`json.dumps`) läuft jetzt vollständig innerhalb des `_lock`,
  so dass kein anderer Thread `self.topics` mutieren kann, während der State geschrieben wird.
- `State.rename_topic(old, new)` und `State.remove_topic(topic)` als neue atomare, Lock-geschützte
  Methoden hinzugefügt. `App.rename_topic()` und `App.delete_topic()` nutzen diese Methoden
  statt direkter `dict`-Mutation auf `state_model.topics`.

### Hinzugefügt / Added (web_companion)
- **Lesestatus-Toggle + Export** (PORTIERUNGSPLAN Schritt 2):
  - `library.js`: `setRead(library, path, value)` schaltet den Gelesen-Status eines Dokuments anhand
    seines Pfads um (Pfad als stabiler Join-Key zum Desktop-Export).
  - `library.js`: `serializeLibrary(library)` serialisiert eine geparste Library zurück ins
    `dokureader-library-v1` JSON-Format (Feldnamen-Rückmapping: `sizeBytes→size_bytes` etc.).
    Das Desktop-Format wird ohne neue Schema-Version wiederverwendet — der Desktop kann es direkt
    reimportieren.
  - `app.js`: Dok-Karten sind jetzt klickbar und per Tastatur (Enter/Space) bedienbar; Klick
    schaltet Gelesen/Ungelesen um und re-rendert die Karte sofort.
  - `app.js`: Schaltfläche „Status exportieren" erscheint nach dem Laden einer Bibliothek;
    löst einen Browser-Download von `dokureader-library-v1.json` mit aktuellem Lesestatus aus.
  - `app.js`: `innerHTML` in `renderDocs`/`renderTopics` durch `replaceChildren()` und
    `textContent`-basierte DOM-Methoden ersetzt (kein XSS-Risiko durch statische Strings mehr).
  - `style.css`: `cursor: pointer` und `:hover/:focus-visible`-Border-Hervorhebung für Dok-Karten.
  - `index.html`: Schaltfläche `#export-btn` (initial `hidden`, wird nach Bibliotheksladung
    eingeblendet).

### Tests
- 16 neue Regressions- und Härtungstests für Desktop (Gesamt: 24 Python-Tests grün).
  - `TestD4SplitDndOeffnendeKlammer`: 3 Tests für BUG-D4
  - `TestD5SplitDndSchliessendekKlammer`: 2 Tests für BUG-D5
  - `TestThreadSafetyHaertung`: 6 Vertragstests für `rename_topic`, `remove_topic`, `save()`
- 1 neuer Regressionstest (web_companion): `BUG-W1 regression: sw.js fetch hat .catch() für Offline-Fallback`.
- 7 neue Tests (web_companion) für `setRead` und `serializeLibrary` (Round-Trip-Verifikation):
  `setRead` toggle/false-return, `serializeLibrary` Feldmapping, Round-Trip, Status-Erhalt.
  (Gesamt web_companion: 32 Node-Tests grün).

### Dokumentation / Documentation
- README, README_de und `llms.txt` um Einstiegstabelle, Suchphrasen, Zielgruppen und Abgrenzung für bessere GitHub-/Web-Auffindbarkeit ergänzt.

### Geändert / Changed
- PDF-Merge von `PdfMerger` auf `PdfWriter` migriert (pypdf 4.x/5.x-kompatibel). `PdfMerger` wurde in pypdf 4.0.0 entfernt. Versions-Pin `pypdf<4.0.0` aufgehoben → `pypdf>=4.0.0`.
- Suchleiste im Desktop-Fenster für kompakte, aber klarere Bedienung nachgeschärft: statt eines uneindeutigen `×`-Symbols gibt es jetzt die beschriftete Schaltfläche `Leeren`, die nur bei aktiver Suche aktiv ist; `Esc` leert die Suche direkt aus dem Suchfeld.

### Build / Release
- EXE neu gebaut 2026-06-01 (PyInstaller, `DokuReader.spec` → `C:\_Local_DEV\codex_build\dokureader`); 5/5 Tests grün, Smoke-Test bestanden. Vorherige EXE: 2026-05-22, Anlass: DokuReader.py 2026-05-26.

### Hinzugefügt / Added
- GitHub Actions CI-Workflow `source-platform-smoke.yml`: führt `tests/source_platform_smoke.py` auf `ubuntu-latest` (mit Xvfb) und `macos-latest` bei jedem Push/PR auf main aus.
- GUI-Regressionstest `tests/test_ui_accessibility.py` für die Suchleiste: prüft die beschriftete `Leeren`-Schaltfläche, den deaktivierten Leerzustand und das Tastatur-Zurücksetzen per `Esc`.

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
