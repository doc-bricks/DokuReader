from __future__ import annotations

import argparse
import json
import re
import xml.etree.ElementTree as ET
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
    "StoreLogo.png": (50, 50),
    "Square150x150Logo.png": (150, 150),
    "Wide310x150Logo.png": (310, 150),
    "Square310x310Logo.png": (310, 310),
}

STORE_SCREENSHOTS = (
    "library-overview.png",
    "pdf-preview.png",
    "collection-export.png",
)
WACK_REPORT_PREFIX = "wack_"

TIER2_STORE_LANGUAGES = (
    "de-DE",
    "en-US",
    "es-ES",
    "zh-CN",
    "ja-JP",
    "ru-RU",
)

REQUIRED_DOCS = (
    "STORE_LISTING.md",
    "PRIVACY_POLICY.md",
    "SUPPORT.md",
    "LICENSE",
    "THIRD_PARTY_LICENSES.txt",
)

FORBIDDEN_LOCAL_PATH_RE = re.compile(
    r"(?:[A-Za-z]:[\\/](?:Users|_Local_DEV)[\\/]|/Users/|/home/)",
    re.IGNORECASE,
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

    if "languages" in data:
        langs = data.get("languages")
        if not isinstance(langs, list) or not all(isinstance(item, str) and item.strip() for item in langs):
            results.append(_result("Store Tier-2 languages", "BLOCKER", "languages must be a non-empty list of BCP-47 tags", path, root))
        else:
            missing_langs = [lang for lang in TIER2_STORE_LANGUAGES if lang not in langs]
            if missing_langs:
                results.append(
                    _result(
                        "Store Tier-2 languages",
                        "BLOCKER",
                        f"missing Tier-2 languages: {', '.join(missing_langs)}",
                        path,
                        root,
                    )
                )
            else:
                results.append(
                    _result(
                        "Store Tier-2 languages",
                        "OK",
                        f"{len(langs)} locales ({', '.join(langs)})",
                        path,
                        root,
                    )
                )

    if "listings" in data:
        listings = data.get("listings")
        if not isinstance(listings, dict):
            results.append(_result("Store Tier-2 listings", "BLOCKER", "listings must be an object keyed by locale", path, root))
        else:
            expected_locales = data.get("languages") if isinstance(data.get("languages"), list) else list(TIER2_STORE_LANGUAGES)
            problems: list[str] = []
            for locale in expected_locales:
                entry = listings.get(locale)
                if not isinstance(entry, dict):
                    problems.append(f"{locale}: missing listing object")
                    continue
                short_desc = str(entry.get("short_description", "")).strip()
                if not (1 <= len(short_desc) <= 100):
                    problems.append(f"{locale}: short_description length {len(short_desc)} (must be 1..100)")
                keywords = entry.get("keywords")
                if not isinstance(keywords, list) or not (1 <= len(keywords) <= 7):
                    problems.append(f"{locale}: keywords must contain 1..7 entries")
                else:
                    for kw in keywords:
                        kw_text = str(kw).strip()
                        if not (1 <= len(kw_text) <= 30):
                            problems.append(f"{locale}: keyword {kw_text!r} exceeds 30 chars or is empty")
                listing_rel = str(entry.get("listing_file", "")).strip()
                if not listing_rel:
                    problems.append(f"{locale}: missing listing_file")
                else:
                    listing_path = root / listing_rel
                    if not listing_path.is_file() or listing_path.stat().st_size == 0:
                        problems.append(f"{locale}: listing_file missing or empty ({listing_rel})")
            if problems:
                results.append(_result("Store Tier-2 listings", "BLOCKER", "; ".join(problems), path, root))
            else:
                results.append(
                    _result(
                        "Store Tier-2 listings",
                        "OK",
                        f"verified {len(expected_locales)} localized listings (short_description <=100, <=7 keywords <=30 chars)",
                        path,
                        root,
                    )
                )

    return results


def check_appx_manifest(root: Path) -> list[CheckResult]:
    manifest_path = root / "releases" / "windowsstore" / "AppxManifest.xml"
    if not manifest_path.exists():
        return []

    pkg_data, pkg_err = _read_json(root / "store_package.json")
    try:
        xml_root = ET.parse(manifest_path).getroot()
    except ET.ParseError as exc:
        return [_result("MSIX AppxManifest template", "BLOCKER", f"invalid XML: {exc}", manifest_path, root)]

    def _local(tag: str) -> str:
        return tag.rsplit("}", 1)[-1]

    identity = next((el for el in xml_root.iter() if _local(el.tag) == "Identity"), None)
    if identity is None:
        return [_result("MSIX AppxManifest template", "BLOCKER", "missing <Identity> element", manifest_path, root)]

    problems: list[str] = []
    if not pkg_err:
        for xml_attr, json_key in (
            ("Name", "identity_name"),
            ("Publisher", "publisher"),
            ("Version", "version"),
        ):
            expected = str(pkg_data.get(json_key, "")).strip()
            actual = str(identity.attrib.get(xml_attr, "")).strip()
            if expected and actual != expected:
                problems.append(f"Identity {xml_attr}={actual!r} != {expected!r}")

    arch = identity.attrib.get("ProcessorArchitecture", "")
    if arch not in {"x64", "arm64", "neutral"}:
        problems.append(f"unexpected ProcessorArchitecture={arch!r}")

    caps = [
        el.attrib.get("Name", "")
        for el in xml_root.iter()
        if _local(el.tag) == "Capability"
    ]
    if "runFullTrust" not in caps:
        problems.append("missing runFullTrust capability")

    manifest_langs = [
        el.attrib.get("Language", "")
        for el in xml_root.iter()
        if _local(el.tag) == "Resource" and el.attrib.get("Language")
    ]
    expected_langs = (
        [str(x) for x in pkg_data.get("languages", [])]
        if not pkg_err and isinstance(pkg_data.get("languages"), list)
        else []
    )
    missing_res = [lang for lang in expected_langs if lang not in manifest_langs]
    if missing_res:
        problems.append(f"missing <Resource Language>: {', '.join(missing_res)}")

    app_el = next((el for el in xml_root.iter() if _local(el.tag) == "Application"), None)
    expected_exe = str(pkg_data.get("executable", "DokuReader.exe")).strip() if not pkg_err else "DokuReader.exe"
    if app_el is None or app_el.attrib.get("Executable", "").strip() != expected_exe:
        problems.append(f"Application Executable must be {expected_exe!r}")

    logo_el = next((el for el in xml_root.iter() if _local(el.tag) == "Logo"), None)
    visual_el = next((el for el in xml_root.iter() if _local(el.tag) == "VisualElements"), None)
    default_tile_el = next((el for el in xml_root.iter() if _local(el.tag) == "DefaultTile"), None)

    expected_logos = {
        "Properties/Logo": (logo_el.text.strip() if logo_el is not None and logo_el.text else "", "StoreLogo.png"),
        "Square150x150Logo": (visual_el.attrib.get("Square150x150Logo", "") if visual_el is not None else "", "Square150x150Logo.png"),
        "Square44x44Logo": (visual_el.attrib.get("Square44x44Logo", "") if visual_el is not None else "", "Square44x44Logo.png"),
        "Wide310x150Logo": (default_tile_el.attrib.get("Wide310x150Logo", "") if default_tile_el is not None else "", "Wide310x150Logo.png"),
        "Square310x310Logo": (default_tile_el.attrib.get("Square310x310Logo", "") if default_tile_el is not None else "", "Square310x310Logo.png"),
    }
    for label, (declared_ref, asset_filename) in expected_logos.items():
        norm_ref = declared_ref.replace("/", "\\")
        valid_staging_refs = {f"icons\\{asset_filename}", f"store_assets\\{asset_filename}"}
        if norm_ref not in valid_staging_refs:
            problems.append(f"{label}={declared_ref!r} must use icons\\{asset_filename} or store_assets\\{asset_filename}")
        elif not (root / "store_assets" / asset_filename).is_file():
            problems.append(f"{label} source PNG missing: store_assets/{asset_filename}")

    if problems:
        return [_result("MSIX AppxManifest template", "BLOCKER", "; ".join(problems), manifest_path, root)]
    return [
        _result(
            "MSIX AppxManifest template",
            "OK",
            f"Identity {identity.attrib.get('Name')} {identity.attrib.get('Version')} ({arch}, {len(manifest_langs)} languages)",
            manifest_path,
            root,
        )
    ]


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

    leaked_keys = [
        key
        for key in ("output_dir", "pfx_path", "makeappx_path", "signtool_path")
        if FORBIDDEN_LOCAL_PATH_RE.search(str(data.get(key, "")))
    ]
    if leaked_keys:
        results.append(
            _result(
                "Packager path hygiene",
                "BLOCKER",
                f"non-portable developer paths in {', '.join(leaked_keys)}",
                path,
                root,
            )
        )
    else:
        results.append(_result("Packager path hygiene", "OK", "no machine-specific user/worktree paths", path, root))

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
        root / "dist" / "DokuReader" / "DokuReader.exe",
        root / "releases" / "v1.0.0" / "DokuReader-1.0.0-win64.exe",
    )
    msix_candidates = (
        root / "releases" / "windowsstore" / "DokuReader.msix",
        root / "releases" / "windowsstore" / "store_package" / "DokuReader.msix",
        root / "store_package" / "DokuReader.msix",
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
    return results


def _load_json_object(path: Path) -> tuple[dict, str | None]:
    data, error = _read_json(path)
    if error:
        return {}, error
    return data, None


def _latest_wack_summary(root: Path) -> Path | None:
    report_dirs = (
        root / "releases" / "windowsstore" / "test_reports",
        root / "releases" / "windowsstore",
    )
    summaries: list[Path] = []
    for directory in report_dirs:
        if directory.exists():
            summaries.extend(directory.glob(f"{WACK_REPORT_PREFIX}*.json"))
    summaries.sort(key=lambda path: (path.stat().st_mtime, path.name))
    return summaries[-1] if summaries else None


def _latest_wack_xml(root: Path) -> Path | None:
    report_dirs = (
        root / "releases" / "windowsstore" / "test_reports",
        root / "releases" / "windowsstore",
    )
    reports: list[Path] = []
    for directory in report_dirs:
        if directory.exists():
            reports.extend(directory.glob(f"{WACK_REPORT_PREFIX}*.xml"))
            reports.extend(directory.glob("*WACK*.xml"))
    reports.sort(key=lambda path: (path.stat().st_mtime, path.name))
    return reports[-1] if reports else None


def _int_from_json(value: object) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def check_wack_runner(root: Path) -> list[CheckResult]:
    path = root / "_WARTUNG" / "run_windows_wack.py"
    if path.exists() and path.stat().st_size > 0:
        return [_result("WACK runner", "OK", "runner present", path, root)]
    return [_result("WACK runner", "BLOCKER", "missing _WARTUNG/run_windows_wack.py", path, root)]


def check_wack_report(root: Path) -> list[CheckResult]:
    summary_path = _latest_wack_summary(root)
    if summary_path is None:
        xml_path = _latest_wack_xml(root)
        if xml_path is not None:
            return [
                _result(
                    "WACK JSON summary",
                    "BLOCKER",
                    "XML report exists but has not been parsed to JSON; run _WARTUNG/run_windows_wack.py --parse-report",
                    xml_path,
                    root,
                )
            ]
        return [
            _result(
                "WACK JSON summary",
                "BLOCKER",
                "no parsed WACK JSON summary found",
                root / "releases" / "windowsstore" / "test_reports",
                root,
            )
        ]

    payload, error = _load_json_object(summary_path)
    if error:
        return [_result("WACK JSON summary", "BLOCKER", f"unreadable summary: {error}", summary_path, root)]

    overall = str(payload.get("overall_result", "UNKNOWN")).upper()
    fail_count = _int_from_json(payload.get("fail_count"))
    pass_count = _int_from_json(payload.get("pass_count"))
    warning_count = _int_from_json(payload.get("warning_count"))
    requirement_count = _int_from_json(payload.get("requirement_count"))
    detail = (
        f"{overall}, {pass_count} PASS, {fail_count} FAIL, "
        f"{warning_count} WARNING, {requirement_count} requirements"
    )
    if fail_count > 0 or overall == "FAIL":
        return [_result("WACK JSON summary", "BLOCKER", detail, summary_path, root)]
    return [_result("WACK JSON summary", "OK", detail, summary_path, root)]


def run_checks(root: Path = PROJECT_ROOT) -> list[CheckResult]:
    root = root.resolve()
    results: list[CheckResult] = []
    results.extend(check_store_package(root))
    results.extend(check_appx_manifest(root))
    results.extend(check_packager_settings(root))
    results.extend(check_required_docs(root))
    results.extend(check_store_assets(root))
    results.extend(check_screenshots(root))
    results.extend(check_build_artifacts(root))
    results.extend(check_wack_runner(root))
    results.extend(check_wack_report(root))
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
