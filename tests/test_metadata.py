"""Automated metadata, manifest, documentation, and security parity tests for DokuReader."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_pyproject_metadata() -> None:
    content = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'name = "dokureader"' in content
    assert 'version = "1.0.1.dev0"' in content
    assert 'requires-python = ">=3.10"' in content
    assert "https://github.com/doc-bricks/DokuReader" in content
    assert 'license = { text = "AGPL-3.0" }' in content


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

    assert "License-AGPL--3.0-green" in readme_de
    assert "Version-1.0.1--dev-blue" in readme_de
    assert "Python-3.10%2B-blue" in readme_de
    assert "Platform-Windows" in readme_de
    assert "LLM--Ready-llms.txt-success" in readme_de
    assert "doc--bricks-purple" in readme_de
    assert "open--bricks-blue" in readme_de

    for readme in (readme_en, readme_de):
        assert "https://github.com/doc-bricks/LitZentrum" in readme
        assert "https://github.com/doc-bricks/CleanMarkdown" in readme
        assert "https://github.com/doc-bricks/UniversalDocsGrabber" in readme
        assert "https://github.com/open-bricks" in readme


def test_test_badges_report_each_suite_separately() -> None:
    """Ein Testbadge darf zwei Suiten nicht zu einer Zahl verschmelzen.

    Bis 2026-08-24 trugen beide READMEs ``Tests-70%20passed``. Die 70 war die
    Summe aus 38 Pytest- und 32 Node-Tests -- und behauptete dabei etwas
    Falsches, denn von den 38 waren 37 bestanden und einer uebersprungen. Die
    Aggregation verschluckte den Skip und machte die Suiten ununterscheidbar.

    Geprueft wird deshalb die Struktur, nicht die Zahl: Sonst zementiert der
    Test den naechsten Stand genauso, wie er den letzten zementiert hat, und
    bricht bei jedem Testzuwachs erneut.
    """
    for name in ("README.md", "README_de.md"):
        readme = (ROOT / name).read_text(encoding="utf-8")
        assert "Pytest-" in readme, f"{name}: kein eigenes Pytest-Badge"
        assert "Web%20Companion-" in readme, f"{name}: kein eigenes Node-Badge"
        assert "Tests-" not in readme, (
            f"{name}: summierendes 'Tests-...'-Badge ist zurueck -- Suiten "
            f"werden getrennt ausgewiesen, nicht addiert"
        )


def test_llms_txt_currency_and_key_files() -> None:
    llms = (ROOT / "llms.txt").read_text(encoding="utf-8")
    # Ein fest verdrahtetes Datum prueft nicht Aktualitaet, sondern nur, ob
    # jemand genau dieses Datum stehen liess -- und bricht bei jeder Pflege.
    # Statisch pruefbar ist die Form, nicht die Frische.
    assert re.search(r"^## Last-checked: \d{4}-\d{2}-\d{2}$", llms, re.MULTILINE), (
        "llms.txt braucht einen Kopf '## Last-checked: YYYY-MM-DD'"
    )
    assert "https://github.com/doc-bricks/DokuReader" in llms
    assert "AGPL-3.0" in llms
    # Suiten getrennt, nicht summiert (siehe test_test_badges_report_each_suite_separately).
    assert "counted separately" in llms
    assert "Web Companion 32 passed" in llms
    assert "test_metadata.py" in llms


def test_security_policy_bilingual_and_invariants() -> None:
    sec = (ROOT / "SECURITY.md").read_text(encoding="utf-8")
    assert "## Deutsch" in sec
    assert "## English" in sec
    assert "security@ellmos.ai" in sec
    assert "Local-First" in sec or "lokal" in sec.lower()
    assert "Zero-Egress" in sec or "Netzwerk" in sec or "offline" in sec.lower()
    assert "Non-Elevation" in sec or "Administrator" in sec or "user mode" in sec.lower()


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
    assert "Discoverability" in changelog or "Sichtbarkeit" in changelog
