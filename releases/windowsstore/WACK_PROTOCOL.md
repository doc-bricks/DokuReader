# Windows App Certification Kit (WACK) Protokoll - DokuReader

**Stand:** 2026-11-18
**App:** DokuReader (Store-Paketmetadaten `1.0.1.0`, Runtime `1.0.1-dev`)
**Package:** `Geiger.DokuReader`
**Zielpfad MSIX-Artefakt (ungetrackt):** `releases/windowsstore/DokuReader.msix`

---

## 1. Paketierungs-Vorbereitung & Manifest-Parameter

Die Vorlagen und Metadaten für das MSIX-Paket sind im Repository vollständig vorbereitet (`store_package.json`, `releases/windowsstore/store_settings.json`, `releases/windowsstore/AppxManifest.xml`):

- **Publisher:** `CN=52596601-BAB4-4F3F-B182-E8F3F273B202`
- **Publisher Display Name:** `Geiger`
- **Identity Name:** `Geiger.DokuReader`
- **Architecture:** `x64`
- **Target OS:** `Windows.Desktop` (`MinVersion="10.0.17763.0"`, `MaxVersionTested="10.0.22621.0"`)
- **Capabilities:** `runFullTrust`
- **Execution Alias:** `dokureader.exe`
- **Unterstützte Sprachen (Tier 2 — 6 Sprachen):** `de-DE`, `en-US`, `es-ES`, `zh-CN`, `ja-JP`, `ru-RU`
- **Paketinhalt:** `DokuReader.exe`, `LICENSE`, `THIRD_PARTY_LICENSES.txt`, Store-Assets (`44x44`, `50x50`, `150x150`, `310x150`, `310x310`)

> **Hinweis zum Release-Boundary-Gate:** Im öffentlichen Git-Repository liegen bewusst keine binären `.msix`- oder `.pfx`-Dateien (`.gitignore`). Ein frisch signiertes MSIX sowie ein erhöhter Administrator-Lauf von `appcert.exe` bleiben vor einer Partner-Center-Einreichung als explizite externe Gates durchzuführen.

---

## 2. Store-Readiness Gate Prüfung

Der automatisierte Readiness-Check (`python _WARTUNG/check_store_readiness.py --allow-blockers`) prüft alle Repository-seitigen Vorbedingungen reproduzierbar:

| Prüfpunkt | Status im Repo | Details |
|---|---|---|
| Store-Metadaten | OK | `store_package.json` mit allen Pflichtfeldern |
| Tier-2 Sprachabdeckung | OK | 6 Sprachen (`de-DE`, `en-US`, `es-ES`, `zh-CN`, `ja-JP`, `ru-RU`) + Listings & Keywords (≤ 7, ≤ 30 Zeichen) |
| Manifest-Vorlage | OK | `releases/windowsstore/AppxManifest.xml` valide (`x64`, `runFullTrust`, `icons\*.png` gegen `store_assets\*.png` geprüft, 6 `<Resource Language="..."/>`) |
| Privacy & Support URLs | OK | Öffentliche HTTPS-URLs hinterlegt |
| Packager-Pfadhygiene | OK | `releases/windowsstore/store_settings.json` ohne hartcodierte Entwicklerpfade und ohne PFX-Passwort |
| Pflichtdokumente | OK | `STORE_LISTING.md`, `PRIVACY_POLICY.md`, `SUPPORT.md`, `LICENSE`, `THIRD_PARTY_LICENSES.txt` |
| Store-Assets & Screenshots | OK | Alle 5 PNG-Kachelgrößen + 3 Store-Screenshots + `README/screenshots/main.png` |
| WACK-Runner | OK | `_WARTUNG/run_windows_wack.py` einsatzbereit |
| Lokale Build-Artefakte (`EXE`/`MSIX`) | Externes Gate | Werden lokal außerhalb von Git erzeugt (`dist/DokuReader.exe`, `releases/windowsstore/DokuReader.msix`) |

---

## 3. WACK-Ausführung (mit Administratorrechten)

Das Windows App Certification Kit (`appcert.exe`) erfordert zur Ausführung Administratorrechte (UAC-Elevation).

### Ausführungsschritte (relativ zum Repository-Root):

1. **Erhöhte PowerShell (Als Administrator) im Repository-Root öffnen:**
   ```powershell
   python _WARTUNG/run_windows_wack.py
   ```

2. **Manueller Direktbefehl:**
   ```powershell
   $repoRoot = (Resolve-Path ".").Path
   $msix = Join-Path $repoRoot "releases\windowsstore\DokuReader.msix"
   $report = Join-Path $repoRoot "releases\windowsstore\test_reports\wack_latest.xml"

   & "C:\Program Files (x86)\Windows Kits\10\App Certification Kit\appcert.exe" reset
   & "C:\Program Files (x86)\Windows Kits\10\App Certification Kit\appcert.exe" test -appxpackagepath $msix -reportoutputpath $report
   ```

3. **Report parsen & JSON-Zusammenfassung schreiben:**
   ```powershell
   python _WARTUNG/run_windows_wack.py --parse-report "releases/windowsstore/test_reports/wack_latest.xml"
   ```

---

## 4. WACK-Anforderungsanalyse für DokuReader

| Test-Kategorie | Erwartung | Technische Absicherung |
|---|---|---|
| App-Manifest-Compliance | PASS | Schema-valide `AppxManifest.xml`, Staging-Logo-Pfade (`icons\*.png` aus `store_assets\*.png`), Namensräume und 6 Sprachressourcen |
| Binary Analyzer | PASS | PyInstaller bündelt aktuelle Python 3.12+ Binaries |
| Security Features | PASS | DEP/NX und ASLR in CPython-Binaries aktiv; unprivilegierter Laufzeitbetrieb (`RunAsInvoker`) |
| Supported APIs | PASS | Desktop Bridge (`runFullTrust`) erlaubt Win32-Standarddialoge und lokale Dateizugriffe |
| Clean Uninstallation | PASS | Keine Registry-Autostarts, Hintergrunddienste oder Systemtreiber |
