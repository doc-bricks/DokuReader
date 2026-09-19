# Sicherheitsrichtlinie / Security Policy

## Deutsch

### Sicherheitsmodell & Invarianten

DokuReader ist als lokale, offline-fähige Desktop-Dokumentenbibliothek für Windows, macOS und Linux konzipiert. Folgende Sicherheits- und Datenschutzprinzipien sind fest im Architekturdesign verankert:

1. **100% Offline & Zero-Egress (INV-LOCAL-01)**: Die Desktop-Anwendung baut keine ausgehenden Netzwerkverbindungen auf. Es findet keinerlei Übertragung von Telemetriedaten, Dokumenten, Dateinamen oder Metadaten an externe Server oder Cloud-Dienste statt.
2. **Unprivilegierte Ausführung / Non-Elevation (INV-RUNAS-02)**: DokuReader erfordert und erbittet keine Administrator- oder Root-Rechte und läuft vollständig im Standard-Benutzerkontext (RunAsInvoker).
3. **Originaldatei-Schutz (INV-INPLACE-03)**: Originaldokumente werden zu keinem Zeitpunkt verändert, verschoben oder eigenmächtig überschrieben. DokuReader liest Dateien ausschließlich schreibgeschützt (Read-Only) für Vorschau und Metadaten-Extraktion.
4. **Zustands- und Datenisolation (INV-ISOLATION-05)**: Die Anwendungsdaten (Themen, Pfadreferenzen und Lesestatus) werden in einer isolierten Benutzerstatusdatei (~/.dokubibliothek_state.json) abgelegt. Exporte (dokureader-library-v1.json) enthalten rein strukturelle Metadaten und niemals sensible Datei-Binärinhalte.
5. **Sichere Konvertierung (INV-SANDBOX-06)**: Externe Werkzeuge für Dokumentkonvertierungen (wie LibreOffice oder PyMuPDF) werden lokal mit deterministischen Argumenten, strengen Timeouts und isolierten temporären Pfaden ausgeführt.

### Service-Level-Agreements (SLA) & Reaktionszeiten (INV-SLA-10)

- **Erstreaktion:** Innerhalb von **48 Stunden** nach Eingang einer Meldung bestätigen wir den Empfang.
- **Triage & Klassifikation:** Innerhalb von **5 Werktagen** erfolgt eine formale Sicherheitsbewertung und Schweregrad-Einstufung (CVSS).
- **Behebung:** Kritische Schwachstellen werden prioritär behoben und über GitHub Security Advisories transparent kommuniziert.

### Unterstützte Versionen

| Version | Status |
| --- | --- |
| Aktueller master (1.0.1-dev) | Unterstützt (Security Fixes & Updates) |

### Sicherheitslücken melden

Wenn Sie eine Sicherheitslücke finden, melden Sie diese bitte verantwortungsvoll und vertraulich:

1. **GitHub Private Vulnerability Reporting**: Navigieren Sie zu Security -> Advisories -> Report a vulnerability.
2. **Direkte Sicherheits-E-Mails**:
   - security@open-bricks.org
   - security@ellmos.ai
   - support@lukasgeiger.com
   - lukas@open-bricks.org
   Betreff: [SECURITY] DokuReader Vulnerability Report
3. Beschreiben Sie Reproduktionsschritte, betroffene Plattformen/Versionen und mögliche Auswirkungen.
4. Bitte veröffentlichen Sie keine technischen Details in öffentlichen GitHub-Issues, bis eine Behebung bereitsteht.

---

## English

### Security Model & Invariants

DokuReader is designed as a local-first, offline document library for Windows, macOS, and Linux. The following core security and privacy invariants guide its design:

1. **100% Offline & Zero-Egress (INV-LOCAL-01)**: The desktop application operates entirely offline without outbound network calls. No telemetry, user files, document names, or metadata are ever transmitted to external servers or cloud services.
2. **Unprivileged Execution / Non-Elevation (INV-RUNAS-02)**: DokuReader runs strictly in standard user mode under RunAsInvoker principles and requires no administrative elevation.
3. **In-Place File Safety (INV-INPLACE-03)**: Original files are never modified, moved, or deleted. Documents are opened strictly in read-only mode for preview rendering and metadata extraction.
4. **State & Metadata Isolation (INV-ISOLATION-05)**: Application state (topics, file references, and read status) is stored locally in ~/.dokubibliothek_state.json. Exports (dokureader-library-v1.json) contain structural metadata only and never include embedded binary document content.
5. **Safe Conversion Sandboxing (INV-SANDBOX-06)**: External document conversion backends (such as LibreOffice or PyMuPDF) are executed locally with bounded parameters, strict timeouts, and isolated temporary paths.

### Service-Level Agreements (SLA) & Response Times (INV-SLA-10)

- **Initial Acknowledgement:** Within **48 hours** of report receipt.
- **Triage & Classification:** Within **5 business days** with formal severity rating.
- **Remediation:** Critical fixes are deployed with highest priority via GitHub Security Advisories.

### Supported Versions

| Version | Status |
| --- | --- |
| Current master (1.0.1-dev) | Supported (Security Fixes & Updates) |

### Reporting a Vulnerability

If you identify a potential security issue or vulnerability, please report it responsibly and privately:

1. **GitHub Private Vulnerability Reporting**: Go to Security -> Advisories -> Report a vulnerability.
2. **Direct Security Emails**:
   - security@open-bricks.org
   - security@ellmos.ai
   - support@lukasgeiger.com
   - lukas@open-bricks.org
   Subject: [SECURITY] DokuReader Vulnerability Report
3. Provide reproduction steps, affected versions/environments, and impact assessment.
4. Please do not open public issues with exploit details before a fix is released.
