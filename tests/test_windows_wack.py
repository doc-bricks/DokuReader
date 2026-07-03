from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = PROJECT_ROOT / "_WARTUNG" / "run_windows_wack.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("dokureader_windows_wack", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _write_store_config(root: Path) -> None:
    (root / "store_package.json").write_text(
        json.dumps({"app_name": "DokuReader", "version": "1.0.1.0"}),
        encoding="utf-8",
    )


def test_dry_run_reports_msix_and_report_paths(tmp_path, capsys):
    module = _load_module()
    _write_store_config(tmp_path)

    exit_code = module.main(["--project-root", str(tmp_path), "--dry-run"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "DokuReader.msix" in output
    assert "WACK-Report:" in output


def test_parse_wack_report_counts_requirement_results(tmp_path):
    module = _load_module()
    report = tmp_path / "wack_20260703.xml"
    report.write_text(
        """
        <REPORT>
          <OVERALL_RESULT>PASS</OVERALL_RESULT>
          <REQUIREMENT><OVERALL_RESULT>PASS</OVERALL_RESULT></REQUIREMENT>
          <REQUIREMENT><OVERALL_RESULT>WARNING</OVERALL_RESULT></REQUIREMENT>
        </REPORT>
        """,
        encoding="utf-8",
    )

    summary = module.parse_wack_report(report)

    assert summary.overall_result == "PASS"
    assert summary.requirement_count == 2
    assert summary.pass_count == 1
    assert summary.warning_count == 1
    assert summary.fail_count == 0


def test_parse_report_main_writes_json_and_fails_on_failed_report(tmp_path, capsys):
    module = _load_module()
    report = tmp_path / "wack_20260703.xml"
    report.write_text(
        """
        <REPORT>
          <OVERALL_RESULT>FAIL</OVERALL_RESULT>
          <TEST Result="PASS" />
          <TEST Result="FAIL" />
        </REPORT>
        """,
        encoding="utf-8",
    )

    exit_code = module.main(["--parse-report", str(report)])
    payload = json.loads(report.with_suffix(".json").read_text(encoding="utf-8"))

    assert exit_code == 1
    assert payload["overall_result"] == "FAIL"
    assert payload["pass_count"] == 1
    assert payload["fail_count"] == 1
    assert "WACK-Zusammenfassung" in capsys.readouterr().out
