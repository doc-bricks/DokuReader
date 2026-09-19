# DokuReader Web/PWA Companion

Der Companion ist die mobile und browserfreundliche Leseschicht für
`dokureader-library-v1.json`. Er lädt lokale JSON-Exporte aus der Desktop-App,
zeigt Themen, Dokumentnamen, Lesestatus und Missing-Flags an und bleibt dabei
read-only.

Der Importbereich ist per Tastatur aktivierbar; Themenfilter sind native
Schaltflächen und der aktuelle Ladezustand wird als Statusmeldung ausgegeben.

## Ziel

- Android und iOS sollen keinen nativen Voll-Clone bekommen.
- Der erste belastbare Mobilpfad ist eine installierbare PWA.
- Capacitor bleibt optional und wird erst sinnvoll, wenn echte native
  Mehrwerte wie Dateiauswahl-Workflows, Notifications oder Store-Verteilung
  belegt sind.

## Lokaler Smoke

```bash
npm test
```

Das prüft:

- Manifest, Icons und Mobile-Metadaten
- Offline-Shell über den Service Worker
- parsebare Demo-Library mit dem produktiven JSON-Schema

## Lokaler Browserlauf

```bash
python -m http.server 4173
```

Dann im Browser öffnen:

- `http://127.0.0.1:4173/web_companion/`
- `http://127.0.0.1:4173/web_companion/?demo=1`

## Android/iOS-PWA-Smoke

1. Companion lokal per HTTP bereitstellen (`python -m http.server 4173`).
2. `?demo=1`, die synthetische `sample_library.json` oder eine eigene `dokureader-library-v1.json` laden.
3. Android: in Chrome "Zum Startbildschirm hinzufügen" prüfen (412 × 915 px).
4. iOS: in Safari "Zum Home-Bildschirm" prüfen (393 × 852 px mit Safe Area).
5. Offline erneut öffnen und Demo-/Shell-Ladepfad gegen den Service Worker validieren.
6. Ausführliche Testmatrix und Screenshot-Kriterien: siehe [PWA_TESTPLAN.md](PWA_TESTPLAN.md).


## Grenzen

- Keine Dokumentinhalte im Standardexport
- Kein nativer Zugriff auf beliebige Desktop-Pfade
- Kein Hintergrund-Sync und keine Push-Logik

Für diese Companion-Linie ist das Absicht: Die Desktop-App bleibt die
autoritative Bibliothek, mobil wird nur der redigierte Export gespiegelt.
