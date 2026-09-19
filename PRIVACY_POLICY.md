# Datenschutz - DokuReader

Stand: 2026-08-11

Die Dokumentation beschreibt den Entwicklungsstand `1.0.1-dev`; die Store-
Paketmetadaten `1.0.1.0` sind keine Aussage über eine Einreichung oder
Veröffentlichung. Siehe `RELEASE_STATUS.md` für den belegten Gate-Stand.

## Kurzfassung

DokuReader arbeitet lokal auf dem Gerät. Die App lädt Dokumente nicht in externe Dienste hoch und betreibt keinen eigenen Cloud- oder Sync-Server.

## Welche Daten verarbeitet die App?

- Themennamen
- Dateipfade zu verknüpften Dokumenten
- Gelesen-/Ungelesen-Status
- Lokale Metadaten wie Dateigröße oder Änderungszeit, wenn ein Export ausgelöst wird

Diese Daten werden lokal in `~/.dokubibliothek_state.json` gespeichert.

## Welche Daten werden nicht standardmäßig übertragen?

- Dokumentinhalte
- Vorschaubilder
- PDFs oder Office-Dateien
- Konten, Tokens oder Cloud-Zugangsdaten

Der Standardexport `dokureader-library-v1.json` enthält nur Themen, Pfade, Dateimetadaten und Lesestatus. Dokumentinhalte werden dabei bewusst nicht eingebettet.

## Netzwerkzugriffe

Die Kern-App benötigt keinen eigenen Online-Dienst. Einzelne optionale Systemkomponenten wie LibreOffice oder Word-Integrationen laufen lokal. Store- oder GitHub-Links werden nur geöffnet, wenn der Nutzer selbst entsprechende Seiten besucht.

## Open-Source- und Lizenzhinweis

DokuReader steht unter AGPL-3.0. Optionale PDF-Vorschau kann PyMuPDF verwenden, das ebenfalls im AGPL-Kontext steht. Die Drittanbieter-Übersicht liegt in `THIRD_PARTY_LICENSES.txt`.

## Support und Rückfragen

Support- und Kontaktwege stehen in `SUPPORT.md`.
