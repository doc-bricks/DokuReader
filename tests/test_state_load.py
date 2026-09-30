"""Malformed persisted libraries must not replace a usable in-memory state."""

import json

import pytest

import DokuReader as app


@pytest.mark.parametrize("payload", [
    None, [], "library", 7,
    {}, {"topics": []}, {"topics": {"Neu": None}},
    {"topics": {"Neu": "document.txt"}},
    {"topics": {"Neu": [None]}},
    {"topics": {"Neu": [{}]}},
    {"topics": {"Neu": [{"path": 7}]}},
    {"topics": {"Neu": [{"path": ""}]}},
    {"topics": {"Neu": [{"path": "quelle.txt", "read": "false"}]}},
])
def test_invalid_structure_preserves_current_library(tmp_path, monkeypatch, payload):
    path = tmp_path / "state.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    original_bytes = path.read_bytes()
    monkeypatch.setattr(app, "STATE_FILE", str(path))
    state = app.State()
    state.topics = {"Vorhanden": [{"path": "alt.txt", "read": True}]}
    state.current_topic = "Vorhanden"
    original_topics = state.topics
    state.load()
    assert state.topics is original_topics
    assert state.current_topic == "Vorhanden"
    assert path.read_bytes() == original_bytes


@pytest.mark.parametrize("content", [b"{", b"\xff\xfeinvalid"])
def test_unreadable_json_preserves_current_library(tmp_path, monkeypatch, content):
    path = tmp_path / "state.json"
    path.write_bytes(content)
    monkeypatch.setattr(app, "STATE_FILE", str(path))
    state = app.State()
    state.ensure_topic("Vorhanden")
    state.current_topic = "Vorhanden"
    state.load()
    assert state.topics == {"Vorhanden": []}
    assert state.current_topic == "Vorhanden"
    assert path.read_bytes() == content


def test_valid_legacy_library_preserves_missing_paths_and_defaults_read(tmp_path, monkeypatch):
    path = tmp_path / "state.json"
    payload = {"topics": {"Bücher": [{"path": "fehlende Prüfung.txt"}]}, "current_topic": "Bücher"}
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(app, "STATE_FILE", str(path))
    state = app.State()
    state.load()
    assert state.list_docs("Bücher") == [{"path": "fehlende Prüfung.txt", "read": False}]
    assert state.current_topic == "Bücher"


def test_valid_library_clears_selection_of_absent_topic(tmp_path, monkeypatch):
    path = tmp_path / "state.json"
    path.write_text('{"topics": {}, "current_topic": "Removed"}', encoding="utf-8")
    monkeypatch.setattr(app, "STATE_FILE", str(path))
    state = app.State()
    state.load()
    assert state.topics == {}
    assert state.current_topic is None
