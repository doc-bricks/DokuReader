# DokuReader – Anforderungsanalyse con2

Stand: 2026-08-11
Quelle: Root-Dokumentation, `DokuReader.py`, Tests und frischer Remote-Clone
`b068420c1e4b08f6380e16f4053ca305dc510e34`.

## Ergebnis

Der lokale Entwicklungs-/Dokumentations-Slice ist zu rund **80 %** erfüllt.
Die Kernanforderungen für sichtbare UI-Zustände, metadata-first-A11y und
getrennte Versionsrollen sind im Clone umgesetzt und statisch/regressionell
belegt. Nicht abgeschlossen sind bewusst externe Gates: vollständige
Tk-/visuelle Runner, echter Screenreader-/Gerätetest, signiertes MSIX, WACK und
Partner-Center-Einreichung. Deshalb wird nichts archiviert und kein Release
behauptet.

## Anforderungsmatrix

| Bereich | Anforderung / Prüfmethode | Status | Beleg |
|---|---|---|---|
| Versionsrollen | Runtime `1.0.1-dev`, PEP-440 `1.0.1.dev0`, Paket `1.0.1.0` getrennt ausweisen | ERFÜLLT | `DokuReader.py`, `pyproject.toml`, `store_package.json`, `RELEASE_STATUS.md` |
| Releaseflächen | Kein unbewiesenes `v1.0.0`-Release; offene MSIX/WACK/Store-Gates sichtbar | ERFÜLLT | README-Badges, `STORE_LISTING.md`, `RELEASE_STATUS.md`, `PORTIERUNGSPLAN.md` |
| A11y-Semantik | Namen, Rollen, Beschreibungen, Fokusstatus über einen testbaren Vertrag registrieren | ERFÜLLT | `apply_accessibility_metadata`, Registry, `tests/test_accessibility_contract.py` |
| Tastatur | Enter/KP-Enter öffnet Dokument; Shift+F10/Menu öffnet Aktionen | ERFÜLLT | `DokuReader.py`, statischer Contract-Test, bestehende GUI-Regression |
| Zustände | Leer-, Filterleer-, Drag-and-drop- und Vorschauzustände erklären den nächsten Schritt | ERFÜLLT | `_reload_docs`, `on_drop`, `clear_preview`, `show_preview` |
| Vorschau | Vorschautext ist schreibgeschützt; Status und Fallback bleiben sichtbar | ERFÜLLT | `tk.Text(state="disabled")`, Preview-State-Label, Source-Smoke |
| Regression | Python- und PWA-Smokes ohne OneDrive-Mutation | ERFÜLLT | 45 Pytest-Tests gesammelt, 0 fehlgeschlagen (ein Test überspringt sporadisch, siehe `RELEASE_STATUS.md`), Source-Smoke Exit 0, 32 Node-Tests (Stand 2026-08-24, `df41cf8`) |
| Vollständige GUI-Abnahme | Tk/ttk-Runtime, visuelle Prüfung und Screenreader | TEILWEISE | Tk-Tests laufen auf diesem Host, überspringen aber sporadisch (4 von 15 Läufen); der früher als erwartet geführte Skip ist ein instabiler Aufbau, siehe `RELEASE_STATUS.md`. Kein Screenreader- und kein Gerätetest-Claim |
| Store/Release | MSIX-Signatur, WACK, Publisher-/PFX- und Partner-Center-Readback | FEHLT/OFFEN | Readiness meldet externe Blocker; keine Artefakte im Fresh Clone |

## Prüfumfang und Grenzen

- OneDrive wurde nur gelesen; `cldflt.sys`-Lockrisiko war hoch und der
  Projektstand enthielt fremde/dirty Dateien. Es gab keine Rückschreibung.
- Der Fresh Clone lief auf dem Remote-Stand `b068420`; die lokale Änderung
  bleibt in `C:\_Local_DEV\repos\REL-PUB_DokuReader-tasksolver-1084-1085`.
- Der Accessibility-Vertrag ist eine metadata-first-Brücke mit nativen
  Tk-Text-, State- und Fokusinformationen. Er ist kein Nachweis für eine
  bestimmte Screenreader-Implementierung.
- `check_store_readiness.py --allow-blockers` bleibt ein Readiness-Readback und
  kein Veröffentlichungsnachweis.
