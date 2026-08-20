# Sicherheitsrichtlinie / Security Policy

## Deutsch

### Sicherheitsmodell & Invarianten

DokuReader ist als lokale, offline-fähige Desktop-Dokumentenbibliothek für Windows, macOS und Linux konzipiert. Folgende Sicherheits- und Datenschutzprinzipien sind fest im Architekturdesign verankert:

1. **100% Offline & Zero-Egress**: Die Desktop-Anwendung baut keine ausgehenden Netzwerkverbindungen auf. Es findet keinerlei Übertragung von Telemetriedaten, Dokumenten, Dateinamen oder Metadaten an externe Server oder Cloud-Dienste statt.
2. **Originaldatei-Schutz (In-Place Reference Only)**: Originaldokumente werden zu keinem Zeitpunkt verändert, verschoben oder eigenmächtig überschrieben. DokuReader liest Dateien ausschließlich schreibgeschützt (Read-Only) für Vorschau und Metadaten-Extraktion.
3. **Zustands- und Datenisolation**: Die Anwendungsdaten (Themen, Pfadreferenzen und Lesestatus) werden in einer isolierten Benutzerstatusdatei (`~/.dokubibliothek_state.json`) abgelegt. Exporte (`dokureader-library-v1.json`) enthalten rein strukturelle Metadaten und niemals sensible Datei-Binärinhalte.
4. **Non-Elevation & Least Privilege**: DokuReader erfordert und erbittet keine Administrator- oder Root-Rechte und läuft vollständig im Standard-Benutzerkontext.
5. **Sichere Konvertierung**: Externe Werkzeuge für Dokumentkonvertierungen (wie LibreOffice oder PyMuPDF) werden lokal mit deterministischen Argumenten und isolierten temporären Pfaden ausgeführt.

### Unterstützte Versionen

| Version | Status |
| --- | --- |
| Aktueller `master` | Unterstützt (Security Fixes & Updates) |

### Sicherheitslücken melden

Wenn Sie eine Sicherheitslücke finden, melden Sie diese bitte verantwortungsvoll und vertraulich:

1. **GitHub Private Vulnerability Reporting**: Navigieren Sie zu `Security` -> `Advisories` -> `Report a vulnerability`.
2. **Direkte E-Mail**: Schreiben Sie vertraulich an [security@ellmos.ai](mailto:security@ellmos.ai) mit dem Betreff `[SECURITY] DokuReader Vulnerability Report`.
3. Beschreiben Sie Reproduktionsschritte, betroffene Plattformen/Versionen und mögliche Auswirkungen.
4. Bitte veröffentlichen Sie keine technischen Details in öffentlichen GitHub-Issues, bis eine Behebung bereitsteht.

---

## English

### Security Model & Invariants

DokuReader is designed as a local-first, offline document library for Windows, macOS, and Linux. The following core security and privacy invariants guide its design:

1. **100% Offline & Zero-Egress**: The desktop application operates entirely offline without outbound network calls. No telemetry, user files, document names, or metadata are ever transmitted to external servers or cloud services.
2. **In-Place File Safety**: Original files are never modified, moved, or deleted. Documents are opened strictly in read-only mode for preview rendering and metadata extraction.
3. **State & Metadata Isolation**: Application state (topics, file references, and read status) is stored locally in `~/.dokubibliothek_state.json`. Exports (`dokureader-library-v1.json`) contain structural metadata only and never include embedded binary document content.
4. **Non-Elevation & Least Privilege**: DokuReader operates purely in standard user mode and requires no administrative elevation.
5. **Safe Conversion Sandboxing**: External document conversion backends (such as LibreOffice or PyMuPDF) are executed locally with bounded parameters and isolated temporary paths.

### Supported Versions

| Version | Status |
| --- | --- |
| Current `master` | Supported (Security Fixes & Updates) |

### Reporting a Vulnerability

If you identify a potential security issue or vulnerability, please report it responsibly and privately:

1. **GitHub Private Vulnerability Reporting**: Go to `Security` -> `Advisories` -> `Report a vulnerability`.
2. **Direct Security Email**: Send details confidentially to [security@ellmos.ai](mailto:security@ellmos.ai) with subject `[SECURITY] DokuReader Vulnerability Report`.
3. Provide reproduction steps, affected versions/environments, and impact assessment.
4. Please do not open public issues with exploit details before a fix is released.
