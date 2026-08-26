# DokuReader — Portierungs- und Gate-Plan

Stand: 2026-08-26

## Produkt- und Plattformgrenzen

| Ziel | Belegter Umfang | Gate |
|---|---|---|
| Windows/Tkinter | autoritative Desktop-App, lokale JSON-State-Datei, Vorschau und PDF-Export | Python-/Source-Smokes und synthetischer Tk-Visual-Smoke grün; Screenreader separat |
| macOS/Linux | gleiche Python-Quelle als Source-/Smoke-Ziel | echter Runner-Readback offen |
| Browser/Android/iOS | `web_companion` als PWA mit `dokureader-library-v1` | `npm test` lokal grün; kein Geräte-/Store-Claim |
| Windows Store | `store_package.json` 1.0.1.0 und Listing-Dokumente | MSIX, Signierung, WACK und Partner Center offen |

## Versionsentscheidung

- Entwicklungs-/Runtime-Version: `DokuReader.py` `APP_VERSION=1.0.1-dev`.
- Python-Projektmetadaten: `pyproject.toml` `1.0.1.dev0`.
- Paketversion: `store_package.json` `1.0.1.0`.
- Releaseversion: keine; `1.0.1-dev` ist kein öffentliches Release.

Diese Rollen dürfen nicht durch einen historischen Versions-Badge oder einen
ignorierten lokalen `releases/`-Ordner vermischt werden.

## Gate-Reihenfolge

1. Python-Regressionen, Source-Smoke und PWA-Node-Smoke lokal prüfen.
2. A11y-Metadaten, Zustände, Tastatur-/Fokuspfade und erklärende Leer-/Fehler-
   texte prüfen; erst danach visuelle Detailpolitur bewerten. Für den aktuellen
   Slice belegt durch `UI_POLISH_SMOKE.json` und drei synthetische Zustände.
3. Store-Dokumente und Lizenzinventar gegen `store_package.json` lesen.
4. Mit externer Publisher-/PFX-Autorisierung ein MSIX bauen, signieren und
   WACK ausführen; XML und geparste JSON-Zusammenfassung ablegen.
5. Erst nach ausdrücklicher Besitzerentscheidung über Sichtbarkeit, Tag und
   Artefaktgrenzen darf eine Veröffentlichung geprüft werden.

## Nicht-Ziele dieses Laufs

- kein Tag, kein GitHub-Release und kein Store-Upload;
- keine Änderung der OneDrive-Projektion;
- kein echter Android-/iOS-Gerätetest und kein Screenreader-Abnahmetest;
- keine Wiederverwendung fremder `WORKSTATION-LG`-Dateien oder Backups.
