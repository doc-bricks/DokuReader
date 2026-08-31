# Changelog / Änderungsprotokoll

Alle wesentlichen Änderungen an diesem Projekt werden hier dokumentiert.
Format basiert auf [Keep a Changelog](https://keepachangelog.com/de/1.1.0/).

## [Unreleased]

### Behoben / Fixed
- **Service-Worker-Cache-Isolation gehärtet (2026-08-31)**:
  - Der Aktivierungs-Handler löscht nur noch veraltete Cache-Versionen im
    Namensraum `dokureader-companion-`; Cache-Einträge anderer Anwendungen auf
    derselben Origin bleiben erhalten.
  - Ein verhaltensbasierter Node-Regressionstest belegt die Namespace-Grenze;
    der Web-Companion-Stand umfasst jetzt 33/33 grüne Tests.
- **macOS-/Linux-Runner-Beleg geschlossen (2026-08-26)**:
  - GitHub Actions Run `32918307130` für Commit `dc226c0` ist auf
    `macos-latest` und `ubuntu-latest` vollständig grün.
  - Der Portierungsplan trennt diesen Source-/Smoke-Beleg weiterhin klar von
    nicht geplanten signierten macOS-/Linux-Paketlinien.
- **Metadata-first UI-Polish abgeschlossen (2026-08-26)**:
  - Rechte Vorschau-/Exportspalte so verdichtet, dass Sammel-PDF und
    Bibliothek-JSON bei der belegten 1400×840-Ansicht vollständig sichtbar sind.
  - Themenaktionen umbrechen kontrolliert in zwei Zeilen; keine abgeschnittene
    Löschen-Aktion mehr. Sammel-PDF-Status steht in einer eigenen Zeile und
    Einzeldokumentzustände verwenden die korrekte Singularform.
  - Der Tk-Testaufbau begrenzt sporadische Initialisierungsfehler mit höchstens
    drei Versuchen. Zehn unabhängige Folgeläufe: 60/60 UI-Tests ohne Skip.
  - Synthetischer Win32-Visual-Smoke für Leer-, Drag-and-drop- und
    Textvorschauzustand ergänzt; kein Screenreader- oder Geräteclaim.
  - Finaler Gesamtreadback: 46/46 Python-Tests und 32/32 Web-Companion-Tests.
- **Versions- und Releaseflächen frisch synchronisiert (2026-08-26)**:
  - Runtime `1.0.1-dev`, Python `1.0.1.dev0` und Store-Paket `1.0.1.0` bleiben
    getrennte Rollen. GitHub hat weder Tags noch Releases; das lokale
    v1.0.0-EXE ist nur ein hashverifiziertes, nicht veröffentlichtes Artefakt.
  - Maschinenspezifischen absoluten Buildpfad aus beiden READMEs entfernt.
- **Testclaims zählen wieder getrennt statt summiert (2026-08-24)**:
  - Die Badges in `README.md` und `README_de.md` trugen `Tests: 70 passed`. Diese Zahl
    war eine Summe aus zwei verschiedenen Suiten (38 Pytest + 32 Node) und behauptete
    dabei etwas Falsches: Von den 38 Pytest-Tests waren 37 bestanden und einer
    übersprungen, es gab also nie 70 bestandene Tests. Die Aggregation verschluckte
    den Skip und machte die beiden Suiten ununterscheidbar — genau das, was ein
    Testbadge nicht tun darf.
  - Ersetzt durch zwei getrennte Badges: `Pytest: 45 tests, 0 failed` und
    `Web Companion: 32 passed`. Das Pytest-Badge nennt bewusst die gesammelte und
    die fehlgeschlagene Zahl statt der bestandenen: Letztere schwankt zwischen 44
    und 45, weil ein Test sporadisch überspringt (siehe nächster Abschnitt). Eine
    Zahl, die in einem Viertel der Läufe falsch ist, gehört nicht in ein Badge.
  - **Autoritativer Lauf** vom 2026-08-24 auf Commit `df41cf8`, Python 3.12.10
    (Windows), jede Suite einzeln und mit Exit-Code:
    - `python -X utf8 -m pytest -ra` → 45 gesammelt, 0 fehlgeschlagen, Exit 0
      (fünfzehn Läufe; 44–45 bestanden, siehe sporadischer Skip)
    - `node --test` in `web_companion/` → 32 bestanden, 0 fehlgeschlagen, Exit 0
    - `ruff check .` → All checks passed, Exit 0
    - `python tests/source_platform_smoke.py` → `source_platform_smoke: OK`, Exit 0
  - `RELEASE_STATUS.md` (38/37/1), `llms.txt` (`38+ tests, 100% clean` sowie
    `70 passed tests`) und `docs/con2_ANFORDERUNGSANALYSE.md` (`37 Pytest-Tests`,
    „Zwei erwartete Tkinter-Skips") auf denselben Lauf gebracht. Die Zahlen
    früherer Einträge bleiben unverändert und datiert.

### Geändert / Changed
- **Der „erwartete Tkinter-Skip" ist sporadisch, nicht umgebungsbedingt (2026-08-24)**:
  - Frühere Stände führten einen bis zwei Tkinter-Skips als erwartete Folge einer
    fehlenden Tcl/ttk-Runtime. Die Messung widerspricht dem: In fünfzehn Läufen derselben
    Sitzung trat der Skip viermal auf und elfmal nicht — bei unverändertem Host
    und unverändertem Testcode.
  - Die Bedingung sitzt in `tests/test_ui_accessibility.py` im `setUp` und greift,
    wenn `DokuReader.App()` einen `tk.TclError` wirft. Wäre Tcl auf diesem Host
    tatsächlich defekt, müsste **jeder** Test dieser Klasse überspringen — es war
    aber genau einer. Tkinter funktioniert hier; instabil ist der Aufbau.
  - Damit lösen sich die widersprüchlichen Altstände auf, die diese Aufgabe
    ausgelöst haben: 38/37/1 und 38/36/2 sind nicht zwei getrennte Readbacks mit
    eigener Historie, sondern derselbe instabile Test mit unterschiedlicher
    Trefferzahl. Eine schwankende Testzahl ist ein Befund über die Testinfrastruktur,
    kein Dokumentationsfehler.
  - `tests/test_metadata.py` prüft Badges und `llms.txt` jetzt auf **Struktur** statt
    auf feste Zahlen und Daten: dass es getrennte Suiten-Badges gibt und kein
    summierendes `Tests-…`-Badge zurückkehrt, und dass `llms.txt` einen
    wohlgeformten `Last-checked`-Kopf trägt. Die alte Fassung nagelte `70 passed`
    und `2026-08-20` fest und hätte bei jedem Testzuwachs erneut gebrochen —
    sie zementierte genau den Zustand, den diese Aufgabe beheben sollte.
  - Offen und bewusst nicht angefasst: die Ursache der Tk-Instabilität. Ein Eingriff
    in fremdes Test-Setup gehört nicht in eine Claim-Synchronisation; der Befund ist
    hier dokumentiert, damit die nächste schwankende Zahl nicht wieder als
    „zwei Readbacks" gelesen wird.
  - MSIX, WACK, Signierung und Store-Gates bleiben extern und werden durch keinen
    dieser Läufe belegt.

### Hinzugefügt / Added
- **Discoverability, README-Design, Badges, Security & Metadata Parity (Pfad B Audit 2026-08-20)**:
  - Shields.io Badges in `README.md` und `README_de.md` um GUI (`Python / Tkinter`), Plattform-Matrix (`Windows | macOS | Linux`), 70 verifizierte Tests (38 Pytest + 32 Node.js Companion Tests), Privacy (`100% Offline / Zero-Egress`) und Security (`Local-First`) synchronisiert.
  - Interaktives Mermaid-Sequenzdiagramm für die lokale Datenfluss- und Datenschutz-Isolationssequenz (Nutzer -> Desktop UI -> Lokaler Status `~/.dokubibliothek_state.json` -> Vorschau / Exporter -> Sammel-PDF & JSON-Export; 0 Netzwerk-Egress) in beiden Sprachfassungen integriert.
  - Zweisprachige `SECURITY.md` um 100% Offline- & Zero-Egress-Garantien, Originaldateischutz (In-Place Reference Only), Status- und Datenisolation, Non-Elevation (User-Mode-Betrieb) sowie direkte Sicherheitskontaktadresse (`security@ellmos.ai`) erweitert.
  - Ausführliche Geschwisterwerkzeuge-Matrix der `doc-bricks`-, `file-bricks`-, `dev-bricks`- und `open-bricks`-Ökosysteme (`LitZentrum`, `CleanMarkdown`, `UniversalDocsGrabber`, `UniversalInvoiceMail`, `UniversalMailCleaner`, `MailProcessor`, `PDFtoPDFocr`, `MediaBrain`, `DokuZen`, `ProFiler`, `ExplorerPro`, `DevCenter`, `CodeBox`, `open-bricks`) zweisprachig ergänzt.
  - Automatisierte Metadaten- und Dokumentations-Paritätstestsuite `tests/test_metadata.py` angelegt (validiert `pyproject.toml`, Shields-Badges, `llms.txt`, `SECURITY.md`, `store_package.json` und `CHANGELOG.md`).
  - `llms.txt` Last-checked-Zeitstempel auf 2026-08-20 und Testverifikationsstand (70 Tests: 38 Pytest + 32 Node.js 100% grün) nachgeführt.
- **Technische Hygiene & Code-Bereinigung (2026-08-14)**:
  - Unbenutzte Imports (`sys` in `DokuReader.py` und `_WARTUNG/check_store_readiness.py`) sowie ungenutzte Variablen (`errors` in `tests/test_bug_regressions.py`) vollständig bereinigt (`ruff check` 100% sauber).
  - PEP 8 E402 Import-Guards (`# noqa: E402`) in Wartungs- und Testskripten (`_WARTUNG/generate_store_media.py`, `tests/source_platform_smoke.py`, `tests/test_bug_regressions.py`, `tests/test_ui_accessibility.py`) standardisiert.
  - `pyproject.toml` um `pythonpath = ["."]` unter `[tool.pytest.ini_options]` erweitert für zuverlässige Standalone-Pytest-Ausführung.
  - Exception-Capture in Threading-Regressionstest `test_thread_safe_save` verankert (`self.assertEqual(errors, [])`).
  - `llms.txt` Last-checked Zeitstempel auf 2026-08-14 und Teststand (36 passed / 2 skipped, ruff 100% sauber, 32 Web Companion Node-Tests) synchronisiert.
- **Versions- und Release-Readback (2026-08-11)**:
  - Laufzeit `1.0.1-dev`, PEP-440-Metadaten `1.0.1.dev0` und Store-Paket `1.0.1.0` sind als getrennte Rollen dokumentiert.
  - README-Badges verweisen auf `1.0.1-dev`; ein öffentliches Release, MSIX, WACK- oder Store-Einreichung wird nicht behauptet.
  - `RELEASE_STATUS.md` und `PORTIERUNGSPLAN.md` halten die offenen externen Gates und die OneDrive-Read-only-Grenze fest.
- **Metadata-first A11y/UI-Polish (2026-08-11)**:
  - Semantische Namen, Rollen, Beschreibungen, Fokuspfade und der schreibgeschützte Vorschautext sind über einen testbaren Tkinter-Vertrag registriert.
  - Dokumentenliste, Vorschau, Leer-/Filter-/Drag-and-drop-Zustände und Return/Shift+F10-Tastaturpfade werden sichtbar und erklärend dargestellt.
  - Der Vertrag ist kein Screenreader-Abnahmetest; vollständige Tk-/visuelle Runner- und Gerätesmokes bleiben offene Gates.
- **Sichtbarkeit & Discoverability (Pfad B Audit 2026-07-30)**:
  - Dachorganisations-Badge für `open-bricks` und Pytest Test-Pass-Badge in `README.md` & `README_de.md` hinzugefügt.
  - `llms.txt` Index-Header auf `Last-checked: 2026-08-11` und Verifikationsstand (38 Pytest-Tests gesammelt, 36 bestanden/2 Tkinter-Skips + 32 Web Companion Node-Tests 100% grün) nachgeführt.
- **Sichtbarkeit & Discoverability (Pfad B Audit 2026-07-27)**:
  - Shields.io Badges für Python 3.10+, AGPL-3.0, den Entwicklungsstand `1.0.1-dev`, Platform Windows, LLM-Ready `llms.txt` und Ecosystem `doc-bricks` in `README.md` & `README_de.md` ergänzt; der frühere Versions-Badge ist damit abgelöst.
  - Standardisierter GitHub-Flavored-Markdown (`> [!NOTE]`) Callout-Block für KI/LLM-Assistenten und Ökosystem-Kontext (LitZentrum, CleanMarkdown, UniversalDocsGrabber) eingebunden.
  - Systemarchitektur-Diagramm (Mermaid) für Desktop Client, Export Engine (Combined PDF / JSON) und PWA Companion App (`web_companion`) hinzugefügt.
  - `llms.txt` Index-Header auf `Last-checked: 2026-07-27` und Verifikationsnotizen (34 Pytest-Tests + 32 Web Companion Node-Tests) aktualisiert.
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
