# PWA-Testplan — DokuReader Web/PWA Companion

Stand: 2026-09-09
Planungs-Gate: `SNW-DOKUREADER-02` (Vorbereitung für `TW-DOKUREADER-02`)

## Ziel

Der DokuReader Web/PWA Companion dient als mobile, browserfreundliche und ressourcenschonende Begleitschicht für die Desktop-Anwendung. Er konsumiert standardisierte `dokureader-library-v1.json`-Dateien, ermöglicht die mobile Durchmusterung von Dokumentthemen, die Suche im Dokumentbestand, das Setzen und Umschalten des Lesestatus sowie den Export der aktualisierten Statusdatei — vollständig offline-fähig via Service Worker.

Dieser Testplan definiert die verbindlichen Kriterien und Durchführungsrichtlinien für mobile Smoke-Tests auf Android (Chrome) und iOS (Safari), bevor ein nativer Wrapper (Capacitor) überhaupt erwogen wird.

## Sicherheits- und Datenschutzgrenzen

1. **Keine privaten Dokumentdaten:** Mobile Smokes und Testläufe dürfen unter keinen Umständen echte Klienten-, Finanz- oder persönliche Arbeitsdaten verwenden.
2. **Standardisierte Testbibliothek:** Als kanonische Testbasis dient ausschließlich die synthetische Datei `web_companion/sample_library.json`.
3. **Kein Server-Sync / Zero Egress:** Der Companion läuft vollständig lokal im Browser/WebView. Es findet keinerlei Übertragung an externe Server statt.

## Test-Voraussetzungen & Bereitstellung

- **Lokaler HTTP-Server:**
  ```bash
  cd web_companion
  python -m http.server 4173
  ```
- **Netzwerk-Zugriff:** Aufruf über die lokale Host-IP (z. B. `http://192.168.x.x:4173/`) oder via Port-Forwarding (`adb reverse tcp:4173 tcp:4173` für Android-Emulatoren).
- **Testdatensatz:** `sample_library.json` im selben Verzeichnis oder per Datei-Download auf das Testgerät übertragen.

## Testmatrix

| Phase / Flow | Android (Chrome) | iOS (Safari) | Soll-Ergebnis / Kriterium |
|---|---|---|---|
| **1. Erststart & Shell** | Seite online im Browser öffnen | Seite online in Safari öffnen | Hero-Header, Theme, Suchleiste und Statusleiste („Noch keine Bibliothek geladen.“) laden fehlerfrei. Service Worker registriert sich. |
| **2. Installation (A2HS)** | Dreipunkt-Menü > „Zum Startbildschirm hinzufügen“ / Install-Banner | Teilen-Menü > „Zum Home-Bildschirm“ | App installiert sich als Standalone-PWA mit korrektem DokuReader-Icon (`192x192`, `512x512`, `apple-touch-icon`). |
| **3. Demo- & Datei-Import** | Klick auf „Demo laden“ oder Datei-Import via Dateimanager | Klick auf „Demo laden“ oder Auswahl aus „Dateien“-App | Themenliste und Dokumentkarten füllen sich; Kennzahlen (3 Themen, Dokumente) in der Statusleiste stimmen überein. |
| **4. Navigation & Suche** | Themen anklicken, Suchfeld nutzen | Themen anklicken, Suchfeld nutzen | Themenfilter schränkt Dokumentenliste sofort ein; Volltextsuche filtert verzögerungsfrei; keine horizontalen Umbrüche. |
| **5. Status-Toggle** | Antippen einer Dokumentkarte | Antippen einer Dokumentkarte | Status wechselt wechselseitig zwischen „Ungelesen“ und „✓ Gelesen“; visuelle Hervorhebung (grüner Akzent) passt sich an. |
| **6. Status-Export** | Klick auf „Bibliothek exportieren“ | Klick auf „Bibliothek exportieren“ | Download von `dokureader-library-v1.json` wird ausgelöst; Schema-Integrität und geänderte Lesestatus-Werte bleiben erhalten. |
| **7. Offline-Neustart** | Flugmodus aktivieren, PWA aus App-Switcher neu starten | Flugmodus aktivieren, PWA neu öffnen | App startet vollständig aus dem Service Worker Cache; bereits importierte Bibliothek bleibt bedienbar. |
| **8. Fehlerbehandlung** | Upload einer beschädigten JSON-Datei | Upload einer beschädigten JSON-Datei | Rote Fehlermeldung in Statusleiste („Fehler: Unbekanntes Schema“ oder „Ungültige JSON-Datei.“); kein App-Crash. |

## Viewport-Spezifikationen

- **Android Standard:** 412 × 915 px (z. B. Google Pixel / Samsung Galaxy)
- **iOS Standard:** 393 × 852 px (z. B. iPhone 14/15/16 Pro mit Dynamic Island und Safe-Area-Insets)
- **Kriterium:** Vollständige Bedienbarkeit ohne horizontales Scrollen; Safe Areas (`safe-area-inset-top`, `safe-area-inset-bottom`) werden respektiert.

## Screenshot-Ablage & Dokumentation

Bei der Durchführung des Gerätesmokes (`TW-DOKUREADER-02`) sind standardisierte Screenshots im PNG-Format abzulegen:
- `README/screenshots/mobile/pwa-android-library.png` (Android Themen- & Dokumentansicht)
- `README/screenshots/mobile/pwa-android-offline.png` (Android Offline-Lauf im Flugmodus)
- `README/screenshots/mobile/pwa-ios-library.png` (iOS Themen- & Dokumentansicht mit Safe Area)
- `README/screenshots/mobile/pwa-ios-offline.png` (iOS Offline-Lauf)

## Abnahmekriterien (Gate SNW-DOKUREADER-02)

1. `sample_library.json` liegt als validierte, datenschutzsichere Schema-Referenz vor.
2. `PWA_TESTPLAN.md` ist im Repository fixiert und referenziert.
3. Node-Testsuite (`npm test`) validiert die Testplan-Präsenz, die Sample-Bibliothek und alle PWA-Spezifikationen.
4. Echte native Mobile-Entwicklungen (Capacitor/React Native) bleiben solange blockiert, bis die Befunde aus `TW-DOKUREADER-02` ausgewertet sind.
