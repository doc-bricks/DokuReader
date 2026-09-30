"""A rejected library must remain recoverable after editing or closing the app."""

from types import SimpleNamespace
from unittest.mock import Mock

import pytest

import DokuReader as app


@pytest.mark.parametrize("damaged", [b"null", b"\xffinvalid", b'{"topics":{"Broken":[null]}}'])
def test_save_preserves_rejected_library_in_unique_backup(tmp_path, monkeypatch, damaged):
    path = tmp_path / "state.json"
    path.write_bytes(damaged)
    foreign = tmp_path / "state.json.damaged-existing.bak"
    foreign.write_bytes(b"older recovery")
    monkeypatch.setattr(app, "STATE_FILE", str(path))
    state = app.State()
    state.load()
    state.ensure_topic("Neue Bücher")
    state.save()
    backups = [p for p in tmp_path.iterdir() if p not in (path, foreign)]
    assert len(backups) == 1
    assert backups[0].read_bytes() == damaged
    assert foreign.read_bytes() == b"older recovery"
    assert "Neue Bücher" in path.read_text(encoding="utf-8")
    assert state.save() is True
    assert backups[0].read_bytes() == damaged
    assert len(list(tmp_path.iterdir())) == 3


def test_failed_backup_blocks_save_and_cleans_partial_copy(tmp_path, monkeypatch):
    path = tmp_path / "state.json"
    damaged = b"not a library"
    path.write_bytes(damaged)
    monkeypatch.setattr(app, "STATE_FILE", str(path))

    def fail_copy(source, destination, *args):
        destination.write(b"partial")
        raise OSError("disk full")

    monkeypatch.setattr(app.shutil, "copyfileobj", fail_copy)
    state = app.State()
    state.load()
    state.ensure_topic("New")
    assert state.save() is False
    assert path.read_bytes() == damaged
    assert list(tmp_path.iterdir()) == [path]


def test_close_keeps_window_open_when_save_fails(monkeypatch):
    window = SimpleNamespace(state_model=SimpleNamespace(save=Mock(return_value=False)), destroy=Mock())
    error = Mock()
    monkeypatch.setattr(app.messagebox, "showerror", error)
    app.App.on_close(window)
    window.destroy.assert_not_called()
    error.assert_called_once()


def test_close_destroys_window_after_successful_save(monkeypatch):
    window = SimpleNamespace(state_model=SimpleNamespace(save=Mock(return_value=True)), destroy=Mock())
    error = Mock()
    monkeypatch.setattr(app.messagebox, "showerror", error)
    app.App.on_close(window)
    window.destroy.assert_called_once()
    error.assert_not_called()
