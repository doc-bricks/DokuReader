"""Only complete, nonempty PDF merges may replace an existing output."""

from pathlib import Path
from unittest.mock import Mock

import pytest
from pypdf import PdfReader, PdfWriter

import DokuReader as app


@pytest.fixture
def pdf_files(tmp_path):
    sources = []
    for index in range(2):
        path = tmp_path / f"quelle-{index}.pdf"
        writer = PdfWriter()
        writer.add_blank_page(width=100 + index, height=200)
        with path.open("wb") as stream:
            writer.write(stream)
        writer.close()
        sources.append(str(path))
    output = tmp_path / "ausgabe.pdf"
    output.write_bytes(b"previous output")
    return sources, output


@pytest.mark.parametrize("error", [OSError("missing source"), ValueError("invalid source")])
def test_one_failed_source_aborts_entire_merge(pdf_files, monkeypatch, error):
    sources, output = pdf_files
    writer = Mock()
    writer.append.side_effect = [None, error]
    monkeypatch.setattr(app, "_PdfWriter", lambda: writer)
    assert app.App._merge_pdfs(None, sources, output) is False
    assert output.read_bytes() == b"previous output"
    writer.write.assert_not_called()
    writer.close.assert_called_once()


def test_partial_write_preserves_existing_output(pdf_files, monkeypatch):
    sources, output = pdf_files
    writer = PdfWriter()

    def fail_write(stream):
        stream.write(b"partial PDF")
        raise OSError("disk full")

    monkeypatch.setattr(writer, "write", fail_write)
    monkeypatch.setattr(app, "_PdfWriter", lambda: writer)
    before = set(output.parent.iterdir())
    assert app.App._merge_pdfs(None, sources, output) is False
    assert output.read_bytes() == b"previous output"
    assert set(output.parent.iterdir()) == before


def test_real_corrupt_pdf_returns_failure_without_publication(pdf_files):
    sources, output = pdf_files
    Path(sources[1]).write_bytes(b"not a PDF")
    assert app.App._merge_pdfs(None, sources, output) is False
    assert output.read_bytes() == b"previous output"


def test_empty_input_does_not_publish_empty_pdf(pdf_files):
    _, output = pdf_files
    assert app.App._merge_pdfs(None, [], output) is False
    assert output.read_bytes() == b"previous output"


def test_zero_page_input_does_not_publish_empty_pdf(pdf_files):
    sources, output = pdf_files
    writer = PdfWriter()
    with Path(sources[0]).open("wb") as stream:
        writer.write(stream)
    writer.close()
    assert app.App._merge_pdfs(None, sources[:1], output) is False
    assert output.read_bytes() == b"previous output"


def test_success_preserves_page_order_and_cleans_temporary_file(pdf_files):
    sources, output = pdf_files
    before = set(output.parent.iterdir())
    assert app.App._merge_pdfs(None, sources, output) is True
    with output.open("rb") as stream:
        result = PdfReader(stream)
        assert [float(page.mediabox.width) for page in result.pages] == [100, 101]
    assert set(output.parent.iterdir()) == before


def test_failed_replace_preserves_output_and_foreign_temp(pdf_files, monkeypatch):
    sources, output = pdf_files
    foreign = output.parent / ".dokureader-pdf-foreign.tmp"
    foreign.write_bytes(b"foreign work")
    before = set(output.parent.iterdir())

    def fail_replace(*args):
        raise PermissionError("destination locked")

    monkeypatch.setattr(app.os, "replace", fail_replace)
    assert app.App._merge_pdfs(None, sources, output) is False
    assert output.read_bytes() == b"previous output"
    assert foreign.read_bytes() == b"foreign work"
    assert set(output.parent.iterdir()) == before
