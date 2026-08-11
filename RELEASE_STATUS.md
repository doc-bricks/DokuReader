# DokuReader — belegter Versions- und Release-Status

Stand: 2026-08-11
Fresh-Remote-Readback: `master` `b068420c1e4b08f6380e16f4053ca305dc510e34`

## Version roles

| Rolle | Quelle | Stand | Bedeutung |
|---|---|---:|---|
| Entwicklung/Runtime | `DokuReader.py` `APP_VERSION` | `1.0.1-dev` | lokaler Entwicklungsstand |
| Python-Projektmetadaten | `pyproject.toml` | `1.0.1.dev0` | PEP-440-Abbildung der Entwicklung |
| Windows-Store-Paket | `store_package.json` | `1.0.1.0` | Paketmetadaten, keine Einreichung |
| Store-Packager-Einstellungen | generiertes `releases/windowsstore/store_settings.json` | `1.0.1.0` in der OneDrive-Projektion | fremder/projizierter Stand, nicht übernommen |
| Öffentliches Release | Git-Tag/Release-Artefakt | keines belegt | keine Veröffentlichung behaupten |

Die Entwicklungs-, Python- und Paketrollen sind damit bewusst getrennt, aber
widerspruchsfrei benannt. Das README-Badge lautet `1.0.1-dev` und verweist auf
`CHANGELOG.md#unreleased`; es bewirbt kein Release.

## Release-Gates

Der frische Git-Clone enthält wegen `.gitignore` keine `releases/`-Artefakte.
Ein signiertes MSIX, ein echter WACK-Report, ein Publisher-/PFX-Readback,
Partner-Center-Einreichung und ein öffentlicher GitHub-Release sind nicht
belegt. `python _WARTUNG/check_store_readiness.py --allow-blockers` meldet diese
externen Blocker weiterhin ausdrücklich. Ein lokaler Store-Readiness-Lauf ist
kein Veröffentlichungsnachweis.

Die OneDrive-Projektion wurde nur gelesen; dort vorhandene `releases/`,
`store_settings.json`, Start-/Build-Änderungen und Asset-Duplikate wurden wegen
hohem Cloud-Lock-Risiko und fremdem Dirty-State weder synchronisiert noch
überschrieben.

## Verifikation

- `python -m pytest -ra`: 38 Tests gesammelt, 36 bestanden und zwei erwartete
  Tkinter-Skips auf diesem Host ohne vollständige Tcl/ttk-Runtime.
- `python tests/source_platform_smoke.py`: Exit 0.
- `npm test` in `web_companion`: 32/32 grün.
- `python -m py_compile DokuReader.py manage_translations.py translator.py
  _WARTUNG/check_store_readiness.py _WARTUNG/run_windows_wack.py`: Exit 0.
- Ein echter Windows-Store-, WACK- oder Gerätesmoke wurde nicht behauptet.
