# Konsolidierte Differenzen con2

Stand: 2026-08-26

## P1/P2 – offen vor einer echten Veröffentlichung

1. Einen autorisierten Windows-Build erzeugen, MSIX signieren und Publisher-
   sowie PFX-Readback dokumentieren.
2. Den signierten Build mit WACK ausführen und XML plus geparste JSON-
   Zusammenfassung kontrolliert ablegen.
3. Partner-Center-/Store-Status mit ausdrücklicher Besitzerfreigabe lesen;
   `STORE_LISTING.md` bleibt bis dahin vorbereitete Copy.

## Lokal geschlossen: UI-Polish und Visual-Smoke

1. Windows-Tk/ttk-GUI-Regression: 46/46 Python-Tests, einschließlich echter
   Fenstergeometrie und metadata-first Zustände.
2. Synthetischer Visual-Smoke für Leer-, Drag-and-drop- und Vorschauzustand;
   Bilder und Hashes stehen in `UI_POLISH_SMOKE.json`.

## P2/P3 – offen für externe UI-/Geräteabnahme

1. Einen echten Tastaturhardware-/Fokus- und Screenreader-Test mit dem vorgesehenen
   Windows-Assistenzstack durchführen; das Ergebnis getrennt vom statischen
   Metadata-Contract protokollieren.
2. Einen kontrollierten Android-/iOS-/PWA-Gerätesmoke nur mit realem Gerät oder
   autorisiertem Runner nachholen; `npm test` allein bleibt lokaler Code-Smoke.

## Bewusst keine Differenzbehebung in diesem Bündel

- Kein Tag, GitHub-Release oder Store-Upload.
- Keine OneDrive-Synchronisierung und keine Übernahme von `WORKSTATION-LG`-
  Kopien, generierten Releases oder fremden Asset-Ständen.
- Keine Erfindung von Release-, Screenreader- oder Geräteabnahmedaten.
