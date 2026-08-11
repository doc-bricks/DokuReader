# Konsolidierte Differenzen con2

Stand: 2026-08-11

## P1/P2 – offen vor einer echten Veröffentlichung

1. Einen autorisierten Windows-Build erzeugen, MSIX signieren und Publisher-
   sowie PFX-Readback dokumentieren.
2. Den signierten Build mit WACK ausführen und XML plus geparste JSON-
   Zusammenfassung kontrolliert ablegen.
3. Partner-Center-/Store-Status mit ausdrücklicher Besitzerfreigabe lesen;
   `STORE_LISTING.md` bleibt bis dahin vorbereitete Copy.

## P2/P3 – offen für vollständige UI-Abnahme

1. Auf einem vollständigen Windows-Tk/ttk-Host den GUI-Regressionstest und den
   visuellen Smoke ausführen.
2. Einen echten Tastatur-/Fokus- und Screenreader-Test mit dem vorgesehenen
   Windows-Assistenzstack durchführen; das Ergebnis getrennt vom statischen
   Metadata-Contract protokollieren.
3. Einen kontrollierten Android-/iOS-/PWA-Gerätesmoke nur mit realem Gerät oder
   autorisiertem Runner nachholen; `npm test` allein bleibt lokaler Code-Smoke.

## Bewusst keine Differenzbehebung in diesem Bündel

- Kein Push, Tag, GitHub-Release oder Store-Upload.
- Keine OneDrive-Synchronisierung und keine Übernahme von `WORKSTATION-LG`-
  Kopien, generierten Releases oder fremden Asset-Ständen.
- Keine Erfindung von Release-, Screenreader-, Geräte- oder visuellen
  Abnahmedaten.
