"""Failed JSON exports must retain existing files and never announce success."""

import io
import json
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

import DokuReader as app


@pytest.fixture
def export_file(tmp_path):
    path = tmp_path / "export.json"
    path.write_bytes(b"previous export")
    return path


def test_partial_write_preserves_existing_export(export_file, monkeypatch):
    real_open, real_fdopen = io.open, app.os.fdopen

    class FailingWriter:
        def __init__(self, stream):
            self.stream = stream

        def __enter__(self):
            return self

        def __exit__(self, *args):
            self.stream.close()

        def write(self, content):
            self.stream.write(content[:5])
            raise OSError("disk full")

    def fail_open(file, mode="r", *args, **kwargs):
        stream = real_open(file, mode, *args, **kwargs)
        return FailingWriter(stream) if "w" in mode and not isinstance(file, int) else stream

    monkeypatch.setattr(io, "open", fail_open)
    monkeypatch.setattr(app.os, "fdopen", lambda *a, **kw: FailingWriter(real_fdopen(*a, **kw)))
    with pytest.raises(OSError):
        app.write_library_export(export_file, {"topics": []})
    assert export_file.read_bytes() == b"previous export"
    assert list(export_file.parent.iterdir()) == [export_file]


def test_invalid_utf8_preserves_existing_export(export_file):
    with pytest.raises(UnicodeError):
        app.write_library_export(export_file, {"topic": "\ud800"})
    assert export_file.read_bytes() == b"previous export"
    assert list(export_file.parent.iterdir()) == [export_file]


def test_failed_replace_preserves_export_and_foreign_temp(export_file, monkeypatch):
    foreign = export_file.parent / ".dokureader-export-foreign.tmp"
    foreign.write_bytes(b"foreign work")

    def fail_replace(*args):
        raise PermissionError("locked destination")

    monkeypatch.setattr(app.os, "replace", fail_replace)
    with pytest.raises(PermissionError):
        app.write_library_export(export_file, {"topics": []})
    assert export_file.read_bytes() == b"previous export"
    assert foreign.read_bytes() == b"foreign work"
    assert set(export_file.parent.iterdir()) == {export_file, foreign}


@pytest.mark.parametrize("error_type", [OSError, ValueError, TypeError])
@pytest.mark.parametrize("stage", ["build_library_export_payload", "write_library_export"])
def test_dialog_reports_failures_without_success(export_file, monkeypatch, stage, error_type):
    window = SimpleNamespace(state_model=app.State())
    monkeypatch.setattr(app.filedialog, "asksaveasfilename", lambda **kw: str(export_file))
    monkeypatch.setattr(app, stage, Mock(side_effect=error_type("export failed")))
    showerror, showinfo = Mock(), Mock()
    monkeypatch.setattr(app.messagebox, "showerror", showerror)
    monkeypatch.setattr(app.messagebox, "showinfo", showinfo)
    app.App.export_library_json(window)
    showerror.assert_called_once()
    showinfo.assert_not_called()
    assert export_file.read_bytes() == b"previous export"


def test_success_preserves_utf8_schema_and_final_newline(export_file):
    payload = app.build_library_export_payload({"Bücher": [{"path": "prüfung.txt", "read": True}]}, "Bücher")
    app.write_library_export(export_file, payload)
    text = export_file.read_text(encoding="utf-8")
    assert text.endswith("\n")
    assert "Bücher" in text and "prüfung.txt" in text
    assert json.loads(text) == payload
    assert list(export_file.parent.iterdir()) == [export_file]
