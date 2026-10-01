"""Every GUI edit reports persistence failure and can retry without losing memory state."""

import json
from types import MethodType, SimpleNamespace
from unittest.mock import Mock

import pytest

import DokuReader as app


OPERATIONS = (
    "on_topic_select", "add_topic", "rename_topic", "delete_topic",
    "add_files_dialog", "on_drop", "set_selected_read", "remove_selected_doc",
)


@pytest.fixture
def library_window(tmp_path, monkeypatch):
    source = tmp_path / "Übersicht.txt"
    source.write_text("Ärztlicher Überblick", encoding="utf-8")
    extra = tmp_path / "Neue Prüfung.txt"
    extra.write_text("Nächster Schritt", encoding="utf-8")
    destination = tmp_path / "bibliothek.json"
    monkeypatch.setattr(app, "STATE_FILE", str(destination))
    state = app.State()
    state.topics = {"Alt": [{"path": str(source), "read": False}], "Zweit": []}
    state.current_topic = "Alt"
    assert state.save() is True
    window = SimpleNamespace(
        state_model=state, topic_list=Mock(), doc_tree=Mock(),
        _reload_topics=Mock(), _reload_docs=Mock(), clear_preview=Mock(),
        _set_document_state=Mock(), save_status_label=Mock(),
        _split_dnd_paths=app.App._split_dnd_paths,
    )
    window._select_topic = MethodType(app.App._select_topic, window)
    window.topic_list.curselection.return_value = (0,)
    window.topic_list.get.return_value = "Alt"
    window.doc_tree.selection.return_value = (str(source),)
    window.doc_tree.get_children.return_value = (str(source),)
    monkeypatch.setattr(app.simpledialog, "askstring", lambda *args, **kwargs: "Neu")
    monkeypatch.setattr(app.filedialog, "askopenfilenames", lambda **kwargs: (str(extra),))
    monkeypatch.setattr(app.messagebox, "askyesno", lambda *args: True)
    warning = Mock()
    monkeypatch.setattr(app.messagebox, "showerror", warning)
    return window, destination, extra, warning


def invoke_edit(window, operation, extra):
    if operation == "on_topic_select":
        window.topic_list.get.return_value = "Zweit"
    arguments = {
        "on_drop": (SimpleNamespace(data="{" + str(extra) + "}"),),
        "set_selected_read": (True,),
    }.get(operation, ())
    getattr(app.App, operation)(window, *arguments)


@pytest.mark.parametrize("operation", OPERATIONS)
def test_failed_autosave_reports_error_and_manual_retry_preserves_edit(library_window, monkeypatch, operation):
    window, destination, extra, warning = library_window
    original = destination.read_bytes()
    real_replace = app.os.replace

    def fail_replace(*args):
        raise PermissionError("library destination busy")

    monkeypatch.setattr(app.os, "replace", fail_replace)
    invoke_edit(window, operation, extra)
    warning.assert_called_once()
    title, message = warning.call_args.args
    assert "nicht gespeichert" in title.lower()
    assert "Strg+S" in message
    assert destination.read_bytes() == original
    memory = {"topics": window.state_model.topics, "current_topic": window.state_model.current_topic}
    assert memory != json.loads(original)
    assert "nicht gespeichert" in window.save_status_label.configure.call_args.kwargs["text"].lower()
    assert not list(destination.parent.glob(".dokureader-state-*.tmp"))

    monkeypatch.setattr(app.os, "replace", real_replace)
    assert app.App.save_library(window) == "break"
    assert json.loads(destination.read_text(encoding="utf-8")) == memory
    assert "nicht" not in window.save_status_label.configure.call_args.kwargs["text"].lower()
    warning.assert_called_once()  # The successful retry must not display another error.


def test_new_topic_selection_survives_restart(library_window):
    window, destination, _extra, warning = library_window
    app.App.add_topic(window)
    restored = app.State()
    restored.load()
    assert restored.current_topic == "Neu"
    assert restored.topics == window.state_model.topics
    assert json.loads(destination.read_text(encoding="utf-8"))["current_topic"] == "Neu"
    warning.assert_not_called()


@pytest.mark.parametrize("publish_fails_after_backup", [False, True])
def test_manual_retry_requires_complete_recovery_before_replacing_damaged_library(tmp_path, monkeypatch, publish_fails_after_backup):
    destination = tmp_path / "bibliothek.json"
    original = b"\xffdamaged library"
    destination.write_bytes(original)
    monkeypatch.setattr(app, "STATE_FILE", str(destination))
    real_copy = app.shutil.copyfileobj

    def incomplete_backup(source, target, *args):
        target.write(b"partial")
        raise OSError("backup unavailable")

    monkeypatch.setattr(app.shutil, "copyfileobj", incomplete_backup)
    state = app.State()
    state.load()
    assert state.load_failed and state.recovery_path is None
    state.ensure_topic("Ärzte")
    state.current_topic = "Ärzte"
    window = SimpleNamespace(state_model=state, save_status_label=Mock())
    error, info = Mock(), Mock()
    monkeypatch.setattr(app.messagebox, "showerror", error)
    monkeypatch.setattr(app.messagebox, "showinfo", info)

    app.App.save_library(window)
    error.assert_called_once()
    info.assert_not_called()
    assert destination.read_bytes() == original
    assert list(tmp_path.iterdir()) == [destination]

    monkeypatch.setattr(app.shutil, "copyfileobj", real_copy)
    assert state.save() is False  # Automatic saving must still respect the gate.
    assert destination.read_bytes() == original
    real_replace = app.os.replace
    if publish_fails_after_backup:
        def fail_publish(*args):
            raise PermissionError("publication blocked")

        monkeypatch.setattr(app.os, "replace", fail_publish)
        app.App.save_library(window)
        assert destination.read_bytes() == original
        assert state.recovery_path in error.call_args.args[1]
        info.assert_not_called()
        monkeypatch.setattr(app.os, "replace", real_replace)
    app.App.save_library(window)
    from pathlib import Path
    assert Path(state.recovery_path).read_bytes() == original
    assert json.loads(destination.read_text(encoding="utf-8")) == {
        "topics": {"Ärzte": []}, "current_topic": "Ärzte",
    }
    if publish_fails_after_backup:
        info.assert_not_called()  # The earlier error already disclosed the backup.
        assert error.call_count == 2
    else:
        info.assert_called_once()
        assert state.recovery_path in info.call_args.args[1]
        error.assert_called_once()
    assert set(tmp_path.iterdir()) == {destination, Path(state.recovery_path)}
