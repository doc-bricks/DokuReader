"""Library registration and final PDF publication share one protection boundary."""
import json
import threading
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from pypdf import PdfReader, PdfWriter

import DokuReader as app


def write_pdf(path, width):
    with PdfWriter() as writer:
        writer.add_blank_page(width=width, height=200)
        writer.write(path)


@pytest.fixture
def publication(tmp_path):
    source, destination = tmp_path / "source.pdf", tmp_path / "Topic_alle.pdf"
    write_pdf(source, 202)
    write_pdf(destination, 101)
    state = app.State()
    state.add_docs("Topic", [str(source)])
    window = SimpleNamespace(state_model=state)
    return window, source, destination


@pytest.mark.parametrize("alias", ["direct", "hardlink", "normalized"])
def test_registration_during_serialization_preserves_original(publication, monkeypatch, alias):
    window, source, destination = publication
    before = destination.read_bytes()
    reference = destination
    if alias == "hardlink":
        reference = destination.with_name("alias.pdf")
        app.os.link(destination, reference)
    elif alias == "normalized":
        folder = destination.parent / "nested"
        folder.mkdir()
        reference = folder / ".." / destination.name
    writer = PdfWriter()
    original_write = writer.write

    def late_registration(stream):
        original_write(stream)
        assert window.state_model.add_docs("Other", [str(reference)]) == 1

    monkeypatch.setattr(writer, "write", late_registration)
    monkeypatch.setattr(app, "_PdfWriter", lambda: writer)
    assert app.App._merge_pdfs(window, [str(source)], destination) is False
    assert destination.read_bytes() == before
    assert reference.read_bytes() == before
    assert not list(destination.parent.glob(".dokureader-pdf-*.tmp"))


def test_missing_reference_loaded_before_publication_is_protected(publication, monkeypatch):
    window, source, destination = publication
    destination.unlink()
    state_file = destination.parent / "state.json"
    state_file.write_text(json.dumps({"topics": {"Other": [
        {"path": str(destination), "read": False},
    ]}, "current_topic": "Other"}), encoding="utf-8")
    monkeypatch.setattr(app, "STATE_FILE", str(state_file))
    writer = PdfWriter()
    original_write = writer.write

    def load_new_library(stream):
        original_write(stream)
        window.state_model.load()

    monkeypatch.setattr(writer, "write", load_new_library)
    monkeypatch.setattr(app, "_PdfWriter", lambda: writer)
    assert app.App._merge_pdfs(window, [str(source)], destination) is False
    assert not destination.exists()
    assert not list(destination.parent.glob(".dokureader-pdf-*.tmp"))


def test_worker_reports_late_conflict_and_retry_uses_safe_name(publication, monkeypatch):
    window, _, destination = publication
    before = destination.read_bytes()
    entered, release = threading.Event(), threading.Event()
    pending = []
    window._set_busy = Mock()
    window.status_info = Mock()
    window.after = lambda _delay, callback: pending.append(callback)
    monkeypatch.setattr(app, "desktop_path", lambda: destination.parent)
    success = Mock()
    monkeypatch.setattr(app.messagebox, "showinfo", success)

    def merge(parts, output, **kwargs):
        entered.set()
        assert release.wait(3)
        return app.App._merge_pdfs(window, parts, output, **kwargs)

    window._merge_pdfs = merge
    worker = threading.Thread(target=app.App._create_collection_pdf_worker,
                              args=(window, "Topic", "alle"))
    worker.start()
    try:
        assert entered.wait(3)
        window.state_model.add_docs("Other", [str(destination)])
    finally:
        release.set()
        worker.join(4)
    assert not worker.is_alive()
    for callback in pending:
        callback()
    assert destination.read_bytes() == before
    success.assert_not_called()
    assert "Original" in window.status_info.call_args.args[0]
    pending.clear()
    window._merge_pdfs = lambda parts, output, **kwargs: app.App._merge_pdfs(window, parts, output, **kwargs)
    app.App._create_collection_pdf_worker(window, "Topic", "alle")
    for callback in pending:
        callback()
    output = destination.with_name("Topic_alle (1).pdf")
    assert destination.read_bytes() == before
    assert float(PdfReader(output).pages[0].mediabox.width) == 202
    success.assert_called_once()
    assert str(output) in success.call_args.args[1]


def test_registration_waits_for_atomic_publication_boundary(publication, monkeypatch):
    window, source, destination = publication
    replace_entered, release = threading.Event(), threading.Event()
    registration_entered, registered = threading.Event(), threading.Event()
    original_replace = app.os.replace
    results = []

    def delayed_replace(*args):
        replace_entered.set()
        assert release.wait(3)
        original_replace(*args)

    def register():
        registration_entered.set()
        window.state_model.add_docs("Other", [str(destination)])
        registered.set()

    monkeypatch.setattr(app.os, "replace", delayed_replace)
    worker = threading.Thread(target=lambda: results.append(
        app.App._merge_pdfs(window, [str(source)], destination)))
    registration = threading.Thread(target=register)
    worker.start()
    try:
        assert replace_entered.wait(3)
        registration.start()
        assert registration_entered.wait(3)
        assert not registered.wait(0.05)
    finally:
        release.set()
        worker.join(4)
        if registration.ident is not None:
            registration.join(4)
    assert not worker.is_alive() and not registration.is_alive()
    assert results == [True]
    assert registered.is_set()
    assert float(PdfReader(destination).pages[0].mediabox.width) == 202


def test_failed_replace_releases_state_lock_and_allows_retry(publication, monkeypatch):
    window, source, destination = publication
    before = destination.read_bytes()
    with monkeypatch.context() as patch:
        patch.setattr(app.os, "replace", Mock(side_effect=PermissionError("locked output")))
        assert app.App._merge_pdfs(window, [str(source)], destination) is False
    assert destination.read_bytes() == before
    assert window.state_model._lock.acquire(timeout=1)
    window.state_model._lock.release()
    assert not list(destination.parent.glob(".dokureader-pdf-*.tmp"))
    assert app.App._merge_pdfs(window, [str(source)], destination) is True


def test_removed_snapshot_original_and_late_alias_remain_protected(publication, monkeypatch):
    window, source, destination = publication
    original = destination.with_name("removed-original.pdf")
    write_pdf(original, 303)
    before = original.read_bytes()
    window.state_model.add_docs("Other", [str(original)])
    _, originals = window.state_model.collection_snapshot("Topic")
    window.state_model.remove_topic("Other")
    writer = PdfWriter()
    original_write = writer.write

    def retarget_after_snapshot(stream):
        original_write(stream)
        destination.unlink()
        app.os.link(original, destination)

    monkeypatch.setattr(writer, "write", retarget_after_snapshot)
    monkeypatch.setattr(app, "_PdfWriter", lambda: writer)
    assert app.App._merge_pdfs(window, [str(source)], destination, original_paths=originals) is False
    assert original.read_bytes() == before
    assert destination.read_bytes() == before


def test_late_alias_to_merge_input_is_protected_without_library(publication, monkeypatch):
    _, source, destination = publication
    before = source.read_bytes()
    writer = PdfWriter()
    original_write = writer.write

    def alias_input(stream):
        original_write(stream)
        destination.unlink()
        app.os.link(source, destination)

    monkeypatch.setattr(writer, "write", alias_input)
    monkeypatch.setattr(app, "_PdfWriter", lambda: writer)
    assert app.App._merge_pdfs(None, [str(source)], destination) is False
    assert source.read_bytes() == before
    assert destination.read_bytes() == before
