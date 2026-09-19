"""Readback contract for version roles and release-boundary documentation."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_version_roles_and_release_surfaces_are_explicit() -> None:
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    runtime = (ROOT / "DokuReader.py").read_text(encoding="utf-8")
    package = json.loads((ROOT / "store_package.json").read_text(encoding="utf-8"))
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    readme_de = (ROOT / "README_de.md").read_text(encoding="utf-8")
    status = (ROOT / "RELEASE_STATUS.md").read_text(encoding="utf-8")
    plan = (ROOT / "PORTIERUNGSPLAN.md").read_text(encoding="utf-8")
    build_script = (ROOT / "build_exe.bat").read_text(encoding="utf-8")

    assert 'version = "1.0.1.dev0"' in pyproject
    assert 'requires-python = ">=3.10"' in pyproject
    assert 'Development Status :: 4 - Beta' in pyproject
    assert re.search(r'^APP_VERSION\s*=\s*"1\.0\.1-dev"$', runtime, re.MULTILINE)
    assert package["version"] == "1.0.1.0"
    for surface in (readme, readme_de):
        assert "1.0.1--dev" in surface
        assert "Version-v1.0.0" not in surface
        assert "kein" in surface.lower() or "no verified public release" in surface.lower()
    assert "Öffentliches Release" in status and "keines belegt" in status
    assert "signiertes MSIX" in status and "WACK" in status
    assert "Releaseversion: keine" in plan
    assert "DOKUREADER_BUILD_ROOT" in build_script
    assert "C:\\_Local_DEV" not in build_script
