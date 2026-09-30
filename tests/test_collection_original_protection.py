"""Collection exports must preserve every original referenced by the library."""

from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from pypdf import PdfReader, PdfWriter

import DokuReader as app


def write_pdf(path, width):
    writer = PdfWriter()
    writer.add_blank_page(width=width, height=200)
    with path.open("wb") as stream:
        writer.write(stream)
    writer.close()


@pytest.mark.parametrize("location", ["selected", "filtered", "other_topic"])
def test_export_uses_new_name_when_target_is_library_original(tmp_path, monkeypatch, location):
    mode = "gelesene" if location == "filtered" else "alle"
    original = tmp_path / f"Topic_{mode}.pdf"
    source = tmp_path / "source.pdf"
    write_pdf(original, 101)
    write_pdf(source, 102)
    original_bytes = original.read_bytes()
    state = app.State()
    state.topics = {"Topic": [{"path": str(source), "read": True}]}
    original_doc = {"path": str(original), "read": location != "filtered"}
    state.topics.setdefault("Other" if location == "other_topic" else "Topic", []).append(original_doc)
    monkeypatch.setattr(app, "desktop_path", lambda: tmp_path)
    success = Mock()
    monkeypatch.setattr(app.messagebox, "showinfo", success)
    window = SimpleNamespace(
        state_model=state, _set_busy=Mock(), status_info=Mock(),
        _merge_pdfs=lambda parts, output: app.App._merge_pdfs(None, parts, output),
        after=lambda delay, callback: callback(),
    )
    app.App._create_collection_pdf_worker(window, "Topic", mode)
    assert original.read_bytes() == original_bytes
    output = tmp_path / f"Topic_{mode} (1).pdf"
    with output.open("rb") as stream:
        result = PdfReader(stream)
        widths = [float(page.mediabox.width) for page in result.pages]
    assert widths == ([102, 101] if location == "selected" else [102])
    success.assert_called_once()
    assert str(output) in success.call_args.args[1]


def test_collision_suffix_does_not_overwrite_existing_unrelated_file(tmp_path, monkeypatch):
    original = tmp_path / "Topic_alle.pdf"
    write_pdf(original, 101)
    foreign = tmp_path / "Topic_alle (1).pdf"
    foreign.write_bytes(b"foreign output")
    original_bytes = original.read_bytes()
    state = app.State()
    state.topics = {"Topic": [{"path": str(original), "read": False}]}
    monkeypatch.setattr(app, "desktop_path", lambda: tmp_path)
    monkeypatch.setattr(app.messagebox, "showinfo", Mock())
    window = SimpleNamespace(
        state_model=state, _set_busy=Mock(), status_info=Mock(),
        _merge_pdfs=lambda parts, output: app.App._merge_pdfs(None, parts, output),
        after=lambda delay, callback: callback(),
    )
    app.App._create_collection_pdf_worker(window, "Topic", "alle")
    assert original.read_bytes() == original_bytes
    assert foreign.read_bytes() == b"foreign output"
    assert (tmp_path / "Topic_alle (2).pdf").is_file()


def test_merge_refuses_to_replace_its_own_input(tmp_path):
    original = tmp_path / "original.pdf"
    write_pdf(original, 101)
    before = original.read_bytes()
    assert app.App._merge_pdfs(None, [str(original)], original) is False
    assert original.read_bytes() == before


def test_merge_refuses_hardlink_alias_of_its_input(tmp_path):
    original = tmp_path / "original.pdf"
    alias = tmp_path / "alias.pdf"
    write_pdf(original, 101)
    app.os.link(original, alias)
    before = original.read_bytes()
    assert app.App._merge_pdfs(None, [str(original)], alias) is False
    assert original.read_bytes() == before
    assert alias.read_bytes() == before
