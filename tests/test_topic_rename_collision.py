"""A rename must preserve both topics when the target already exists."""

from types import SimpleNamespace
from unittest.mock import Mock, patch

import DokuReader as app


def populated_state():
    state = app.State()
    state.topics = {
        "Quelle": [{"path": "quelle.txt", "read": False}],
        "Ziel": [{"path": "ziel.txt", "read": True}],
    }
    state.current_topic = "Quelle"
    return state


def test_collision_preserves_both_topics_and_selection():
    state = populated_state()
    original = {key: [dict(doc) for doc in docs] for key, docs in state.topics.items()}
    assert state.rename_topic("Quelle", "Ziel") is False
    assert state.topics == original
    assert state.current_topic == "Quelle"


def test_same_name_is_a_successful_noop():
    state = populated_state()
    original = state.topics["Quelle"]
    assert state.rename_topic("Quelle", "Quelle") is True
    assert state.topics["Quelle"] is original
    assert state.current_topic == "Quelle"


def test_concurrent_renames_to_one_target_preserve_losing_source():
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    state = populated_state()
    barrier = Barrier(2)

    def rename(source):
        barrier.wait(timeout=5)
        return state.rename_topic(source, "Gemeinsam")

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(rename, ("Quelle", "Ziel")))
    assert sorted(results) == [False, True]
    assert len(state.topics) == 2
    assert sorted(doc["path"] for docs in state.topics.values() for doc in docs) == [
        "quelle.txt", "ziel.txt",
    ]
    assert state.current_topic in state.topics


def test_dialog_does_not_save_or_select_a_target_created_during_rename():
    state = populated_state()
    state.save = Mock()
    rename = state.rename_topic

    def create_target_then_rename(source, target):
        state.topics[target] = [{"path": "neues-ziel.txt", "read": True}]
        return rename(source, target)

    state.rename_topic = create_target_then_rename
    window = SimpleNamespace(
        topic_list=Mock(), state_model=state,
        _reload_topics=Mock(), _select_topic=Mock(),
    )
    window.topic_list.curselection.return_value = (0,)
    window.topic_list.get.return_value = "Quelle"
    with patch.object(app.simpledialog, "askstring", return_value="Neu"), \
            patch.object(app.messagebox, "showwarning") as warning:
        app.App.rename_topic(window)
    assert state.topics["Quelle"][0]["path"] == "quelle.txt"
    assert state.topics["Neu"][0]["path"] == "neues-ziel.txt"
    assert state.current_topic == "Quelle"
    warning.assert_called_once()
    state.save.assert_not_called()
    window._reload_topics.assert_not_called()
    window._select_topic.assert_not_called()
