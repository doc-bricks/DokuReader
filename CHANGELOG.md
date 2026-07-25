# Changelog / Änderungsprotokoll

Alle wesentlichen Änderungen an diesem Projekt werden hier dokumentiert.
Format basiert auf [Keep a Changelog](https://keepachangelog.com/de/1.1.0/).

## [Unreleased]

### Hinzugefügt / Added
- `pyproject.toml`: PEP 621-konformes Projekt-Metadaten- und Build-System inklusive Pytest-Konfiguration angelegt
- Erster Design-Refresh-Slice für die Desktop-Oberfläche: `DokuReader.py`
  rendert jetzt einen klareren Kopfbereich mit Untertitel, ein ruhigeres
  Farbsystem, konsistentere Karten-/Toolbar-Stile sowie aufgeräumtere
  Such-, Themen-, Dokument- und Exportflächen, ohne das bestehende
  Bedienmodell zu ändern.
- Windows-Store-Readiness-Gate `_WARTUNG/check_store_readiness.py` ergänzt. Es prüft
  Store-Metadaten, öffentliche Privacy-/Support-URLs, Pflichtdokumente, Store-Assets,
  Screenshots, EXE, MSIX, WACK-Runner und geparste WACK-JSON-Zusammenfassungen und
  kann erwartete externe Store-Blocker per `--allow-blockers` transparent ausgeben.
- WACK-Runner `_WARTUNG/run_windows_wack.py` ergänzt. Er bietet Dry-Run-Pfade,
  kontrollierte `appcert.exe`-Ausführung, Admin-/Tool-Blocker und `--parse-report`
  für XML-zu-JSON-Zusammenfassungen.
- Desktop-Dokumentliste hat jetzt einen sichtbaren Einstieg `Aktionen…` für
  `Als gelesen markieren`, `Gelesen-Markierung entfernen` und `Aus Bibliothek entfernen`.
  Derselbe Menüpfad ist zusätzlich per `Shift+F10` und Kontextmenü-Taste
  tastaturfreundlich erreichbar.

### Behoben / Fixed
- Der Bereich `Sammel-PDF` spiegelt seine Verfügbarkeit jetzt direkt im UI:
  Ohne aktuelles Thema oder ohne passende Dokumente bleibt die Exportaktion
  deaktiviert und erklärt den Zustand mit einer kurzen Statuszeile, statt erst
  nach dem Klick einen Hinweisdialog zu zeigen.
- Regressionstest für den macOS-/Linux-Dateiöffner prüft jetzt die kanonische
  `DokuReader.py` statt einer privaten Workstation-Kopie, damit die öffentliche
  Testsuite ohne lokale Zusatzdateien lauffähig bleibt.
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
- `llms.txt`: Last-checked Datum auf 2026-07-25 aktualisiert
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
- GUI-Regression erweitert: `tests/test_ui_accessibility.py` prüft jetzt zusätzlich den
  sichtbaren `Aktionen…`-Button und den Tastaturzugang zum Dokument-Kontextmenü.
- `tests/test_ui_accessibility.py` deckt jetzt auch den direkt erklärten
  Verfügbarkeitszustand des Sammel-PDF-Exports für leere, passende und
  filterleere Themen ab.
- 1 neuer Regressionstest (web_companion): `BUG-W1 regression: sw.js fetch hat .catch() für Offline-Fallback`.
- 7 neue Tests (web_companion) für `setRead` und `serializeLibrary` (Round-Trip-Verifikation):
  `setRead` toggle/false-return, `serializeLibrary` Feldmapping, Round-Trip, Status-Erhalt.
  (Gesamt web_companion: 32 Node-Tests grün).

### Dokumentation / Documentation
- README und README_de um Workflow-Fit und Abgrenzung innerhalb der doc-bricks-Familie ergänzt; `llms.txt` auf den Sichtbarkeitscheck vom 2026-07-25 mit aktuellen Suchphrasen und External-Discovery-Notes synchronisiert.
