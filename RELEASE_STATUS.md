# DokuReader — belegter Versions- und Release-Status

Stand: 2026-08-26
Baseline-Remote-Readback vor diesem Slice: `master`
`733fff10ee5633914121678e1ec65cbdb5ba92a2`

## Version roles

| Rolle | Quelle | Stand | Bedeutung |
|---|---|---:|---|
| Entwicklung/Runtime | `DokuReader.py` `APP_VERSION` | `1.0.1-dev` | lokaler Entwicklungsstand |
| Python-Projektmetadaten | `pyproject.toml` | `1.0.1.dev0` | PEP-440-Abbildung der Entwicklung |
| Windows-Store-Paket | `store_package.json` | `1.0.1.0` | Paketmetadaten, keine Einreichung |
| Store-Packager-Einstellungen | generiertes `releases/windowsstore/store_settings.json` | `1.0.1.0` in der OneDrive-Projektion | read-only geprüft, nicht übernommen |
| Lokales Archivartefakt | `releases/v1.0.0/DokuReader-1.0.0-win64.exe` in OneDrive | SHA-256 `fb5a2d…4655` stimmt mit `SHA256SUMS.txt` | Integrität, aber kein Build-/Releasebeleg |
| Öffentliches Release | Git-Tags und GitHub-Releases | keines belegt | keine Veröffentlichung behaupten |

Die Entwicklungs-, Python- und Paketrollen sind damit bewusst getrennt, aber
widerspruchsfrei benannt. Das README-Badge lautet `1.0.1-dev` und verweist auf
`CHANGELOG.md#unreleased`; es bewirbt kein Release.

## Release-Gates

Der öffentliche GitHub-Readback vom 2026-08-26 bestätigt das Repo
`doc-bricks/DokuReader`, Default-Branch `master`, aber keine Tags und keine
GitHub-Releases. Der frische Git-Clone enthält wegen `.gitignore` keine
`releases/`-Artefakte. Ein signiertes MSIX, ein echter WACK-Report, ein
Publisher-/PFX-Readback und eine Partner-Center-Einreichung sind nicht belegt.
`python _WARTUNG/check_store_readiness.py --allow-blockers` meldet diese
externen Blocker weiterhin ausdrücklich. Ein lokaler Store-Readiness-Lauf oder
das vorhandene v1.0.0-EXE ist kein Veröffentlichungsnachweis.

Die OneDrive-Projektion wurde nur gelesen; dort vorhandene `releases/`,
`store_settings.json`, Start-/Build-Änderungen und Asset-Duplikate wurden wegen
hohem Cloud-Lock-Risiko und fremdem Dirty-State weder synchronisiert noch
überschrieben.

## Verifikation

- `python -X utf8 -m pytest -ra`: 46 Tests gesammelt, 46 bestanden,
  0 übersprungen, 0 fehlgeschlagen, Exit 0 (finaler Lauf 2026-08-26,
  Python 3.12.10 auf Windows).
- Der zuvor sporadische Einzel-Skip im Tk-Testaufbau ist begrenzt gehärtet:
  jeder Test darf die App-Initialisierung höchstens dreimal versuchen und
  überspringt nur, wenn alle drei Versuche scheitern. Zehn unabhängige
  Folgeläufe von `tests/test_ui_accessibility.py` ergaben 60/60 bestandene
  Tests ohne Skip.
- `_WARTUNG/capture_ui_polish_smoke.py` startete eine echte Tk-App mit
  synthetischem temporärem State und erfasste Leer-, Drag-and-drop- und
  Textvorschauzustand per Win32 `PrintWindow`. Alle 26 A11y-Einträge besitzen
  Name und Beschreibung; Vorschautext ist schreibgeschützt und die geprüften
  unteren/rechten Layoutgrenzen liegen innerhalb des Fensters. Beleg:
  `UI_POLISH_SMOKE.json` und `README/screenshots/ui-polish-*.png`.
- `python tests/source_platform_smoke.py`: Exit 0.
- `npm test` in `web_companion`: 32/32 grün.
- `python -m py_compile DokuReader.py manage_translations.py translator.py
  _WARTUNG/check_store_readiness.py _WARTUNG/run_windows_wack.py`: Exit 0.
- Die Bilder wurden visuell auf Clipping, Statuslesbarkeit und kompakte
  Anordnung geprüft. Ein Screenreader-, Tastaturhardware-, Windows-Store-,
  WACK- oder Gerätesmoke wurde nicht behauptet.
