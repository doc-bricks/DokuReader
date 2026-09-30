"""Partial collection exports must disclose omissions in the final dialog."""

from types import SimpleNamespace
from unittest.mock import Mock

import pytest

import DokuReader as app


@pytest.fixture
def export_window(tmp_path, monkeypatch):
    pending = []
    window = SimpleNamespace(
        state_model=SimpleNamespace(list_docs=Mock()),
        _set_busy=Mock(), status_info=Mock(),
        _txt_to_pdf=Mock(return_value=None),
        _image_to_pdf=Mock(return_value=None),
        _office_to_pdf=Mock(return_value=None),
        _merge_pdfs=Mock(return_value=True),
        after=lambda delay, callback: pending.append(callback),
    )
    warning, success = Mock(), Mock()
    monkeypatch.setattr(app, "desktop_path", lambda: tmp_path)
    monkeypatch.setattr(app.messagebox, "showwarning", warning)
    monkeypatch.setattr(app.messagebox, "showinfo", success)
    return window, pending, warning, success


@pytest.mark.parametrize("suffix", [".txt", ".png", ".docx", ".unknown"])
def test_partial_export_lists_omitted_document(export_window, suffix):
    window, pending, warning, success = export_window
    missing = "prüfung" + suffix
    window.state_model.list_docs.return_value = [
        {"path": "included.pdf", "read": False}, {"path": missing, "read": True},
    ]
    app.App._create_collection_pdf_worker(window, "Bücher", "alle")
    warning.assert_not_called()
    for callback in pending:
        callback()
    warning.assert_called_once()
    title, message = warning.call_args.args
    assert "unvollständig" in title.lower()
    assert missing in message
    assert "1 von 2" in message
    success.assert_not_called()
    window._set_busy.assert_any_call(False)


def test_conversion_exception_reaches_partial_export_warning(export_window):
    window, pending, warning, success = export_window
    window.state_model.list_docs.return_value = [{"path": "included.pdf"}, {"path": "broken.txt"}]
    window._txt_to_pdf.side_effect = OSError("Datei nicht lesbar")
    app.App._create_collection_pdf_worker(window, "Topic", "alle")
    for callback in pending:
        callback()
    warning.assert_called_once()
    assert "broken.txt" in warning.call_args.args[1]
    assert "Datei nicht lesbar" in warning.call_args.args[1]
    success.assert_not_called()


def test_all_conversions_failed_reports_sources_and_does_not_merge(export_window):
    window, _, _, success = export_window
    window.state_model.list_docs.return_value = [{"path": "failed.txt"}, {"path": "failed.docx"}]
    app.App._create_collection_pdf_worker(window, "Topic", "alle")
    window._merge_pdfs.assert_not_called()
    message = window.status_info.call_args.args[0]
    assert "failed.txt" in message and "failed.docx" in message
    success.assert_not_called()
    window._set_busy.assert_any_call(False)


def test_filter_excludes_documents_without_reporting_them_as_omissions(export_window):
    window, pending, warning, success = export_window
    window.state_model.list_docs.return_value = [
        {"path": "included.pdf", "read": True}, {"path": "excluded.txt", "read": False},
    ]
    app.App._create_collection_pdf_worker(window, "Topic", "gelesene")
    for callback in pending:
        callback()
    warning.assert_not_called()
    success.assert_called_once()
    assert "excluded.txt" not in success.call_args.args[1]
    window._txt_to_pdf.assert_not_called()


def test_merge_failure_retains_conversion_details_without_success(export_window):
    window, pending, warning, success = export_window
    window.state_model.list_docs.return_value = [{"path": "included.pdf"}, {"path": "failed.txt"}]
    window._merge_pdfs.return_value = False
    app.App._create_collection_pdf_worker(window, "Topic", "alle")
    for callback in pending:
        callback()
    assert "failed.txt" in window.status_info.call_args.args[0]
    warning.assert_not_called()
    success.assert_not_called()
