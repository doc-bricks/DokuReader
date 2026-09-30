"""Topic names must produce portable filenames contained in the chosen directory."""

from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from pypdf import PdfWriter

import DokuReader as app


@pytest.mark.parametrize("topic", ["../escaped", "nested/report", "Ärzte: Untersuchung", "a\\b?c*"])
def test_worker_exports_unsafe_topic_inside_desktop(tmp_path, monkeypatch, topic):
    desktop = tmp_path / "desktop"
    desktop.mkdir()
    source = tmp_path / "source.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=200)
    with source.open("wb") as stream:
        writer.write(stream)
    writer.close()
    monkeypatch.setattr(app, "desktop_path", lambda: desktop)
    success = Mock()
    monkeypatch.setattr(app.messagebox, "showinfo", success)
    window = SimpleNamespace(
        state_model=SimpleNamespace(
            list_docs=lambda topic: [{"path": str(source)}],
            all_document_paths=lambda: [str(source)],
        ),
        _set_busy=Mock(), status_info=Mock(),
        _merge_pdfs=lambda sources, output: app.App._merge_pdfs(None, sources, output),
        after=lambda delay, callback: callback(),
    )
    app.App._create_collection_pdf_worker(window, topic, "alle")
    outputs = list(desktop.iterdir())
    assert len(outputs) == 1
    assert outputs[0].parent == desktop
    assert not any(char in outputs[0].name for char in '<>:"/\\|?*')
    assert not (tmp_path / "escaped_alle.pdf").exists()
    success.assert_called_once()


@pytest.mark.parametrize("topic", ["Ärzte", "Bücher und Prüfung"])
def test_normal_german_topic_names_remain_unchanged(topic):
    assert app.collection_pdf_filename(topic, "gelesene") == topic + "_gelesene.pdf"


def test_sanitized_names_do_not_collide_with_other_topics():
    names = [app.collection_pdf_filename(topic, "alle") for topic in ["a/b", "a\\b", "a_b"]]
    assert len(set(names)) == 3


def test_long_topic_is_shortened_to_portable_component():
    name = app.collection_pdf_filename("Prüfung" * 70, "ungelesene")
    assert len(name.encode("utf-16-le")) // 2 <= 255
    assert name.endswith("_ungelesene.pdf")


@pytest.mark.parametrize("filter_mode", ["../escape", "invalid"])
def test_unknown_filter_cannot_become_part_of_a_path(filter_mode):
    with pytest.raises(ValueError):
        app.collection_pdf_filename("Topic", filter_mode)
