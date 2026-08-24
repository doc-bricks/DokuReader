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

- `python -X utf8 -m pytest -ra`: 45 Tests gesammelt, 0 fehlgeschlagen, Exit 0.
  Gemessen 2026-08-24 auf Commit `df41cf8`, Python 3.12.10 (Windows), fünfzehn Läufe.
- **Die Passed-Zahl schwankt zwischen 44 und 45 - und das ist der eigentliche
  Befund dieser Prüfung.** In vier von fünfzehn Läufen übersprang
  `tests/test_ui_accessibility.py` einen Test, in elf lief er durch. Deshalb
  nennt das README-Badge die gesammelte Zahl und die Fehlerzahl, nicht die
  bestandene: 45 Tests, 0 fehlgeschlagen. Diese Aussage ist in jedem Lauf wahr.
- **Der Skip ist sporadisch, nicht umgebungsbedingt.** Er meldet „Tkinter ist in
  dieser Umgebung nicht stabil verfügbar: Can't find a usable init.tcl". Die
  Bedingung sitzt im `setUp` und greift, wenn `DokuReader.App()` einen
  `tk.TclError` wirft. Wäre Tcl auf diesem Host defekt, müsste **jeder** Test
  dieser Klasse überspringen - es ist aber jedes Mal genau einer, und elfmal
  keiner. Tkinter funktioniert hier; instabil ist der Aufbau.
  Damit lösen sich die widersprüchlichen Altstände auf, die diese Prüfung
  ausgelöst haben: 38/37/1 und 38/36/2 sind nicht zwei Readbacks mit eigener
  Historie, sondern derselbe instabile Test mit unterschiedlicher Trefferzahl.
  Eine schwankende Testzahl ist hier ein Befund über die Testinfrastruktur,
  kein Dokumentationsfehler.
  (Historisch: 38/37/1 auf Commit `88827cb`; die Testbasis ist seither
  gewachsen.)
- `python tests/source_platform_smoke.py`: Exit 0.
- `npm test` in `web_companion`: 32/32 grün.
- `python -m py_compile DokuReader.py manage_translations.py translator.py
  _WARTUNG/check_store_readiness.py _WARTUNG/run_windows_wack.py`: Exit 0.
- Ein echter Windows-Store-, WACK- oder Gerätesmoke wurde nicht behauptet.
