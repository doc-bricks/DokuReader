"""Same-name sources in different folders must retain their distinct PDF content."""

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from pypdf import PdfReader, PdfWriter

import DokuReader as app


def worker_window(paths, tmp_path, monkeypatch):
    monkeypatch.setattr(app, "desktop_path", lambda: tmp_path)
    monkeypatch.setattr(app.messagebox, "showinfo", Mock())
    monkeypatch.setattr(app.messagebox, "showwarning", Mock())
    return SimpleNamespace(
        state_model=SimpleNamespace(
            list_docs=lambda topic: [{"path": str(p)} for p in paths],
            all_document_paths=lambda: [str(p) for p in paths],
        ),
        _set_busy=Mock(), status_info=Mock(),
        after=lambda delay, callback: callback(),
        _merge_pdfs=lambda parts, output: app.App._merge_pdfs(None, parts, output),
    )


@pytest.mark.parametrize("extensions,method", [
    ((".txt", ".txt"), "_txt_to_pdf"),
    ((".png", ".jpg"), "_image_to_pdf"),
    ((".docx", ".odt"), "_office_to_pdf"),
])
def test_conversions_isolate_same_stem_documents(tmp_path, monkeypatch, extensions, method):
    sources = [tmp_path / "first" / ("Bericht" + extensions[0]),
               tmp_path / "second" / ("Bericht" + extensions[1])]
    for index, source in enumerate(sources):
        source.parent.mkdir()
        source.write_bytes(f"original {index}".encode())
    window = worker_window(sources, tmp_path, monkeypatch)
    conversion_dirs = []

    def convert(source, directory):
        conversion_dirs.append(directory)
        output = directory / (Path(source).stem + ".pdf")
        writer = PdfWriter()
        writer.add_blank_page(width=100 + len(conversion_dirs), height=200)
        with output.open("wb") as stream:
            writer.write(stream)
        writer.close()
        return str(output)

    setattr(window, method, convert)
    app.App._create_collection_pdf_worker(window, "Bücher", "alle")
    with (tmp_path / "Bücher_alle.pdf").open("rb") as stream:
        result = PdfReader(stream)
        assert [float(page.mediabox.width) for page in result.pages] == [101, 102]
    assert len(set(conversion_dirs)) == 2
    assert all(not directory.exists() for directory in conversion_dirs)
    assert [p.read_bytes() for p in sources] == [b"original 0", b"original 1"]


@pytest.mark.skipif(not app.REPORTLAB_AVAILABLE, reason="ReportLab required for real TXT conversion")
def test_real_text_conversion_preserves_both_same_name_sources(tmp_path, monkeypatch):
    sources = [tmp_path / "first" / "Bericht.txt", tmp_path / "second" / "Bericht.txt"]
    contents = ["FIRST DISTINCT DOCUMENT", "SECOND DISTINCT DOCUMENT"]
    for source, content in zip(sources, contents):
        source.parent.mkdir()
        source.write_text(content, encoding="utf-8")
    window = worker_window(sources, tmp_path, monkeypatch)
    window._txt_to_pdf = lambda source, directory: app.App._txt_to_pdf(None, source, directory)
    app.App._create_collection_pdf_worker(window, "Topic", "alle")
    with (tmp_path / "Topic_alle.pdf").open("rb") as stream:
        result = PdfReader(stream)
        texts = [page.extract_text().strip() for page in result.pages]
    assert texts == contents
    assert [p.read_text(encoding="utf-8") for p in sources] == contents
