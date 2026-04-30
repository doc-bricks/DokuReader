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

### Getting Started

```bash
git clone https://github.com/doc-bricks/DokuReader.git
cd DokuReader
pip install -r requirements.txt
python DokuReader.py
```
