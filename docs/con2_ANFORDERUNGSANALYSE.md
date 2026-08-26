# DokuReader – Anforderungsanalyse con2

Stand: 2026-08-26
Quelle: Root-Dokumentation, `DokuReader.py`, Tests und Remote-Baseline
`733fff10ee5633914121678e1ec65cbdb5ba92a2`.

## Ergebnis

Der lokale Entwicklungs-/Dokumentations-Slice für TASKPLAN 1084/1085 ist
erfüllt. Sichtbare UI-Zustände, metadata-first-A11y, kompakte Layoutgrenzen und
getrennte Versionsrollen sind technisch und durch einen echten synthetischen
Tk-Visual-Smoke belegt. Bewusst separat und offen bleiben Screenreader-/Geräte-
abnahme, signiertes MSIX, WACK und Partner-Center-Einreichung. Deshalb wird kein
Release behauptet.

## Anforderungsmatrix

| Bereich | Anforderung / Prüfmethode | Status | Beleg |
|---|---|---|---|
| Versionsrollen | Runtime `1.0.1-dev`, PEP-440 `1.0.1.dev0`, Paket `1.0.1.0` getrennt ausweisen | ERFÜLLT | `DokuReader.py`, `pyproject.toml`, `store_package.json`, `RELEASE_STATUS.md` |
| Releaseflächen | Kein unbewiesenes `v1.0.0`-Release; offene MSIX/WACK/Store-Gates sichtbar | ERFÜLLT | README-Badges, `STORE_LISTING.md`, `RELEASE_STATUS.md`, `PORTIERUNGSPLAN.md` |
| A11y-Semantik | Namen, Rollen, Beschreibungen, Fokusstatus über einen testbaren Vertrag registrieren | ERFÜLLT | `apply_accessibility_metadata`, Registry, `tests/test_accessibility_contract.py` |
| Tastatur | Enter/KP-Enter öffnet Dokument; Shift+F10/Menu öffnet Aktionen | ERFÜLLT | `DokuReader.py`, statischer Contract-Test, bestehende GUI-Regression |
| Zustände | Leer-, Filterleer-, Drag-and-drop- und Vorschauzustände erklären den nächsten Schritt | ERFÜLLT | `_reload_docs`, `on_drop`, `clear_preview`, `show_preview` |
| Vorschau | Vorschautext ist schreibgeschützt; Status und Fallback bleiben sichtbar | ERFÜLLT | `tk.Text(state="disabled")`, Preview-State-Label, Source-Smoke |
| Regression | Python- und PWA-Smokes ohne OneDrive-Mutation | ERFÜLLT | 46/46 Pytest, 10×6/6 fokussierte UI-Vorläufe, Source-Smoke Exit 0, 32/32 Node-Tests |
| Kontrollierter UI-Smoke | Tk/ttk-Runtime und visuelle Prüfung von Leer-, Drag-and-drop- und Vorschauzustand | ERFÜLLT | `UI_POLISH_SMOKE.json`, drei synthetische Screenshots, 26 vollständige Metadata-Einträge, Layoutgrenzen innerhalb des Fensters |
| Screenreader-/Geräteabnahme | produktiver Screenreader, Tastaturhardware und Zielgeräte | SEPARATES GATE | in diesem Lauf nicht ausgeführt und nicht behauptet |
| Store/Release | MSIX-Signatur, WACK, Publisher-/PFX- und Partner-Center-Readback | FEHLT/OFFEN | Readiness meldet externe Blocker; keine Artefakte im Fresh Clone |

## Prüfumfang und Grenzen

- OneDrive wurde nur gelesen; `cldflt.sys`-Lockrisiko war hoch und der
  Projektstand enthielt fremde/dirty Dateien. Es gab keine Rückschreibung.
- Der kanonische lokale Clone basierte vor diesem Slice exakt auf
  `origin/master` `733fff1`; die OneDrive-Projektion war keine Mutationsquelle.
- Der Accessibility-Vertrag ist eine metadata-first-Brücke mit nativen
  Tk-Text-, State- und Fokusinformationen. Er ist kein Nachweis für eine
  bestimmte Screenreader-Implementierung.
- `check_store_readiness.py --allow-blockers` bleibt ein Readiness-Readback und
  kein Veröffentlichungsnachweis.
