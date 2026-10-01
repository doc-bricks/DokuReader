# Beitragsrichtlinie / Contributing Guide

## Deutsch

Vielen Dank für Ihr Interesse, zu diesem Projekt beizutragen.

### Wie Sie beitragen können

1. Melden Sie Bugs über GitHub Issues mit nachvollziehbaren Schritten.
2. Schlagen Sie Features über GitHub Issues vor.
3. Reichen Sie Code- oder Dokumentationsänderungen per Pull Request ein.

Bitte veröffentlichen Sie keine Secrets, privaten Dokumente oder Sicherheitslücken in öffentlichen Issues. Für Sicherheitsmeldungen gilt `SECURITY.md`.

### Pull Requests

1. Forken Sie das Repository.
2. Erstellen Sie einen Feature-Branch: `git checkout -b feature/mein-feature`.
3. Testen Sie Ihre Änderung lokal.
4. Committen Sie Ihre Änderung: `git commit -m "Beschreibung der Änderung"`.
5. Pushen Sie den Branch und erstellen Sie einen Pull Request.

### Lizenz- und Rechtehinweise

Pull Requests werden unter der Projektlizenz eingereicht, sofern im konkreten Beitrag nichts anderes vereinbart ist. Bitte reichen Sie nur Code, Dokumentation oder Assets ein, die Sie unter dieser Lizenz beisteuern dürfen.

### Code-Richtlinien

- Python: PEP 8 Stil
- Encoding: UTF-8
- Keine hardcoded lokalen Pfade
- Keine API-Keys, Tokens, Passwörter oder privaten Dokumente
- Lokale Build-Artefakte bleiben ungetrackt

### Qualitäts-Gates & Automatisierte Tests

Vor jedem Pull Request oder Commit müssen alle lokalen Qualitätsprüfungen fehlerfrei bestehen:

```bash
# 1. Vollständige Python-Testsuite ausführen (inklusive Metadaten- und Vertragstests)
pytest -ra -v

# 2. Linter & statische Codeanalyse
ruff check .

# 3. Vollständige Bytecode-Kompilierung
python -m compileall -q .

# 4. Mobile Web-Companion-Testsuite
cd web_companion && node --test
```

### Architektonische Invarianten & Governance

Beiträge müssen alle 10 Kern-Invarianten des Projekts respektieren:
- `INV-LOCAL-01` (100% Local-First & Zero Egress): Keine Hintergrund-Netzwerkverbindungen, Telemetrie oder externe API-Aufrufe.
- `INV-RUNAS-02` (Unprivilegierter Modus): Standard-Benutzerrechte (`RunAsInvoker`), keine Admin-Rechte erforderlich.
- `INV-INPLACE-03` (Originale unverändert): Dokumente verbleiben an Ort und Stelle; keine Dateimanipulation im Dateisystem.
- `INV-SCHEMA-04` (Deterministisches Schema): Bibliotheks-Exporte folgen strikt der `dokureader-library-v1` Spezifikation.
- `INV-ISOLATION-05` (Zustands- & Cache-Isolation): Lokaler Zustand in `~/.dokubibliothek_state.json`; isolierter PWA-Cache.
- `INV-SANDBOX-06` (Sichere Subprozesse): Optionale externe Tools (LibreOffice, Poppler) laufen mit Timeouts.
- `INV-PARITY-07` (Plattform-Parität): Vollständige Unterstützung für Windows, macOS und Linux.
- `INV-A11Y-08` (Barrierefreiheit): Tastaturbedienbarkeit und semantische Rollen für alle Steuerelemente.
- `INV-DISCOVERY-09` (Transparenz): Zweisprachige Dokumentation (EN/DE) und gepflegte `llms.txt`.
- `INV-SLA-10` (Sicherheits-SLA): 48h-Erstreaktionszeit und 5-Werktage-Triage gem. `SECURITY.md`.

### Plan D Lokales Setup & Versions-Disziplin

- **Kanonischer Arbeitsort:** Lokaler Git-Klon unter `C:\_Local_DEV\repos\REL-PUB_DokuReader-tasksolver-1084-1085`.
- **OneDrive-Spiegel:** `C:\Users\lukas\OneDrive\.TOPICS\.SOFTWARE\DOCS\REL-PUB_DokuReader` dient als gitloser Spiegel.
- **Versions-Freeze (T-20260920-167562623):** Die Versionsnummer (`1.0.1-dev` / `1.0.1.dev0`) bleibt für laufende Hygiene- und Marketing-Läufe strikt eingefroren. Alle Neuerungen werden unter `## [Unreleased]` im `CHANGELOG.md` erfasst.

### Erste Schritte

```bash
git clone https://github.com/doc-bricks/DokuReader.git
cd DokuReader
pip install -r requirements.txt
python DokuReader.py
```

---

## English

Thank you for your interest in contributing to this project.

### How to Contribute

1. Report bugs through GitHub Issues with reproducible steps.
2. Suggest features through GitHub Issues.
3. Submit code or documentation changes through Pull Requests.

Do not publish secrets, private documents, or security vulnerability details in public issues. For security reports, use `SECURITY.md`.

### Pull Requests

1. Fork the repository.
2. Create a feature branch: `git checkout -b feature/my-feature`.
3. Test your change locally.
4. Commit your change: `git commit -m "Description of change"`.
5. Push the branch and open a Pull Request.

### Licensing and Contribution Terms

Pull requests are submitted under the project license unless otherwise agreed for a specific contribution. Please submit only code, documentation, or assets that you are allowed to contribute under that license.

### Code Guidelines

- Python: PEP 8 style
- Encoding: UTF-8
- No hardcoded local paths
- No API keys, tokens, passwords, or private documents
- Local build artifacts stay untracked

### Quality Gates & Automated Verification

All pull requests and commits must pass local verification gates before submission:

```bash
# 1. Full Python test suite (including contract and metadata validation)
pytest -ra -v

# 2. Fast linting and static analysis
ruff check .

# 3. Whole-repository bytecode compilation
python -m compileall -q .

# 4. Mobile Web Companion test runner
cd web_companion && node --test
```

### Architectural Invariants & Governance

Contributions must preserve all 10 architectural and runtime invariants:
- `INV-LOCAL-01` (100% Local-First & Zero Egress): No outbound network requests, analytics, or external telemetry.
- `INV-RUNAS-02` (Unprivileged User Mode): Executes purely under `RunAsInvoker` without administrative elevation.
- `INV-INPLACE-03` (In-Place File Safety): Original documents are strictly read-only; originals never moved or altered.
- `INV-SCHEMA-04` (Deterministic Schema): Export payloads adhere to the versioned `dokureader-library-v1` JSON specification.
- `INV-ISOLATION-05` (State & Cache Isolation): Isolated user state in `~/.dokubibliothek_state.json`; scoped PWA cache.
- `INV-SANDBOX-06` (Safe Subprocesses): Bounded execution with strict timeout limits for optional tools.
- `INV-PARITY-07` (Tri-Platform Support): Parity across Windows, macOS, and Linux host environments.
- `INV-A11Y-08` (Accessibility): Full keyboard navigation and semantic roles across the UI.
- `INV-DISCOVERY-09` (Transparency): Bilingual documentation parity (EN/DE) and machine-readable `llms.txt`.
- `INV-SLA-10` (Security Response SLA): Binding 48-hour initial response and 5-day triage commitment.

### Plan D Setup & Version Freeze Discipline

- **Canonical Repository:** Local Git clone at `C:\_Local_DEV\repos\REL-PUB_DokuReader-tasksolver-1084-1085`.
- **OneDrive Mirror:** `C:\Users\lukas\OneDrive\.TOPICS\.SOFTWARE\DOCS\REL-PUB_DokuReader` serves as gitless multi-device mirror.
- **Version Freeze (T-20260920-167562623):** Version numbers (`1.0.1-dev` / `1.0.1.dev0`) remain strictly frozen during routine maintenance. All enhancements are tracked under `## [Unreleased]` in `CHANGELOG.md`.

### Getting Started

```bash
git clone https://github.com/doc-bricks/DokuReader.git
cd DokuReader
pip install -r requirements.txt
python DokuReader.py
```
