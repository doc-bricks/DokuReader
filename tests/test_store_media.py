from __future__ import annotations

import importlib.util
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = PROJECT_ROOT / "_WARTUNG" / "generate_store_media.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("dokureader_store_media", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_create_demo_library_creates_expected_files(tmp_path):
    module = _load_module()

    topics = module.create_demo_library(tmp_path / "demo_docs")

    assert sorted(topics.keys()) == ["Forschung", "Verwaltung"]
    pdf_path = Path(topics["Forschung"][0]["path"])
    txt_path = Path(topics["Forschung"][1]["path"])
    image_path = Path(topics["Verwaltung"][0]["path"])
    missing_path = Path(topics["Forschung"][2]["path"])

    assert pdf_path.exists()
    assert txt_path.exists()
    assert image_path.exists()
    assert not missing_path.exists()


def test_write_screenshot_manifest_lists_all_entries(tmp_path):
    module = _load_module()

    module.write_screenshot_manifest(tmp_path)

    content = (tmp_path / "README.md").read_text(encoding="utf-8")
    for filename, caption in module.SCREENSHOTS:
        assert filename in content
        assert caption in content


def test_write_asset_manifest_lists_all_expected_assets(tmp_path):
    module = _load_module()

    module.write_asset_manifest(tmp_path)

    content = (tmp_path / "README.md").read_text(encoding="utf-8")
    for filename, size in module.STORE_ASSETS.items():
        assert filename in content
        assert f"{size[0]}x{size[1]}" in content
