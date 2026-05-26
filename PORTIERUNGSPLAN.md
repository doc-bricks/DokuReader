# PORTIERUNGSPLAN - DokuReader

Stand: 2026-05-26

## Ausgangslage

DokuReader ist eine lokale Tkinter-Desktop-App für private Dokumentenbibliotheken. Die App speichert Themen, Dateipfade und Lesestatus in `~/.dokubibliothek_state.json`; Originaldateien bleiben am Ursprungsort. Vorschau und Sammel-PDF-Export nutzen optionale lokale Abhängigkeiten wie Pillow, `pypdf`, `pdf2image`, PyMuPDF, LibreOffice oder Microsoft Word.

Ein eigenständiger Portierungsplan lag bisher nicht vor. Es gibt aber bereits eine cross-platform Grundlage: Tkinter, `open`/`xdg-open`-Fallbacks für macOS/Linux, lokale JSON-Persistenz und ein optionaler Windows-Build.

## Zweck der Portierung

DokuReader hat einen hohen Mobilitätsnutzen, weil Leseablagen, Forschungs-PDFs und Dokumentenlisten häufig unterwegs gesichtet werden. Gleichzeitig ist die Desktop-App wichtig, weil sie lokale Dateien, Office-Konvertierung und Sammel-PDF-Export besser bedienen kann als mobile Browser-Sandboxen.

Die passende Strategie ist deshalb keine vollständige native Mobile-Neuentwicklung, sondern:

1. Desktop-App als autoritative lokale Bibliothek erhalten.
2. Ein stabiles Austauschformat `dokureader-library-v1.json` schaffen.
3. Web/PWA-Companion für Android, iOS und Browser als Leselisten- und Statusansicht planen.
4. macOS/Linux als Source-/Smoke-Ziele aus derselben Tkinter-Codebasis führen.

## Plattformentscheidung

| Plattform | Bewertung | Entscheidung |
|---|---|---|
| Windows Store | Sinnvoll, weil DokuReader ein lokales Datenschutz-Tool mit klarer Desktop-Nutzung ist. AGPL ist für kostenlose Veröffentlichung mit öffentlichem Quellcode tragbar; PyMuPDF bleibt als AGPL-Kontext zu beachten. | P1: Store-Vorbereitung fortführen, Screenshots/Listing/WACK ergänzen. |
| Android | Hoher Nutzen für Lesestatus, Themenlisten und schnelle Recherche. Direkter Zugriff auf beliebige Desktop-Pfade ist mobil aber unrealistisch. | P2: über Web/PWA oder Capacitor auf Basis von `dokureader-library-v1.json`; kein nativer Voll-Clone. |
| Webapp | Sinnvoll als gemeinsamer Companion für Browser, Android und iOS. Datei-Uploads oder exportierte Bundles können sandboxkonform genutzt werden. | P1: PWA-Companion planen, zunächst read-only/Statusansicht. |
| iOS | Nutzen wie Android, aber Dateisystemzugriff und Store-Aufwand sprechen gegen einen frühen nativen Port. | P2: PWA/Capacitor-Smoke nach Web-Companion. |
| Mac App | Technisch aus Tkinter-Codebasis möglich; Office-Konvertierung anders als Windows testen. | P3: Source-Smoke, später optional signiertes App-Bundle. |
| Linux Version | Technisch naheliegend; LibreOffice und `xdg-open` passen gut zum Usecase. | P3: Source-Smoke und optional AppImage/Flatpak prüfen. |

## Zielarchitektur

- **Desktop Windows:** Haupt-App, lokale Dokumentverweise, Vorschau, Office-Konvertierung, Sammel-PDF-Export, Windows Store.
- **Desktop macOS/Linux:** gleiche Tkinter-Codebasis; Fokus auf Start, Themenverwaltung, PDF-/Textvorschau, `open`/`xdg-open`, LibreOffice-Pfad.
- **Web/PWA Companion:** importiert `dokureader-library-v1.json`, zeigt Themen, Dokumentnamen, Lesestatus, Metadaten und optional kleine hochgeladene Dateien; schreibt Statusänderungen als Export zurück.
- **Android/iOS:** zunächst PWA-Smoke; später Capacitor nur, wenn Offline-Cache, Dateiauswahl und Push/Reminder tatsächlich gebraucht werden.

## Austauschformat

Geplantes Format: `dokureader-library-v1.json`

Mindestfelder:

- `schema_version`: `"dokureader-library-v1"`
- `exported_at`, `app_version`
- `topics`: Liste mit `name`, `documents`
- pro Dokument: `path`, `filename`, `extension`, `read`, optional `size_bytes`, `mtime`, `missing`
- optional `bundle_files`: relative Pfade, falls Dateien für einen mobilen/webbasierten Test bewusst mitkopiert werden

Wichtig: Der Export darf standardmäßig keine Dokumentinhalte einbetten, weil DokuReader bewusst lokal und datenschutzschonend arbeitet. Ein späterer Bundle-Export muss explizit vom Nutzer ausgelöst werden.

## Umsetzungsstatus

- Windows-Desktop-App: vorhanden.
- Windows-Build: vorhanden (`build_exe.bat`, `DokuReader.spec`).
- macOS/Linux-Quelllauf: im Code grundsätzlich angelegt, aber nicht als Smoke-Test dokumentiert.
- Web/PWA: noch nicht vorhanden.
- Android/iOS: noch nicht vorhanden.
- Exportformat: noch nicht vorhanden.

## Nächste Schritte

1. `dokureader-library-v1.json` als Desktop-Export definieren und dokumentieren.
2. Exportfunktion für Themen, Dokumentmetadaten und Lesestatus ergänzen.
3. Import-/Merge-Strategie für Lesestatus aus Companion-Export festlegen.
4. Windows-Store-Unterlagen aktualisieren: Listing, Screenshots, WACK/Testprotokoll.
5. Minimalen Web/PWA-Prototyp für importierte Bibliotheken planen.
6. macOS/Linux-Smoke-Test dokumentieren: Start, Datei öffnen, PDF/Textvorschau, Sammel-PDF mit LibreOffice.
