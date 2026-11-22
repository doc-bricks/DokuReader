# DokuReader - Windows Store Build- & Packaging-Anleitung

## Voraussetzungen

1. Python 3.10+ mit Tkinter, PyMuPDF, Pillow, reportlab, pypdf
2. PyInstaller für den Desktop-Build (`DokuReader.spec` oder Single-File-Build)
3. Windows 10/11 SDK mit `makeappx.exe`, `signtool.exe` und `appcert.exe`
4. Lokaler Schreibpfad außerhalb synchronisierter Cloud-Ordner für MSIX-Artefakte (`$env:DOKUREADER_STORE_BUILD`)

Setze `$projectRoot` auf den lokalen Repository-Checkout und `$softwareRoot` auf das lokale Store-Tooling-Verzeichnis.

---

## Schritt 0: Store-Readiness & Manifest-Vorlage prüfen

```powershell
$projectRoot = (Resolve-Path ".").Path
Set-Location $projectRoot
$env:PYTHONIOENCODING = "utf-8"

# Preflight-Store-Audit ausführen (prüft Metadaten, 6 Sprachen, AppxManifest.xml, Logo-Staging & Assets)
python _WARTUNG\check_store_readiness.py --allow-blockers
```

Vorhandene Store-Assets und Vorlagen:
- `store_assets\Square44x44Logo.png` (44x44 -> Staging `icons\Square44x44Logo.png`)
- `store_assets\StoreLogo.png` (50x50 -> Staging `icons\StoreLogo.png`)
- `store_assets\Square150x150Logo.png` (150x150 -> Staging `icons\Square150x150Logo.png`)
- `store_assets\Wide310x150Logo.png` (310x150 -> Staging `icons\Wide310x150Logo.png`)
- `store_assets\Square310x310Logo.png` (310x310 -> Staging `icons\Square310x310Logo.png`)
- `releases\windowsstore\AppxManifest.xml` (`Geiger.DokuReader`, `x64`, `runFullTrust`, `icons\*.png`, 6 `<Resource Language="..."/>`-Einträge)
- `releases\windowsstore\store_listing_{de,en,es,zh,ja,ru}.md`
- `releases\windowsstore\screenshots\*.png` (3 hochauflösende Screenshots)

---

## Schritt 1: Desktop-EXE bauen

```powershell
Set-Location $projectRoot
pyinstaller --clean --noconfirm DokuReader.spec
```

Erwarteter Hauptpfad:
- `dist\DokuReader.exe` (bzw. `dist\DokuReader\DokuReader.exe` bei Ordner-Build)

---

## Schritt 2: Store-Pretest

```powershell
& (Join-Path $softwareRoot "_STORE\msstore_pretest.ps1") `
  -ExePath (Join-Path $projectRoot "dist\DokuReader.exe") `
  -ProjectRoot $projectRoot `
  -StartWait 6
```

---

## Schritt 3: MSIX lokal außerhalb synchronisierter Cloud-Ordner bauen

`msstore_build_msix.ps1` kopiert `DokuReader.exe` (bzw. den kompletten Onedir-Ordner), übernimmt alle PNGs aus `store_assets\` nach `icons\` im Staging-Verzeichnis und packt das MSIX per `makeappx.exe`:

```powershell
$outputRoot = if ($env:DOKUREADER_STORE_BUILD) { $env:DOKUREADER_STORE_BUILD } else { Join-Path $env:TEMP "dokureader-store-build" }
New-Item -ItemType Directory -Force -Path $outputRoot | Out-Null

& (Join-Path $softwareRoot "_STORE\msstore_build_msix.ps1") `
  -ProjectRoot $projectRoot `
  -ExePath (Join-Path $projectRoot "dist\DokuReader.exe") `
  -OutputMsix (Join-Path $outputRoot "DokuReader.msix") `
  -ExtraFiles @(
    (Join-Path $projectRoot "LICENSE"),
    (Join-Path $projectRoot "THIRD_PARTY_LICENSES.txt")
  )
```

---

## Schritt 4: Windows App Certification Kit (WACK) Lauf

In einer PowerShell-Konsole mit Administratorrechten:

```powershell
$msixPath = Join-Path $projectRoot "releases\windowsstore\DokuReader.msix"
$reportDir = Join-Path $projectRoot "releases\windowsstore\test_reports"

& (Join-Path $softwareRoot "_STORE\msstore_wack.ps1") `
  -MsixPath $msixPath `
  -ReportDir $reportDir

python _WARTUNG\run_windows_wack.py --parse-report (Join-Path $reportDir "wack_latest.xml")
```

---

## Schritt 5: Partner Center Upload & Listing Checkliste (Tier-2: 6 Sprachen)

1. Paket `DokuReader.msix` erst nach expliziter Freigabe im Microsoft Partner Center unter Packages hochladen.
2. Store-Listings für alle 6 unterstützten Sprachen übernehmen (`releases\windowsstore\store_listing_{de,en,es,zh,ja,ru}.md`):
   - `de-DE`, `en-US`, `es-ES`, `zh-CN`, `ja-JP`, `ru-RU`
3. Suchbegriffe (je 7 Keywords ≤ 30 Zeichen nach Richtlinie 10.1.3, keine fremden Markenbezeichnungen) aus `store_package.json` (`listings.<locale>.keywords`) übernehmen.
4. Screenshots aus `releases\windowsstore\screenshots\` für Desktop hochladen.
5. Privacy Policy URL hinterlegen: `https://github.com/doc-bricks/DokuReader/blob/master/PRIVACY_POLICY.md`.
6. Support URL hinterlegen: `https://github.com/doc-bricks/DokuReader/issues`.
7. Preis & Verfügbarkeit: Kostenlos (Free, AGPL-3.0-or-later).
