# Windows App Certification Kit (WACK) Protokoll - DokuReader

**Stand:** 2026-08-14  
**App:** DokuReader (Version 1.0.1.0)  
**Package:** `Geiger.DokuReader`  
**MSIX-Artefakt:** `releases/windowsstore/DokuReader.msix`  

---

## 1. Paketierung & Signatur-Status

Das MSIX-Paket wurde mit den Windows 10/11 SDK-Tools (`makeappx.exe` und `signtool.exe`) erfolgreich erstellt und mit dem Entwicklerzertifikat signiert:

- **Publisher:** `CN=52596601-BAB4-4F3F-B182-E8F3F273B202`
- **Publisher Display Name:** `Geiger`
- **Identity Name:** `Geiger.DokuReader`
- **Target OS:** `Windows.Desktop` (MinVersion `10.0.17763.0`, MaxVersionTested `10.0.19041.0`)
- **Capabilities:** `runFullTrust`
- **Unterstützte Sprachen:** `de-DE`, `en-US`
- **Paketinhalt:** `DokuReader.exe`, `LICENSE.txt`, `THIRD_PARTY_LICENSES.txt`, Icons (44x44, 50x50, 150x150, 310x150, 310x310)
- **Signatur-Algorithmus:** SHA-256 (authenticode-kompatibel)

---

## 2. Store-Readiness Gate Prüfung

Der automatisierte Readiness-Check (`python _WARTUNG/check_store_readiness.py`) bestätigt die Erfüllung aller Store-Anforderungen:

| Prüfpunkt | Status | Details |
|---|---|---|
| Store-Metadaten | OK | `store_package.json` mit allen Pflichtfeldern |
| Privacy Policy URL | OK | Public HTTPS URL hinterlegt |
| Support URL | OK | Public HTTPS Issue Tracker hinterlegt |
| WinStorePackager Konfiguration | OK | `releases/windowsstore/store_settings.json` vorhanden |
| Passwort-Sicherheit | OK | Kein PFX-Passwort im Repo gespeichert |
| Dokumente | OK | `STORE_LISTING.md`, `PRIVACY_POLICY.md`, `SUPPORT.md`, `LICENSE`, `THIRD_PARTY_LICENSES.txt` |
| Store-Assets | OK | `Square44x44Logo.png`, `Square150x150Logo.png`, `Wide310x150Logo.png`, `Square310x310Logo.png` |
| Screenshots | OK | `library-overview.png`, `pdf-preview.png`, `collection-export.png` |
| README-Vorschau | OK | `README/screenshots/main.png` |
| Windows-Executable | OK | `dist/DokuReader.exe` gebaut und getestet |
| MSIX-Paket | OK | `releases/windowsstore/DokuReader.msix` gebaut und signiert |
| WACK-Runner | OK | `_WARTUNG/run_windows_wack.py` einsatzbereit |

---

## 3. WACK-Ausführung (mit Administratorrechten)

Das Windows App Certification Kit (`appcert.exe`) erfordert zur Ausführung Administratorrechte auf dem System (UAC-Elevation).

### Ausführungsschritte:

1. **Erhöhte PowerShell (Als Administrator) öffnen:**
   ```powershell
   cd C:\_Local_DEV\repos\DokuReader
   python _WARTUNG/run_windows_wack.py
   ```

2. **Manueller Direktbefehl:**
   ```powershell
   & "C:\Program Files (x86)\Windows Kits\10\App Certification Kit\appcert.exe" reset
   & "C:\Program Files (x86)\Windows Kits\10\App Certification Kit\appcert.exe" test -appxpackagepath "C:\_Local_DEV\repos\DokuReader\releases\windowsstore\DokuReader.msix" -reportoutputpath "C:\_Local_DEV\repos\DokuReader\releases\windowsstore\test_reports\wack_latest.xml"
   ```

3. **Report parsen & zusammenfassen:**
   ```powershell
   python _WARTUNG/run_windows_wack.py --parse-report "C:\_Local_DEV\repos\DokuReader\releases\windowsstore\test_reports\wack_latest.xml"
   ```

---

## 4. WACK-Anforderungsanalyse für DokuReader

| Test-Kategorie | Erwartung | Begründung & Absicherung |
|---|---|---|
| App-Manifest-Compliance | PASS | Gültige Schemadefinition, korrekte Logos und Namensräume |
| Binary Analyzer | PASS | PyInstaller bündelt saubere Python 3.12+ Binaries |
| Security Features | PASS | DEP/NX, ASLR und SafeSEH werden von CPython Binaries unterstützt |
| Supported APIs | PASS | Desktop Bridge (`runFullTrust`) erlaubt Standard-Win32-APIs |
| Performance & Launch | PASS | Startzeit < 5s bei Erststart, keine Hintergrund-Dienste |
| Clean Uninstallation | PASS | Keine verbleibenden Registry-Schlüssel oder persistente Treiber |
