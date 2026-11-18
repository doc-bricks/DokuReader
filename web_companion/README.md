# DokuReader Web/PWA Companion

Der Companion ist die mobile und browserfreundliche Begleitschicht für
`dokureader-library-v1.json`. Er lädt lokale JSON-Exporte aus der Desktop-App,
zeigt Themen, Dokumentnamen, Lesestatus und Missing-Flags an, erlaubt das
Umschalten des Lesestatus per Klick oder Tastatur (`Enter`/`Leertaste`), hält
den Arbeitsstand offline-persistent im lokalen Browser-Speicher (`localStorage`)
und exportiert aktualisierte `dokureader-library-v1.json`-Dateien für den
Rückimport am Desktop (`Status importieren…`).

Die Oberfläche unterstützt vollständig alle 6 Tier-2-Sprachen (`Deutsch`,
`English`, `Español`, `简体中文`, `日本語`, `Русский`) mit automatischer
Spracherkennung, manuellem Umschalter (`#lang-select`) und barrierefreier
Tastaturbedienung (`44 px` Touch-Ziele, `aria-live="polite"`).

## Ziel

- Android und iOS bekommen bewusst keinen nativen Voll-Clone (`Regel e2`).
- Der belastbare Mobilpfad ist eine installierbare Offline-PWA (`Regel c`, `Regel d`, `Regel g`).
- Capacitor bleibt optional und wird erst erwogen, wenn ein echter Gerätesmoke (`TW-DOKUREADER-02`) konkreten nativen Mehrwert belegt.

## Lokaler Smoke

```bash
npm test
```

Das prüft:

- Manifest, Icons, Touch-Targets und Mobile-Metadaten (inkl. iOS Safe-Area-Härtung)
- Offline-Shell und `ASSET_HASH`-Wächter über den Service Worker (`sw.js`)
- 6-Sprachen-Parität (`DE/EN/ES/ZH/JA/RU`) in `i18n.js`
- Lokale Offline-Persistenz (`saveLibrarySnapshot` / `loadLibrarySnapshot` / `clearLibrarySnapshot`), Selbstheilung bei korruptem Storage und 4-MiB-Größenwächter
- Parsebare Demo- und Sample-Library mit dem produktiven JSON-Schema

## Lokaler Browserlauf

```bash
python -m http.server 4173
```

Dann im Browser öffnen:

- `http://127.0.0.1:4173/web_companion/`
- `http://127.0.0.1:4173/web_companion/?demo=1`
- `http://127.0.0.1:4173/web_companion/?lang=en` (oder `es`, `zh`, `ja`, `ru`)

## Android/iOS-PWA-Smoke

1. Companion lokal per HTTP bereitstellen (`python -m http.server 4173`).
2. `?demo=1`, die synthetische `sample_library.json` oder eine eigene `dokureader-library-v1.json` laden.
3. Android: in Chrome „Zum Startbildschirm hinzufügen“ prüfen (412 × 915 px).
4. iOS: in Safari „Zum Home-Bildschirm“ prüfen (393 × 852 px mit Safe Area).
5. Flugmodus aktivieren, App schließen und neu öffnen: Shell lädt aus dem Service-Worker-Cache (`v9`) und die zuletzt geladene Bibliothek inkl. geänderter Gelesen-Markierungen wird automatisch aus `localStorage` wiederhergestellt.
6. Über „Lokale Daten löschen“ (`#clear-btn`) prüfen, dass der lokale Offline-Zwischenspeicher jederzeit rückstandsfrei geleert werden kann.
7. Ausführliche Testmatrix und Screenshot-Kriterien: siehe [PWA_TESTPLAN.md](PWA_TESTPLAN.md).

## Grenzen

- Keine Dokumentinhalte im Standardexport (`INV-SCHEMA-04`)
- Kein nativer Zugriff auf beliebige Desktop-Pfade (`INV-INPLACE-03`)
- Kein Hintergrund-Sync, kein Server-Upload und keine Push-Logik (`INV-LOCAL-01`)

Für diese Companion-Linie ist das Absicht: Die Desktop-App bleibt die
autoritative Bibliothek, mobil wird ausschließlich der inhaltsfreie
Metadaten-Export gespiegelt und per `dokureader-library-v1.json` abgeglichen.
