# DokuReader - Windows Store Build- & Packaging-Anleitung

## Voraussetzungen

1. Python 3.10+ mit Tkinter, PyMuPDF, Pillow, reportlab, pypdf
2. PyInstaller für den Desktop-Build (`DokuReader.spec` oder Single-File-Build)
3. Windows 10/11 SDK mit `makeappx.exe`, `signtool.exe` und `appcert.exe`
4. Lokaler Schreibpfad außerhalb synchronisierter Cloud-Ordner für MSIX-Artefakte, z. B. `C:\_Local_DEV\build\dokureader-store`

Die Befehle verwenden standardisierte Pfade.
Setze `$projectRoot` auf den lokalen Checkout `C:\_Local_DEV\repos\DokuReader` und `$softwareRoot` auf den lokalen Pipeline-Ordner `C:\Users\User\OneDrive\.TOPICS\.SOFTWARE`.

---

## Schritt 0: Store-Material & Icons aktualisieren

```powershell
$projectRoot = "C:\_Local_DEV\repos\DokuReader"
Set-Location $projectRoot
$env:PYTHONIOENCODING="utf-8"

# Kacheln & Store-Assets erzeugen
python -c "import _WARTUNG.generate_store_media as g; g.generate_store_assets()"

# Preflight-Store-Audit ausführen
python _WARTUNG\check_store_readiness.py
```

Erwartete Artefakte:
- `store_assets\Square44x44Logo.png` (44x44)
- `store_assets\StoreLogo.png` (50x50)
- `store_assets\Square150x150Logo.png` (150x150)
- `store_assets\Wide310x150Logo.png` (310x150)
- `store_assets\Square310x310Logo.png` (310x310)
- `releases\windowsstore\StoreLogo.png` (50x50)
- `releases\windowsstore\screenshots\*.png` (3 hochauflösende Screenshots)

---

## Schritt 1: Desktop-EXE bauen

```powershell
Set-Location $projectRoot
pyinstaller --clean --noconfirm --windowed --name DokuReader --icon DokuReader.ico DokuReader.py
```

Erwarteter Hauptpfad:
- `dist\DokuReader\DokuReader.exe`

---

## Schritt 2: Store-Pretest

```powershell
$softwareRoot = "C:\Users\User\OneDrive\.TOPICS\.SOFTWARE"
& (Join-Path $softwareRoot "_STORE\msstore_pretest.ps1") `
  -ExePath (Join-Path $projectRoot "dist\DokuReader\DokuReader.exe") `
  -ProjectRoot $projectRoot `
  -StartWait 6
```

---

## Schritt 3: MSIX lokal außerhalb von OneDrive bauen

```powershell
$outputRoot = "C:\_Local_DEV\build\dokureader-store"
New-Item -ItemType Directory -Force -Path $outputRoot | Out-Null

python (Join-Path $softwareRoot "_STORE\store_packager.py") `
  $projectRoot `
  --dist (Join-Path $projectRoot "dist\DokuReader") `
  --output-dir $outputRoot `
  --app-name "DokuReader" `
  --version "1.0.1.0" `
  --publisher "CN=52596601-BAB4-4F3F-B182-E8F3F273B202" `
  --identity-name "Geiger.DokuReader" `
  --capabilities "runFullTrust"
```

Erwartetes MSIX-Paket:
- `C:\_Local_DEV\build\dokureader-store\DokuReader.msix` (wird nach `releases\windowsstore\DokuReader.msix` gespiegelt)

---

## Schritt 4: Windows App Certification Kit (WACK) Lauf

In einer PowerShell-Konsole mit Administratorrechten:

```powershell
$softwareRoot = "C:\Users\User\OneDrive\.TOPICS\.SOFTWARE"
$msixPath = "C:\_Local_DEV\repos\DokuReader\releases\windowsstore\DokuReader.msix"
$reportDir = Join-Path $projectRoot "releases\windowsstore\test_reports"

& (Join-Path $softwareRoot "_STORE\msstore_wack.ps1") `
  -MsixPath $msixPath `
  -ReportDir $reportDir
```

Report parsen und JSON-Zusammenfassung aktualisieren:
```powershell
python _WARTUNG\run_windows_wack.py --parse-report "$reportDir\wack_latest.xml"
```

---

## Schritt 5: Partner Center Upload & Listing Checkliste

1. Paket `DokuReader.msix` im Microsoft Partner Center unter Packages hochladen.
2. Store-Listing aus `releases\windowsstore\store_listing_de.md` und `store_listing_en.md` übernehmen.
3. Suchbegriffe (exakt 7 Keywords nach Richtlinie 10.1.3, keine Markenbezeichnungen) einpflegen:
   - DE: `Dokumente, PDF, Vorschau, Bibliothek, Leseliste, Sammel-PDF, Datenschutz`
   - EN: `documents, PDF, preview, library, reading list, bundle PDF, privacy`
4. Screenshots aus `releases\windowsstore\screenshots\` für Desktop hochladen.
5. Privacy Policy URL hinterlegen: `https://github.com/doc-bricks/DokuReader/blob/master/PRIVACY_POLICY.md`.
6. Support URL hinterlegen: `https://github.com/doc-bricks/DokuReader/issues`.
7. Preis & Verfügbarkeit: Kostenlos (Free, AGPL-3.0-or-later).
