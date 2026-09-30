"""Saving a library must preserve its previous file when publication fails."""

import builtins
import json
import os

import pytest

import DokuReader as app


@pytest.fixture
def library(tmp_path, monkeypatch):
    path = tmp_path / "bibliothek.json"
    original = b'{"topics": {"Alt": []}, "current_topic": "Alt"}'
    path.write_bytes(original)
    monkeypatch.setattr(app, "STATE_FILE", str(path))
    state = app.State()
    state.topics = {"Bücher": [{"path": "prüfung.txt", "read": True}]}
    state.current_topic = "Bücher"
    return state, path, original


def test_partial_write_preserves_previous_library(library, monkeypatch):
    state, path, original = library
    real_open, real_fdopen = builtins.open, os.fdopen

    class FailingWriter:
        def __init__(self, stream):
            self.stream = stream

        def __enter__(self):
            return self

        def __exit__(self, *args):
            self.stream.close()

        def write(self, content):
            self.stream.write(content[:8])
            raise OSError("simulated disk write failure")

    def failing_open(file, mode="r", *args, **kwargs):
        stream = real_open(file, mode, *args, **kwargs)
        return FailingWriter(stream) if "w" in mode else stream

    monkeypatch.setattr(builtins, "open", failing_open)
    monkeypatch.setattr(os, "fdopen", lambda *a, **kw: FailingWriter(real_fdopen(*a, **kw)))
    state.save()
    assert path.read_bytes() == original
    assert list(path.parent.iterdir()) == [path]


def test_invalid_utf8_preserves_previous_library(library):
    state, path, original = library
    state.current_topic = "\ud800"
    try:
        state.save()
    except UnicodeError:
        pass
    assert path.read_bytes() == original
    assert list(path.parent.iterdir()) == [path]


def test_failed_replace_preserves_library_and_foreign_file(library, monkeypatch):
    state, path, original = library
    foreign = path.parent / ".dokureader-state-foreign.tmp"
    foreign.write_bytes(b"belongs to another writer")

    def fail_replace(*args):
        raise PermissionError("destination busy")

    monkeypatch.setattr(os, "replace", fail_replace)
    state.save()
    assert path.read_bytes() == original
    assert foreign.read_bytes() == b"belongs to another writer"
    assert set(path.parent.iterdir()) == {path, foreign}


def test_saved_library_roundtrips_umlauts_and_read_status(library):
    state, path, _ = library
    state.save()
    assert "Bücher" in path.read_text(encoding="utf-8")
    assert json.loads(path.read_text(encoding="utf-8"))["topics"] == state.topics
    restored = app.State()
    restored.load()
    assert restored.topics == state.topics
    assert restored.current_topic == "Bücher"
    assert list(path.parent.iterdir()) == [path]
