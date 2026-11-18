# DokuReader — belegter Versions- und Release-Status

Stand: 2026-11-18
Baseline-Remote-Readback vor diesem Slice: `master`
`85bb0e6bc47a304e8973ff97dd873aed5135e55d`

## Version roles

| Rolle | Quelle | Stand | Bedeutung |
|---|---|---:|---|
| Entwicklung/Runtime | `DokuReader.py` `APP_VERSION` | `1.0.1-dev` | lokaler Entwicklungsstand (Versions-Freeze `T-20260920-167562623`) |
| Python-Projektmetadaten | `pyproject.toml` | `1.0.1.dev0` | PEP-440-Abbildung der Entwicklung |
| Windows-Store-Paket | `store_package.json` & `releases/windowsstore/AppxManifest.xml` | `1.0.1.0` | vorbereitete Tier-2-Paketmetadaten (6 Sprachen), keine Einreichung |
| Store-Packager-Einstellungen | `releases/windowsstore/store_settings.json` | `1.0.1.0` | portable relative Pfade ohne PFX-Geheimnisse |
| Web/PWA-Companion | `web_companion/` (`sw.js` `dokureader-companion-v9`) | `dokureader-library-v1` | installierbare Offline-PWA mit lokaler `localStorage`-Persistenz & 6 Sprachen (`DE/EN/ES/ZH/JA/RU`) |
| Öffentliches Release | Git-Tags und GitHub-Releases | keines belegt | keine Veröffentlichung behaupten |

Die Entwicklungs-, Python- und Paketrollen sind damit bewusst getrennt, aber
widerspruchsfrei benannt. Das README-Badge lautet `1.0.1-dev` und verweist auf
`CHANGELOG.md#unreleased`; es bewirbt kein Release.

## Release-Gates

Das öffentliche Repository `doc-bricks/DokuReader` (Default-Branch `master`)
führt weiterhin keine Git-Tags und keine öffentlichen GitHub-Releases. Der
frische Git-Klon enthält wegen `.gitignore` keine binären Build-Artefakte
(`dist/`, `*.msix`). Ein signiertes MSIX, ein echter WACK-Report aus einer
erhöhten Administrator-Konsole, ein PFX-Signaturnachweis und eine
Partner-Center-Einreichung sind nicht belegt.
`python _WARTUNG/check_store_readiness.py --allow-blockers` weist die
fehlenden lokalen Binärartefakte (`Windows EXE`, `MSIX package`) im frischen
Git-Klon weiterhin transparent als externe Build-/Signier-Gates aus, während
alle Repository-seitigen Vorbedingungen (inkl. 6-Sprachen-Listings,
Keyword-Richtlinie 10.1.3, Pfadhygiene und `AppxManifest.xml`) erfüllt sind.

## Verifikation (Stand 2026-11-18)

- **Python-Gesamtsuite (`pytest`):** 285 gesammelt, **280 bestanden**, 5 POSIX-spezifische Skips unter Windows, 0 fehlgeschlagen, Exit 0 (inklusive Companion-Lesestatus-Roundtrip `test_companion_roundtrip_and_pwa.py`, 1100×720-Kompaktlayout `test_ui_accessibility.py`, Metadaten- und Store-Readiness-Tests).
- **Desktop ↔ Companion Roundtrip (`dokureader-library-v1.json`):** Desktop-Export (`JSON-Export…`) → Offline-PWA-Statuswechsel & `localStorage`-Wiederherstellung → Desktop-Statusabgleich (`Status importieren…`) end-to-end über Python und Node.js verifiziert; Originaldateien bleiben unberührt (`INV-INPLACE-03`).
- **Web/PWA-Companion (`node --test` in `web_companion`):** **48/48 Tests** in 3 Suiten grün (inkl. Service-Worker-`ASSET_HASH`-Wächter, 6-Sprachen-Parität `DE/EN/ES/ZH/JA/RU` und Offline-Neustart-Persistenz).
- **Windows-Store-Readiness (`python _WARTUNG/check_store_readiness.py`):** **27 OK / 0 WARN / 0 BLOCKER** im lokalen Entwicklungsklon (mit den ungetrackten lokalen Binärartefakten `dist/DokuReader.exe` und `releases/windowsstore/DokuReader.msix` sowie der im Repo getrackten Preflight-Zusammenfassung `releases/windowsstore/test_reports/wack_preflight_20260922.json`); in einem frischen Git-Klon ohne lokale Binärartefakte meldet `--allow-blockers` erwartungsgemäß `25 OK / 0 WARN / 2 BLOCKER` (`Windows EXE`, `MSIX package`).
- **Source-Plattform-Smoke (`python tests/source_platform_smoke.py`):** Exit 0 (inkl. PDF-/Office-Fallbacks, Schutz beschädigter PDFs und JSON-Roundtrip).
- **Statische Prüfung:** `ruff check .`, `python -m compileall -q .` und `git diff --check` jeweils Exit 0.
- Ein physischer Android-/iOS-Gerätelauf (`TW-DOKUREADER-02`), ein Screenreader-Abnahmetest sowie ein echter Administrator-WACK-/Partner-Center-Lauf (`TW-DOKUREADER-01`) werden hier ausdrücklich nicht behauptet.
