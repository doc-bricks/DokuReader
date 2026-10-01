"""Accepted collection exports survive close and never invoke Tk from a worker."""
import os
import sys
import threading
import queue
import time
from unittest.mock import Mock

import fitz
import pytest

import DokuReader as app


def pump(window, predicate, timeout=4):
    deadline = time.monotonic() + timeout
    while not predicate() and time.monotonic() < deadline:
        window.update()
        time.sleep(0.005)
    assert predicate(), "GUI/worker did not complete within the test deadline"


@pytest.fixture
def window(tmp_path, monkeypatch):
    if not (sys.platform.startswith("win") or os.environ.get("DISPLAY")
            or os.environ.get("WAYLAND_DISPLAY")):
        pytest.skip("Tk UI requires a display")
    monkeypatch.setattr(app, "STATE_FILE", str(tmp_path / "state.json"))
    monkeypatch.setattr(app, "desktop_path", lambda: tmp_path)
    monkeypatch.setattr(app.messagebox, "showinfo", Mock())
    monkeypatch.setattr(app.messagebox, "showerror", Mock())
    for attempt in range(3):
        try:
            ui = app.App()
            break
        except app.tk.TclError:
            partial = getattr(app.tk, "_default_root", None)
            if partial is not None:
                try:
                    partial.destroy()
                except app.tk.TclError:
                    pass
            if attempt == 2:
                raise
    ui.withdraw()
    source = tmp_path / "Überblick.pdf"
    with fitz.open() as pdf:
        pdf.new_page().insert_text((30, 30), "Original document")
        pdf.save(source)
    ui.state_model.topics = {"Bücher": [{"path": str(source), "read": True}]}
    ui.state_model.current_topic = "Bücher"
    ui._reload_topics()
    ui._select_topic("Bücher")
    ui.update()
    original_after = ui.after
    owner_thread = threading.get_ident()

    def checked_after(*args, **kwargs):
        assert threading.get_ident() == owner_thread, "worker invoked Tk.after"
        return original_after(*args, **kwargs)

    monkeypatch.setattr(ui, "after", checked_after)
    try:
        yield ui
    finally:
        worker = getattr(ui, "_collection_thread", None)
        if worker is not None:
            worker.join(5)
            assert not worker.is_alive()
        try:
            ui.destroy()
        except app.tk.TclError:
            pass


def block_merge(window, monkeypatch):
    entered, release = threading.Event(), threading.Event()
    original = window._merge_pdfs
    calls = []

    def merge(parts, destination, **kwargs):
        calls.append((parts, destination))
        entered.set()
        assert release.wait(3)
        return original(parts, destination, **kwargs)

    monkeypatch.setattr(window, "_merge_pdfs", merge)
    return entered, release, calls


def test_double_start_and_close_drain_one_real_pdf(window, tmp_path, monkeypatch):
    entered, release, calls = block_merge(window, monkeypatch)
    original_save = window.state_model.save
    save = Mock(wraps=original_save)
    monkeypatch.setattr(window.state_model, "save", save)
    closed = threading.Event()
    destroy = window.destroy
    monkeypatch.setattr(window, "destroy", lambda: (destroy(), closed.set()))
    try:
        window.create_collection_pdf()
        pump(window, entered.is_set)
        window.create_collection_pdf()
        window.filter_var.set("gelesene")
        window._reload_docs()
        assert "disabled" in window.collection_export_button.state()
        assert not window._collection_thread.daemon
        window.on_close()
        save.assert_not_called()
        assert not closed.is_set()
        heartbeat = threading.Event()
        window.after(0, heartbeat.set)
        pump(window, heartbeat.is_set)
        assert window.winfo_exists()
    finally:
        release.set()
    pump(window, closed.is_set)
    assert len(calls) == 1
    assert (tmp_path / "Bücher_alle.pdf").exists()
    save.assert_called_once()
    app.messagebox.showinfo.assert_called_once()


def test_delayed_close_save_failure_preserves_window_and_edits(window, monkeypatch):
    entered, release, _ = block_merge(window, monkeypatch)
    save = Mock(return_value=False)
    monkeypatch.setattr(window.state_model, "save", save)
    try:
        window.create_collection_pdf()
        pump(window, entered.is_set)
        window.on_close()
    finally:
        release.set()
    pump(window, lambda: save.call_count == 1)
    assert window.winfo_exists()
    assert window.state_model.current_topic == "Bücher"
    assert window._collection_thread is None
    assert not window._close_requested
    assert "disabled" not in window.collection_export_button.state()
    app.messagebox.showerror.assert_called_once()


def test_callback_failure_keeps_polling_live_export(window, monkeypatch):
    entered, release, _ = block_merge(window, monkeypatch)
    report = Mock()
    monkeypatch.setattr(window, "report_callback_exception", report)
    try:
        window.create_collection_pdf()
        pump(window, entered.is_set)
        window._ui_callbacks.put(Mock(side_effect=RuntimeError("dialog failed")))
        pump(window, lambda: report.call_count == 1)
        assert window._collection_thread.is_alive()
        assert "disabled" in window.collection_export_button.state()
    finally:
        release.set()
    pump(window, lambda: window._collection_thread is None)
    app.messagebox.showinfo.assert_called_once()
    assert "disabled" not in window.collection_export_button.state()


def test_thread_start_failure_restores_controls_and_allows_retry(window, monkeypatch):
    original_start = threading.Thread.start
    with monkeypatch.context() as patch:
        patch.setattr(threading.Thread, "start", Mock(side_effect=RuntimeError("no threads")))
        window.create_collection_pdf()
    assert window._collection_thread is None
    assert "disabled" not in window.collection_export_button.state()
    app.messagebox.showerror.assert_called_once()
    assert threading.Thread.start is original_start
    window.create_collection_pdf()
    pump(window, lambda: window._collection_thread is None)
    app.messagebox.showinfo.assert_called_once()


def test_unexpected_worker_failure_reports_on_gui_and_allows_retry(window, monkeypatch):
    desktop = app.desktop_path
    monkeypatch.setattr(app, "desktop_path", Mock(side_effect=OSError("no output directory")))
    window.create_collection_pdf()
    pump(window, lambda: getattr(window, "_collection_thread", None) is None
         and app.messagebox.showerror.call_count == 1)
    assert "no output directory" in app.messagebox.showerror.call_args.args[1]
    assert "disabled" not in window.collection_export_button.state()
    monkeypatch.setattr(app, "desktop_path", desktop)
    window.create_collection_pdf()
    pump(window, lambda: window._collection_thread is None)
    app.messagebox.showinfo.assert_called_once()


def test_accepted_snapshot_survives_edits_and_protects_removed_original(window, tmp_path, monkeypatch):
    protected = tmp_path / "Bücher_gelesene.pdf"
    protected.write_bytes(b"original in another topic")
    window.state_model.topics["Other"] = [{"path": str(protected), "read": False}]
    window.filter_var.set("gelesene")
    entered, release = threading.Event(), threading.Event()
    original_worker = window._create_collection_pdf_worker

    def delayed(*args):
        entered.set()
        assert release.wait(3)
        original_worker(*args)

    monkeypatch.setattr(window, "_create_collection_pdf_worker", delayed)
    try:
        window.create_collection_pdf()
        pump(window, entered.is_set)
        window.state_model.set_read("Bücher", str(tmp_path / "Überblick.pdf"), False)
        window.state_model.remove_topic("Other")
        window.state_model.rename_topic("Bücher", "Neu")
        window.filter_var.set("ungelesene")
    finally:
        release.set()
    pump(window, lambda: window._collection_thread is None)
    assert protected.read_bytes() == b"original in another topic"
    outputs = [path for path in tmp_path.glob("Bücher_gelesene*.pdf") if path != protected]
    assert len(outputs) == 1
    with fitz.open(outputs[0]) as pdf:
        assert "Original document" in pdf[0].get_text()
    app.messagebox.showinfo.assert_called_once()


def test_state_export_snapshot_copies_documents_and_all_topic_paths():
    state = app.State()
    state.topics = {"A": [{"path": "a.pdf", "read": True}],
                    "B": [{"path": "b.pdf", "read": False}]}
    documents, originals = state.collection_snapshot("A")
    state.set_read("A", "a.pdf", False)
    state.remove_topic("B")
    assert documents == [{"path": "a.pdf", "read": True}]
    assert originals == ["a.pdf", "b.pdf"]


def test_poller_drains_result_published_between_empty_check_and_worker_end():
    from types import SimpleNamespace

    callbacks = queue.SimpleQueue()
    empty_observed, finished = threading.Event(), threading.Event()
    notification = Mock()

    def finish_after_empty_check():
        assert empty_observed.wait(2)
        callbacks.put(notification)
        finished.set()

    worker = threading.Thread(target=finish_after_empty_check)

    class BoundaryQueue:
        raced = False

        def get_nowait(self):
            try:
                return callbacks.get_nowait()
            except queue.Empty:
                if not self.raced:
                    self.raced = True
                    empty_observed.set()
                    assert finished.wait(2)
                    worker.join(2)
                raise

    ui = SimpleNamespace(
        _ui_callbacks=BoundaryQueue(), _collection_thread=worker,
        _close_requested=False, config=Mock(), _update_collection_export_controls=Mock(),
    )
    worker.start()
    try:
        app.App._poll_collection_export(ui)
    finally:
        empty_observed.set()
        worker.join(2)
    notification.assert_called_once()
    assert callbacks.empty()
    assert ui._collection_thread is None


@pytest.mark.parametrize("report_failed", [False, True])
def test_callback_failure_cannot_strand_finished_export(report_failed):
    from types import SimpleNamespace

    callbacks = queue.SimpleQueue()
    callbacks.put(Mock(side_effect=RuntimeError("dialog failed")))
    report = Mock(side_effect=RuntimeError("report failed") if report_failed else None)
    ui = SimpleNamespace(
        _ui_callbacks=callbacks,
        _collection_thread=SimpleNamespace(is_alive=lambda: False, join=Mock()),
        _close_requested=False, config=Mock(), _update_collection_export_controls=Mock(),
        report_callback_exception=report,
    )
    if report_failed:
        with pytest.raises(RuntimeError, match="report failed"):
            app.App._poll_collection_export(ui)
    else:
        app.App._poll_collection_export(ui)
    report.assert_called_once()
    assert ui._collection_thread is None
    ui._update_collection_export_controls.assert_called_once()
