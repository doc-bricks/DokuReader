from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

try:
    from PIL import Image
except Exception:  # pragma: no cover - exercised only on minimal Python installs
    Image = None


PROJECT_ROOT = Path(__file__).resolve().parents[1]

STORE_ASSETS = {
    "Square44x44Logo.png": (44, 44),
    "Square150x150Logo.png": (150, 150),
    "Wide310x150Logo.png": (310, 150),
    "Square310x310Logo.png": (310, 310),
}

STORE_SCREENSHOTS = (
    "library-overview.png",
    "pdf-preview.png",
    "collection-export.png",
)

REQUIRED_DOCS = (
    "STORE_LISTING.md",
    "PRIVACY_POLICY.md",
    "SUPPORT.md",
    "LICENSE",
    "THIRD_PARTY_LICENSES.txt",
)


@dataclass(frozen=True)
class CheckResult:
    name: str
    status: str
    detail: str
    path: str | None = None


def _rel(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _result(name: str, status: str, detail: str, path: Path | None = None, root: Path | None = None) -> CheckResult:
    return CheckResult(name=name, status=status, detail=detail, path=_rel(path, root or PROJECT_ROOT) if path else None)


def _read_json(path: Path) -> tuple[dict, str | None]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}, "missing"
    except json.JSONDecodeError as exc:
        return {}, f"invalid JSON: {exc}"
    if not isinstance(data, dict):
        return {}, "JSON root is not an object"
    return data, None


def _valid_url(value: object) -> bool:
    return isinstance(value, str) and bool(re.match(r"^https://[^\s]+$", value))


def check_store_package(root: Path) -> list[CheckResult]:
    path = root / "store_package.json"
    data, error = _read_json(path)
    if error:
        return [_result("Store metadata", "BLOCKER", error, path, root)]

    required = ("app_name", "publisher", "identity_name", "version", "privacy_url", "support_url", "description")
    missing = [key for key in required if not str(data.get(key, "")).strip()]
    results: list[CheckResult] = []
    if missing:
        results.append(_result("Store metadata", "BLOCKER", f"missing fields: {', '.join(missing)}", path, root))
    else:
        results.append(_result("Store metadata", "OK", "required fields present", path, root))

    for key in ("privacy_url", "support_url"):
        value = data.get(key)
        if _valid_url(value):
            results.append(_result(f"{key}", "OK", str(value), path, root))
        else:
            results.append(_result(f"{key}", "BLOCKER", "must be a public https URL", path, root))

    return results


def check_packager_settings(root: Path) -> list[CheckResult]:
    path = root / "releases" / "windowsstore" / "store_settings.json"
    if not path.exists():
        return [_result("WinStorePackager settings", "WARN", "local store_settings.json is not generated yet", path, root)]

    data, error = _read_json(path)
    if error:
        return [_result("WinStorePackager settings", "BLOCKER", error, path, root)]

    results: list[CheckResult] = []
    if str(data.get("publisher", "")).strip():
        results.append(_result("WinStorePackager publisher", "OK", "publisher field is filled", path, root))
    else:
        results.append(_result("WinStorePackager publisher", "BLOCKER", "publisher must be filled before MSIX signing", path, root))

    password = str(data.get("pfx_password", "")).strip()
    if password:
        results.append(_result("Signing password", "BLOCKER", "pfx_password must not be stored in project files", path, root))
    else:
        results.append(_result("Signing password", "OK", "no signing password stored", path, root))

    return results


def check_required_docs(root: Path) -> list[CheckResult]:
    results: list[CheckResult] = []
    for relative in REQUIRED_DOCS:
        path = root / relative
        if path.exists() and path.stat().st_size > 0:
            results.append(_result(f"Document {relative}", "OK", "present", path, root))
        else:
            results.append(_result(f"Document {relative}", "BLOCKER", "missing or empty", path, root))
    return results


def _check_png_size(path: Path, expected: tuple[int, int], root: Path) -> CheckResult:
    if not path.exists():
        return _result(f"Asset {path.name}", "BLOCKER", f"missing {expected[0]}x{expected[1]} PNG", path, root)
    if Image is None:
        return _result(f"Asset {path.name}", "WARN", "present; Pillow unavailable, size not verified", path, root)
    try:
        with Image.open(path) as image:
            size = image.size
    except OSError as exc:
        return _result(f"Asset {path.name}", "BLOCKER", f"not a readable PNG: {exc}", path, root)
    if size == expected:
        return _result(f"Asset {path.name}", "OK", f"{size[0]}x{size[1]}", path, root)
    return _result(f"Asset {path.name}", "BLOCKER", f"expected {expected[0]}x{expected[1]}, got {size[0]}x{size[1]}", path, root)


def check_store_assets(root: Path) -> list[CheckResult]:
    asset_dir = root / "store_assets"
    return [_check_png_size(asset_dir / filename, size, root) for filename, size in STORE_ASSETS.items()]


def check_screenshots(root: Path) -> list[CheckResult]:
    screenshot_dir = root / "releases" / "windowsstore" / "screenshots"
    results: list[CheckResult] = []
    for filename in STORE_SCREENSHOTS:
        path = screenshot_dir / filename
        if path.exists() and path.stat().st_size > 0:
            results.append(_result(f"Screenshot {filename}", "OK", "present", path, root))
        else:
            results.append(_result(f"Screenshot {filename}", "BLOCKER", "missing generated Store screenshot", path, root))

    readme_shot = root / "README" / "screenshots" / "main.png"
    if readme_shot.exists() and readme_shot.stat().st_size > 0:
        results.append(_result("README screenshot", "OK", "present", readme_shot, root))
    else:
        results.append(_result("README screenshot", "BLOCKER", "missing README/screenshots/main.png", readme_shot, root))
    return results


def _first_existing(paths: Iterable[Path]) -> Path | None:
    return next((path for path in paths if path.exists() and path.stat().st_size > 0), None)


def check_build_artifacts(root: Path) -> list[CheckResult]:
    exe_candidates = (
        root / "dist" / "DokuReader.exe",
        root / "releases" / "v1.0.0" / "DokuReader-1.0.0-win64.exe",
    )
    msix_candidates = (
        root / "releases" / "windowsstore" / "DokuReader.msix",
        root / "releases" / "windowsstore" / "store_package" / "DokuReader.msix",
        root / "store_package" / "DokuReader.msix",
    )
    wack_reports = sorted((root / "releases" / "windowsstore").glob("*wack*.xml")) + sorted(
        (root / "releases" / "windowsstore").glob("*WACK*.xml")
    )

    results: list[CheckResult] = []
    exe = _first_existing(exe_candidates)
    if exe:
        results.append(_result("Windows EXE", "OK", "build artifact present", exe, root))
    else:
        results.append(_result("Windows EXE", "BLOCKER", "no dist or release EXE found", exe_candidates[0], root))

    msix = _first_existing(msix_candidates)
    if msix:
        results.append(_result("MSIX package", "OK", "package artifact present", msix, root))
    else:
        results.append(_result("MSIX package", "BLOCKER", "no signed MSIX package found", msix_candidates[0], root))

    wack = _first_existing(wack_reports)
    if wack:
        results.append(_result("WACK XML report", "OK", "report present", wack, root))
    else:
        results.append(_result("WACK XML report", "BLOCKER", "no WACK XML report found", root / "releases" / "windowsstore", root))
    return results


def run_checks(root: Path = PROJECT_ROOT) -> list[CheckResult]:
    root = root.resolve()
    results: list[CheckResult] = []
    results.extend(check_store_package(root))
    results.extend(check_packager_settings(root))
    results.extend(check_required_docs(root))
    results.extend(check_store_assets(root))
    results.extend(check_screenshots(root))
    results.extend(check_build_artifacts(root))
    return results


def summarize(results: Iterable[CheckResult]) -> dict[str, int]:
    counts = {"OK": 0, "WARN": 0, "BLOCKER": 0}
    for result in results:
        counts[result.status] = counts.get(result.status, 0) + 1
    return counts


def _print_text(results: list[CheckResult]) -> None:
    counts = summarize(results)
    print("DokuReader Windows Store readiness")
    print(f"Summary: {counts['OK']} OK / {counts['WARN']} WARN / {counts['BLOCKER']} BLOCKER")
    for result in results:
        location = f" ({result.path})" if result.path else ""
        print(f"[{result.status}] {result.name}: {result.detail}{location}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check DokuReader Windows Store readiness inputs.")
    parser.add_argument("--project-root", type=Path, default=PROJECT_ROOT)
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON")
    parser.add_argument("--allow-blockers", action="store_true", help="return success even when external Store blockers remain")
    args = parser.parse_args(argv)

    results = run_checks(args.project_root)
    counts = summarize(results)
    if args.json:
        print(json.dumps({"summary": counts, "checks": [asdict(result) for result in results]}, ensure_ascii=False, indent=2))
    else:
        _print_text(results)
    return 0 if args.allow_blockers or counts["BLOCKER"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
