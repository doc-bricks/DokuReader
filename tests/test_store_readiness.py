from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

from PIL import Image


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = PROJECT_ROOT / "_WARTUNG" / "check_store_readiness.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("dokureader_store_readiness", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _write_png(path: Path, size: tuple[int, int]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGBA", size, (245, 248, 252, 255)).save(path, "PNG")


def _create_store_ready_fixture(root: Path) -> None:
    (root / "store_package.json").write_text(
        json.dumps(
            {
                "app_name": "DokuReader",
                "publisher": "CN=52596601-BAB4-4F3F-B182-E8F3F273B202",
                "publisher_display": "Geiger",
                "identity_name": "Geiger.DokuReader",
                "version": "1.0.1.0",
                "description": "Local document library.",
                "privacy_url": "https://github.com/doc-bricks/DokuReader/blob/master/README.md#privacy-and-local-data",
                "support_url": "https://github.com/doc-bricks/DokuReader/issues",
            }
        ),
        encoding="utf-8",
    )
    for name in ("STORE_LISTING.md", "PRIVACY_POLICY.md", "SUPPORT.md", "LICENSE", "THIRD_PARTY_LICENSES.txt"):
        (root / name).write_text(f"# {name}\n", encoding="utf-8")
    (root / "_WARTUNG").mkdir(parents=True, exist_ok=True)
    (root / "_WARTUNG" / "run_windows_wack.py").write_text("# WACK runner fixture\n", encoding="utf-8")

    module = _load_module()
    for filename, size in module.STORE_ASSETS.items():
        _write_png(root / "store_assets" / filename, size)
    for filename in module.STORE_SCREENSHOTS:
        _write_png(root / "releases" / "windowsstore" / "screenshots" / filename, (1366, 768))
    _write_png(root / "README" / "screenshots" / "main.png", (1366, 768))

    (root / "releases" / "v1.0.0").mkdir(parents=True, exist_ok=True)
    (root / "releases" / "v1.0.0" / "DokuReader-1.0.0-win64.exe").write_bytes(b"MZ")
    settings_dir = root / "releases" / "windowsstore"
    settings_dir.mkdir(parents=True, exist_ok=True)
    (settings_dir / "store_settings.json").write_text(
        json.dumps({"publisher": "CN=52596601-BAB4-4F3F-B182-E8F3F273B202", "pfx_password": ""}),
        encoding="utf-8",
    )


def _by_name(results):
    return {result.name: result for result in results}


def test_store_readiness_reports_external_msix_and_wack_blockers(tmp_path):
    module = _load_module()
    _create_store_ready_fixture(tmp_path)

    results = _by_name(module.run_checks(tmp_path))

    assert results["Store metadata"].status == "OK"
    assert results["MSIX package"].status == "BLOCKER"
    assert results["WACK runner"].status == "OK"
    assert results["WACK JSON summary"].status == "BLOCKER"


def test_store_readiness_flags_unfilled_packager_publisher(tmp_path):
    module = _load_module()
    _create_store_ready_fixture(tmp_path)
    settings_path = tmp_path / "releases" / "windowsstore" / "store_settings.json"
    settings_path.write_text(json.dumps({"publisher": "", "pfx_password": ""}), encoding="utf-8")

    results = _by_name(module.run_checks(tmp_path))

    assert results["WinStorePackager publisher"].status == "BLOCKER"


def test_store_readiness_passes_when_msix_and_wack_are_present(tmp_path):
    module = _load_module()
    _create_store_ready_fixture(tmp_path)
    (tmp_path / "releases" / "windowsstore" / "DokuReader.msix").write_bytes(b"PK")
    report_dir = tmp_path / "releases" / "windowsstore" / "test_reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "wack_20260702.json").write_text(
        json.dumps(
            {
                "overall_result": "PASS",
                "requirement_count": 2,
                "pass_count": 2,
                "fail_count": 0,
                "warning_count": 0,
            }
        ),
        encoding="utf-8",
    )

    results = module.run_checks(tmp_path)
    summary = module.summarize(results)

    assert summary["BLOCKER"] == 0


def test_store_readiness_blocks_failed_wack_summary(tmp_path):
    module = _load_module()
    _create_store_ready_fixture(tmp_path)
    (tmp_path / "releases" / "windowsstore" / "DokuReader.msix").write_bytes(b"PK")
    report_dir = tmp_path / "releases" / "windowsstore" / "test_reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "wack_20260702.json").write_text(
        json.dumps(
            {
                "overall_result": "FAIL",
                "requirement_count": 2,
                "pass_count": 1,
                "fail_count": 1,
                "warning_count": 0,
            }
        ),
        encoding="utf-8",
    )

    results = _by_name(module.run_checks(tmp_path))

    assert results["WACK JSON summary"].status == "BLOCKER"
