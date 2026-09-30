"""A JSON exchange export must not replace originals or internal state files."""

import json
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

import DokuReader as app


@pytest.mark.parametrize("target_kind", [
    "original", "other_topic", "state", "missing_state", "recovery", "original_alias", "state_alias",
])
def test_dialog_rejects_protected_export_targets(tmp_path, monkeypatch, target_kind):
    original = tmp_path / "original.txt"
    original.write_bytes(b"original document")
    persisted = tmp_path / "state.json"
    if target_kind != "missing_state":
        persisted.write_bytes(b'{"topics": {}, "current_topic": null}')
    recovery = tmp_path / "state.json.damaged-backup.bak"
    recovery.write_bytes(b"damaged state retained for recovery")
    state = app.State()
    state.topics = {"Other" if target_kind == "other_topic" else "Topic": [{"path": str(original), "read": True}]}
    state.recovery_path = str(recovery)
    monkeypatch.setattr(app, "STATE_FILE", str(persisted))
    targets = {"original": original, "other_topic": original, "state": persisted,
               "missing_state": persisted, "recovery": recovery}
    if target_kind.endswith("_alias"):
        alias = tmp_path / "alias.json"
        app.os.link(original if target_kind == "original_alias" else persisted, alias)
        target = alias
    else:
        target = targets[target_kind]
    before = {path: path.read_bytes() for path in tmp_path.iterdir()}
    monkeypatch.setattr(app.filedialog, "asksaveasfilename", lambda **kw: str(target))
    success, error = Mock(), Mock()
    monkeypatch.setattr(app.messagebox, "showinfo", success)
    monkeypatch.setattr(app.messagebox, "showerror", error)
    app.App.export_library_json(SimpleNamespace(state_model=state))
    assert {path: path.read_bytes() for path in tmp_path.iterdir()} == before
    success.assert_not_called()
    error.assert_called_once()
    assert "andere" in error.call_args.args[1].lower()


def test_unrelated_existing_export_can_still_be_replaced(tmp_path, monkeypatch):
    source = tmp_path / "quelle.txt"
    source.write_text("Prüfung", encoding="utf-8")
    destination = tmp_path / "export.json"
    destination.write_bytes(b"previous export")
    monkeypatch.setattr(app, "STATE_FILE", str(tmp_path / "state.json"))
    state = app.State()
    state.topics = {"Bücher": [{"path": str(source), "read": True}]}
    monkeypatch.setattr(app.filedialog, "asksaveasfilename", lambda **kw: str(destination))
    success, error = Mock(), Mock()
    monkeypatch.setattr(app.messagebox, "showinfo", success)
    monkeypatch.setattr(app.messagebox, "showerror", error)
    app.App.export_library_json(SimpleNamespace(state_model=state))
    assert json.loads(destination.read_text(encoding="utf-8"))["schema_version"] == app.LIBRARY_EXPORT_SCHEMA
    assert source.read_text(encoding="utf-8") == "Prüfung"
    success.assert_called_once()
    error.assert_not_called()


def test_cancelled_dialog_does_not_inspect_or_write_library(monkeypatch):
    state = Mock()
    monkeypatch.setattr(app.filedialog, "asksaveasfilename", lambda **kw: "")
    write = Mock()
    monkeypatch.setattr(app, "write_library_export", write)
    app.App.export_library_json(SimpleNamespace(state_model=state))
    state.all_document_paths.assert_not_called()
    write.assert_not_called()
