'''Automated metadata, manifest, documentation, and security parity tests for DokuReader.'''

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def gh_slug(text: str) -> str:
    text = text.replace("`", "")
    cleaned = re.sub(r"[^\w\s-]", "", text.lower())
    return cleaned.replace(" ", "-")


def test_pyproject_metadata() -> None:
    content = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'name = "dokureader"' in content
    assert 'version = "1.0.1.dev0"' in content
    assert 'requires-python = ">=3.10"' in content
    assert "https://github.com/doc-bricks/DokuReader" in content
    assert 'license = { text = "AGPL-3.0" }' in content
    assert "Documentation" in content
    assert "Changelog" in content
    assert "Security" in content
    assert "Third-Party Licenses" in content
    assert "Marketing Log" in content
    assert "LLM Context" in content
    assert "Parent Organization" in content
    assert "Umbrella Ecosystem" in content
    assert 'addopts = "-ra -v"' in content


def test_readme_badges_and_links_parity() -> None:
    readme_en = (ROOT / "README.md").read_text(encoding="utf-8")
    readme_de = (ROOT / "README_de.md").read_text(encoding="utf-8")

    assert "License-AGPL--3.0-green" in readme_en
    assert "Version-1.0.1--dev-blue" in readme_en
    assert "Python-3.10%2B-blue" in readme_en
    assert "Platform-Windows" in readme_en
    assert "LLM--Ready-llms.txt-success" in readme_en
    assert "Ecosystem-doc--bricks-purple" in readme_en
    assert "open--bricks-blue" in readme_en
    assert "Security%20SLA-48h%20%2F%205d-orange" in readme_en
    assert "RunAsInvoker-Non--Elevated-success" in readme_en
    assert "Third--Party%20Licenses-Audited-green" in readme_en
    assert "Marketing%20Log-Active-blue" in readme_en
    assert "Audit-2026--09--25-informational" in readme_en or "Audit-2026--09--22-informational" in readme_en
    assert "Attribution-NOTICE-blue" in readme_en

    assert "License-AGPL--3.0-green" in readme_de
    assert "Version-1.0.1--dev-blue" in readme_de
    assert "Python-3.10%2B-blue" in readme_de
    assert "Platform-Windows" in readme_de
    assert "LLM--Ready-llms.txt-success" in readme_de
    assert "doc--bricks-purple" in readme_de
    assert "open--bricks-blue" in readme_de
    assert "Sicherheits--SLA-48h%20%2F%205d-orange" in readme_de
    assert "RunAsInvoker-Unprivilegiert-success" in readme_de
    assert "Marketing%20Log-Aktiv-blue" in readme_de
    assert "Audit-2026--09--25-informational" in readme_de or "Audit-2026--09--22-informational" in readme_de
    assert "Attribution-NOTICE-blue" in readme_de

    for readme in (readme_en, readme_de):
        assert "https://github.com/doc-bricks/LitZentrum" in readme
        assert "https://github.com/doc-bricks/CleanMarkdown" in readme
        assert "https://github.com/doc-bricks/UniversalDocsGrabber" in readme
        assert "https://github.com/open-bricks" in readme


def test_test_badges_report_each_suite_separately() -> None:
    '''Ein Testbadge darf zwei Suiten nicht zu einer Zahl verschmelzen.'''
    for name in ("README.md", "README_de.md"):
        readme = (ROOT / name).read_text(encoding="utf-8")
        assert "Pytest-" in readme, f"{name}: kein eigenes Pytest-Badge"
        assert "Web%20Companion-" in readme, f"{name}: kein eigenes Node-Badge"
        assert "Tests-" not in readme, (
            f"{name}: summierendes 'Tests-...'-Badge ist zurueck -- Suiten "
            f"werden getrennt ausgewiesen, nicht addiert"
        )


def test_readme_18_point_navigation_and_anchors() -> None:
    '''Prüft die 18-Punkte-Schnellnavigation und reziproke Ankerparität in EN und DE.'''
    for filename in ("README.md", "README_de.md"):
        text = (ROOT / filename).read_text(encoding="utf-8")
        nav_match = re.search(r"(?:### Quick Navigation|### Schnellnavigation)\s*\n(.*?)\n---", text, re.DOTALL)
        assert nav_match, f"{filename}: Keine Quick Navigation gefunden"
        links = re.findall(r"\[([^\]]+)\]\(#([^\)]+)\)", nav_match.group(1))
        assert len(links) == 18, f"{filename}: Erwartete 18 Navigationspunkte, fand {len(links)}"

        headers = re.findall(r"^##\s+(.+)$", text, re.MULTILINE)
        header_slugs = {gh_slug(h): h for h in headers}

        for title, anchor in links:
            assert anchor in header_slugs or f'id="{anchor}"' in text, (
                f"{filename}: Anker '#{anchor}' für '{title}' entspricht keinem Header oder HTML-Anker. "
                f"Verfügbare Header-Slugs: {list(header_slugs.keys())}"
            )

        # Reziproke duale HTML-Anker sec-01 bis sec-18
        for i in range(1, 19):
            sec_id = f"sec-{i:02d}"
            assert f'<a id="{sec_id}"></a>' in text, f"{filename} fehlt dualer HTML-Anker {sec_id}"


def test_governance_invariants_parity() -> None:
    '''Prüft, dass alle 10 Invarianten in READMEs und MARKETING-LOG vorhanden sind.'''
    invariants = [
        "INV-LOCAL-01",
        "INV-RUNAS-02",
        "INV-INPLACE-03",
        "INV-SCHEMA-04",
        "INV-ISOLATION-05",
        "INV-SANDBOX-06",
        "INV-PARITY-07",
        "INV-A11Y-08",
        "INV-DISCOVERY-09",
        "INV-SLA-10",
    ]
    for filename in ("README.md", "README_de.md", "MARKETING-LOG.txt"):
        text = (ROOT / filename).read_text(encoding="utf-8")
        for inv in invariants:
            assert inv in text, f"{filename} fehlt Invariante {inv}"


def test_dual_mermaid_diagrams() -> None:
    '''Prüft, dass beide READMEs Flowchart- und Sequenzdiagramme enthalten.'''
    for filename in ("README.md", "README_de.md"):
        text = (ROOT / filename).read_text(encoding="utf-8")
        assert "flowchart TD" in text
        assert "sequenceDiagram" in text
        assert "subgraph Host" in text
        assert "autonumber" in text


def test_third_party_licenses_audit() -> None:
    '''Prüft die Vollständigkeit des Drittanbieter-Lizenzinventars.'''
    tpl = (ROOT / "THIRD_PARTY_LICENSES.md").read_text(encoding="utf-8")
    assert "GNU Affero General Public License v3.0" in tpl
    assert "PyMuPDF" in tpl
    assert "Pillow" in tpl
    assert "pypdf" in tpl
    assert "reportlab" in tpl
    assert "RunAsInvoker" in tpl
    assert "Zero-Egress" in tpl
    assert "node:test" in tpl


def test_marketing_log_contract() -> None:
    '''Prüft die Struktur und Personas in MARKETING-LOG.txt.'''
    mlog = (ROOT / "MARKETING-LOG.txt").read_text(encoding="utf-8")
    assert "DokuReader -- Marketing, Discoverability & Architecture Audit" in mlog
    assert "Legal Tech & Compliance Analysts" in mlog
    assert "Academic Researchers & Literature Curators" in mlog
    assert "Offline-First Knowledge Workers & Privacy Advocates" in mlog
    assert "AI Desktop Application Developers & Coding Agents" in mlog
    assert "4-WAY COMPETITIVE MATRIX" in mlog
    assert "HIGH-INTENT SEARCH PHRASES" in mlog


def test_ci_workflow_hardening() -> None:
    '''Prüft, dass der CI-Workflow Concurrency und Bytecode-Kompilierung enthält.'''
    ci_yaml = (ROOT / ".github/workflows/source-platform-smoke.yml").read_text(encoding="utf-8")
    assert "concurrency:" in ci_yaml
    assert "cancel-in-progress: true" in ci_yaml
    assert "compileall" in ci_yaml


def test_llms_txt_currency_and_key_files() -> None:
    llms = (ROOT / "llms.txt").read_text(encoding="utf-8")
    assert re.search(r"^## Last-checked: \d{4}-\d{2}-\d{2}$", llms, re.MULTILINE), (
        "llms.txt braucht einen Kopf '## Last-checked: YYYY-MM-DD'"
    )
    assert "https://github.com/doc-bricks/DokuReader" in llms
    assert "AGPL-3.0" in llms
    assert "counted separately" in llms
    assert re.search(r"Web Companion \d+ passed / 0 failed", llms)
    assert "test_metadata.py" in llms
    assert "THIRD_PARTY_LICENSES.md" in llms
    assert "MARKETING-LOG.txt" in llms


def test_security_policy_bilingual_and_invariants() -> None:
    sec = (ROOT / "SECURITY.md").read_text(encoding="utf-8")
    assert "## Deutsch" in sec
    assert "## English" in sec
    assert "security@ellmos.ai" in sec
    assert "security@open-bricks.org" in sec
    assert "48 Stunden" in sec or "48 hours" in sec
    assert "5 Werktagen" in sec or "5 business days" in sec
    assert "Local-First" in sec or "lokal" in sec.lower()
    assert "Zero-Egress" in sec or "Netzwerk" in sec or "offline" in sec.lower()
    assert "Non-Elevation" in sec or "Administrator" in sec or "user mode" in sec.lower()
    assert "RunAsInvoker" in sec


def test_store_package_parity() -> None:
    package = json.loads((ROOT / "store_package.json").read_text(encoding="utf-8"))
    assert package["identity_name"] == "Geiger.DokuReader"
    assert package["version"] == "1.0.1.0"
    assert package["publisher_display"] == "Geiger"
    assert "https://github.com/doc-bricks/DokuReader" in package["support_url"]


def test_changelog_unreleased_entries() -> None:
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    assert "## [Unreleased]" in changelog
    assert "2026-08-20" in changelog
    assert "2026-09-11" in changelog
    assert "Discoverability" in changelog or "Sichtbarkeit" in changelog


def test_ci_matrix_workflow() -> None:
    '''Prüft den vollwertigen Multi-OS CI-Matrix Workflow.'''
    ci_yaml = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    assert "name: CI" in ci_yaml
    assert "concurrency:" in ci_yaml
    assert "cancel-in-progress: true" in ci_yaml
    assert "contents: read" in ci_yaml
    assert "ubuntu-latest" in ci_yaml
    assert "windows-latest" in ci_yaml
    assert "macos-latest" in ci_yaml
    for py_ver in ("3.10", "3.11", "3.12", "3.13"):
        assert py_ver in ci_yaml
    assert "python3-tk" in ci_yaml
    assert "xvfb" in ci_yaml
    assert "compileall" in ci_yaml
    assert "ruff check ." in ci_yaml
    assert "web-companion" in ci_yaml


def test_pep621_classifiers_and_keywords() -> None:
    '''Prüft PEP 621 Metadaten, Keywords und Python 3.13 Classifier.'''
    pyproj = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'requires = ["setuptools>=77.0"]' in pyproj
    assert 'license-files = ["LICENSE", "NOTICE", "THIRD_PARTY_LICENSES.md", "THIRD_PARTY_LICENSES.txt"]' in pyproj
    assert "keywords = [" in pyproj
    assert '"desktop-app"' in pyproj
    assert '"local-first"' in pyproj
    assert '"Programming Language :: Python :: 3.13"' in pyproj


def test_ruff_configuration() -> None:
    '''Prüft die formale Ruff-Linter-Konfiguration.'''
    pyproj = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert "[tool.ruff]" in pyproj
    assert "line-length = 100" in pyproj
    assert 'target-version = "py310"' in pyproj
    assert "[tool.ruff.lint]" in pyproj


def test_gitignore_multihost_conflict_hardening() -> None:
    '''Prüft den Schutz gegen Multi-Host-Synchronisationskonflikte in .gitignore.'''
    gi = (ROOT / ".gitignore").read_text(encoding="utf-8")
    assert "*conflicted copy*" in gi
    assert "*-WORKSTATION*" in gi
    assert "*-ASUS*" in gi
    assert "* (kopie)*" in gi
    assert "*.orig" in gi


def test_notice_attribution_contract() -> None:
    '''Prüft die kanonische NOTICE-Attributionsdatei auf Urheber, Lizenz und Open-Bricks-Bezug.'''
    notice_file = ROOT / "NOTICE"
    assert notice_file.is_file(), "NOTICE-Datei fehlt im Repository-Root"
    notice = notice_file.read_text(encoding="utf-8")
    assert "DokuReader" in notice
    assert "Copyright (c) 2026 Lukas Geiger, doc-bricks Team" in notice
    assert "doc-bricks family under the open-bricks open-source umbrella" in notice
    assert "AGPL-3.0" in notice
    assert "THIRD_PARTY_LICENSES.md" in notice


def test_ci_timeout_and_concurrency_guardrails() -> None:
    '''Prüft, dass alle CI-Workflows Timeout-Guardrails und Concurrency-Schutz besitzen.'''
    stale = (ROOT / ".github/workflows/stale.yml").read_text(encoding="utf-8")
    assert "timeout-minutes: 10" in stale

    welcome = (ROOT / ".github/workflows/welcome.yml").read_text(encoding="utf-8")
    assert "timeout-minutes: 5" in welcome
    assert "concurrency:" in welcome
    assert "cancel-in-progress: true" in welcome

    smoke = (ROOT / ".github/workflows/source-platform-smoke.yml").read_text(encoding="utf-8")
    assert "timeout-minutes: 15" in smoke
    assert "concurrency:" in smoke
    assert "cancel-in-progress: true" in smoke

    ci = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    assert "timeout-minutes: 15" in ci
    assert "timeout-minutes: 10" in ci


def test_extended_lock_and_multihost_defense() -> None:
    '''Prüft Fail-Closed Canonical Lock System und erweiterte Multi-Host-Patterns in .gitignore.'''
    gi = (ROOT / ".gitignore").read_text(encoding="utf-8")
    for pattern in (
        "LOCK.user.*",
        "LOCK.until.*",
        "LOCK.condition.*",
        "LOCK.permissions.json",
        ".automation-lock",
        "*-WORKSTATION-LG*",
        "*-ASUS-GEI*",
        "*-LAPTOP*",
        "*-Mac Studio*",
        "*-MacBook*",
        "uv.lock",
        "!package-lock.json",
        ".hypothesis/",
        ".turbo/",
        ".tox/",
    ):
        assert pattern in gi, f"{pattern} fehlt in .gitignore"


def test_pyproject_pep621_hardening() -> None:
    '''Prüft PEP 621 Standardisierung, Versionsfreeze und Pytest-Norecursedirs in pyproject.toml.'''
    pyproj = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "1.0.1.dev0"' in pyproj, "Versionsnummer darf im Pfad A/B nicht geändert werden (T-20260920-167562623)"
    assert 'Notice = "https://github.com/doc-bricks/DokuReader/blob/master/NOTICE"' in pyproj
    assert 'norecursedirs = [".git", ".pytest_cache", "__pycache__", "build", "dist", ".venv"]' in pyproj


def test_third_party_licenses_audit_recency() -> None:
    '''Prüft Aktualität und NOTICE-Verlinkung im Drittanbieter-Lizenzinventar.'''
    tpl = (ROOT / "THIRD_PARTY_LICENSES.md").read_text(encoding="utf-8")
    assert "2026-09-25" in tpl or "2026-09-22" in tpl
    assert "[NOTICE](NOTICE)" in tpl
    for inv in (
        "INV-LOCAL-01",
        "INV-RUNAS-02",
        "INV-INPLACE-03",
        "INV-SCHEMA-04",
        "INV-ISOLATION-05",
        "INV-SANDBOX-06",
        "INV-PARITY-07",
        "INV-A11Y-08",
        "INV-DISCOVERY-09",
        "INV-SLA-10",
    ):
        assert inv in tpl, f"THIRD_PARTY_LICENSES.md fehlt Invariante {inv}"


def test_web_companion_badge_and_test_count_parity() -> None:
    '''Prüft, dass Web Companion Badges und llms.txt die 37 Node-Tests getrennt und konsistent abbilden.'''
    readme_en = (ROOT / "README.md").read_text(encoding="utf-8")
    readme_de = (ROOT / "README_de.md").read_text(encoding="utf-8")
    llms = (ROOT / "llms.txt").read_text(encoding="utf-8")

    assert "Web%20Companion-37%20passed-success" in readme_en
    assert "Web%20Companion-37%20passed-success" in readme_de
    assert "37 Node.js tests verified" in llms or "Web Companion 37 passed" in llms


def test_target_personas_and_seo_discoverability() -> None:
    '''Prüft das Vorhandensein der 4 Ziel-Personas und High-Intent Suchbegriffe.'''
    readme_en = (ROOT / "README.md").read_text(encoding="utf-8")
    readme_de = (ROOT / "README_de.md").read_text(encoding="utf-8")

    personas = ["[PERSONA-01]", "[PERSONA-02]", "[PERSONA-03]", "[PERSONA-04]"]
    for text, name in [(readme_en, "README.md"), (readme_de, "README_de.md")]:
        for p in personas:
            assert p in text, f"{name} fehlt Persona {p}"
        assert "offline local document organizer" in text.lower() or "lokale dokumentenverwaltung" in text.lower()
        assert "dokureader-library-v1.json" in text


def test_comparative_matrix_ten_dimensions_and_invariants() -> None:
    '''Prüft die 10-Dimensionen-Vergleichsmatrix und Zuordnung aller Invarianten INV-LOCAL-01 bis INV-SLA-10.'''
    readme_en = (ROOT / "README.md").read_text(encoding="utf-8")
    readme_de = (ROOT / "README_de.md").read_text(encoding="utf-8")

    invariants = [
        "INV-LOCAL-01",
        "INV-RUNAS-02",
        "INV-INPLACE-03",
        "INV-SCHEMA-04",
        "INV-ISOLATION-05",
        "INV-SANDBOX-06",
        "INV-PARITY-07",
        "INV-A11Y-08",
        "INV-DISCOVERY-09",
        "INV-SLA-10",
    ]
    for text, name in [(readme_en, "README.md"), (readme_de, "README_de.md")]:
        for inv in invariants:
            assert inv in text, f"{name} Vergleichsmatrix fehlt Invariante {inv}"
        assert "Calibre" in text
        assert "Zotero" in text
        assert "DEVONthink" in text


def test_statutory_bgb_disclaimer_and_48h_sla() -> None:
    '''Prüft den gesetzlichen Haftungsausschluss gem. § 521 BGB und das 48h Security Response SLA.'''
    readme_en = (ROOT / "README.md").read_text(encoding="utf-8")
    readme_de = (ROOT / "README_de.md").read_text(encoding="utf-8")

    for text, name in [(readme_en, "README.md"), (readme_de, "README_de.md")]:
        assert "§ 521 BGB" in text, f"{name} fehlt § 521 BGB Referenz"
        assert "Gefälligkeitsrecht" in text, f"{name} fehlt Gefälligkeitsrecht Hinweis"
        assert "48-hour response" in text.lower() or "48-stunden" in text.lower() or "48 stunden" in text.lower()
        assert "security@open-bricks.org" in text
