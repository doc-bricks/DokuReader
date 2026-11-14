"""Regressionstests — Bugsweep DokuReader 2026-11-14."""

from types import SimpleNamespace
from unittest.mock import Mock

from pypdf import PdfReader, PdfWriter

import DokuReader as app


def write_pdf(path, width, password=None):
    writer = PdfWriter()
    writer.add_blank_page(width=width, height=200)
    if password:
        writer.encrypt(user_password=password, owner_password=password)
    with path.open("wb") as stream:
        writer.write(stream)
    writer.close()


def test_protected_pdf_is_skipped_instead_of_failing_the_whole_collection(tmp_path, monkeypatch):
    """Eine einzige passwortgeschützte PDF ließ das ganze Sammel-PDF scheitern (ohne Hinweis, welche)."""
    normal = tmp_path / "normal.pdf"
    protected = tmp_path / "geschuetzt.pdf"
    broken = tmp_path / "kaputt.pdf"
    write_pdf(normal, 111)
    write_pdf(protected, 222, password="geheim")
    broken.write_bytes(b"%PDF-1.4 kein echtes PDF")
    state = app.State()
    state.topics = {"Topic": [{"path": str(p), "read": False} for p in (normal, protected, broken)]}
    monkeypatch.setattr(app, "desktop_path", lambda: tmp_path)
    warning = Mock()
    monkeypatch.setattr(app.messagebox, "showwarning", warning)
    status = Mock()
    window = SimpleNamespace(
        state_model=state, _set_busy=Mock(), status_info=status,
        _merge_pdfs=lambda parts, output, **kwargs: app.App._merge_pdfs(None, parts, output, **kwargs),
        after=lambda delay, callback: callback(),
    )

    app.App._create_collection_pdf_worker(window, "Topic", "alle")

    status.assert_not_called()  # kein „Konnte Sammel-PDF nicht vollständig erstellen“
    with (tmp_path / "Topic_alle.pdf").open("rb") as stream:
        widths = [float(page.mediabox.width) for page in PdfReader(stream).pages]
    assert widths == [111]
    message = warning.call_args.args[1]
    assert "Enthalten: 1 von 3" in message
    assert str(protected) in message and str(broken) in message
    assert "Passwortgeschützt" in message


def test_pdf_part_problem_names_the_reason(tmp_path):
    normal = tmp_path / "ok.pdf"
    protected = tmp_path / "pw.pdf"
    write_pdf(normal, 100)
    write_pdf(protected, 100, password="x")
    assert app.pdf_part_problem(str(normal)) is None
    assert "Passwortgeschützt" in app.pdf_part_problem(str(protected))
    assert app.pdf_part_problem(str(tmp_path / "verschoben.pdf")) == "Datei fehlt"
