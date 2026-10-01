"""LibreOffice failures cannot publish old, partial or invalid output."""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
import subprocess

import pytest
from pypdf import PdfWriter

import DokuReader as app


def write_pdf(path, pages=1):
    with PdfWriter() as writer:
        for _ in range(pages):
            writer.add_blank_page(width=240, height=320)
        writer.write(path)


@pytest.fixture
def isolated_backend(monkeypatch):
    monkeypatch.setattr(app.shutil, "which", lambda name: "/private/soffice" if name == "soffice" else None)
    monkeypatch.setattr(app.platform, "system", lambda: "Linux")


@pytest.mark.parametrize("kind", ["stale", "partial", "empty", "nonzero", "timeout"])
def test_failure_preserves_previous_output(tmp_path, monkeypatch, isolated_backend, kind):
    source = tmp_path / "Ärzte #brief.odt"
    source.write_bytes(b"unchanged original")
    destination = tmp_path / (source.stem + ".pdf")
    write_pdf(destination)
    previous = destination.read_bytes()

    def run(command, **kwargs):
        output = Path(command[command.index("--outdir") + 1]) / destination.name
        if kind == "partial":
            output.write_bytes(b"%PDF-1.4 incomplete")
        elif kind == "empty":
            write_pdf(output, pages=0)
        elif kind in ("nonzero", "timeout"):
            write_pdf(output)
        if kind == "timeout":
            raise subprocess.TimeoutExpired(command, 180)
        return SimpleNamespace(returncode=7 if kind == "nonzero" else 0)

    monkeypatch.setattr(app.subprocess, "run", run)
    assert app.App._office_to_pdf(None, str(source), tmp_path) is None
    assert source.read_bytes() == b"unchanged original"
    assert destination.read_bytes() == previous
    assert sorted(path.name for path in tmp_path.iterdir()) == sorted([source.name, destination.name])


def test_fresh_pdf_uses_isolated_profile_and_output(tmp_path, monkeypatch, isolated_backend):
    source = tmp_path / "Ärzte #brief.odt"
    source.write_bytes(b"unchanged original")
    destination = tmp_path / (source.stem + ".pdf")
    write_pdf(destination)
    captured = []

    def run(command, **kwargs):
        assert command[0] == "/private/soffice"
        assert kwargs["timeout"] == 180
        output_directory = Path(command[command.index("--outdir") + 1])
        assert output_directory != tmp_path
        assert output_directory.is_dir()
        profile_arg = next(arg for arg in command if arg.startswith("-env:UserInstallation="))
        profile = output_directory.parent / "profile"
        assert profile_arg == "-env:UserInstallation=" + profile.resolve().as_uri()
        assert command[-1] == str(source.resolve())
        write_pdf(output_directory / destination.name, pages=2)
        captured.append(output_directory.parent)
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(app.subprocess, "run", run)
    result = app.App._office_to_pdf(None, str(source), tmp_path)
    assert result == str(destination)
    from pypdf import PdfReader
    assert len(PdfReader(result).pages) == 2
    assert source.read_bytes() == b"unchanged original"
    assert captured and not captured[0].exists()


def test_start_error_retains_word_fallback(tmp_path, monkeypatch):
    monkeypatch.setattr(app.shutil, "which", lambda name: "/private/soffice" if name == "soffice" else None)
    monkeypatch.setattr(app.platform, "system", lambda: "Windows")
    monkeypatch.setattr(app.subprocess, "run", Mock(side_effect=OSError("cannot start")))
    word = Mock(return_value="word-result.pdf")
    monkeypatch.setattr(app, "convert_word_to_pdf", word)
    assert app.App._office_to_pdf(None, "source.docx", tmp_path) == "word-result.pdf"
    word.assert_called_once_with("source.docx", tmp_path)
    assert list(tmp_path.iterdir()) == []


def test_failed_candidate_output_cannot_leak_into_retry(tmp_path, monkeypatch, isolated_backend):
    source = tmp_path / "source.odt"
    source.write_bytes(b"original")
    destination = tmp_path / "source.pdf"
    write_pdf(destination)
    previous = destination.read_bytes()
    monkeypatch.setattr(app.shutil, "which", lambda name: "/private/" + name)
    attempts = []

    def run(command, **kwargs):
        output = Path(command[command.index("--outdir") + 1])
        profile = next(arg for arg in command if arg.startswith("-env:UserInstallation="))
        attempts.append((output, profile))
        if len(attempts) == 1:
            write_pdf(output / "source.pdf", pages=2)
            return SimpleNamespace(returncode=1)
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(app.subprocess, "run", run)
    assert app.App._office_to_pdf(None, str(source), tmp_path) is None
    assert len(attempts) == 2
    assert attempts[0][0] != attempts[1][0]
    assert attempts[0][1] != attempts[1][1]
    assert destination.read_bytes() == previous
    assert sorted(path.name for path in tmp_path.iterdir()) == ["source.odt", "source.pdf"]


@pytest.mark.parametrize("failure", ["cleanup", "publish"])
def test_finalization_failure_keeps_previous_pdf(tmp_path, monkeypatch, isolated_backend, failure):
    source = tmp_path / "source.odt"
    source.write_bytes(b"original")
    destination = tmp_path / "source.pdf"
    write_pdf(destination)
    previous = destination.read_bytes()

    def run(command, **kwargs):
        output = Path(command[command.index("--outdir") + 1]) / "source.pdf"
        write_pdf(output, pages=2)
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(app.subprocess, "run", run)
    if failure == "cleanup":
        real_temporary = app.tempfile.TemporaryDirectory

        class FailingCleanup:
            def __init__(self, *args, **kwargs):
                self.wrapped = real_temporary(*args, **kwargs)

            def __enter__(self):
                return self.wrapped.__enter__()

            def __exit__(self, *args):
                self.wrapped.__exit__(*args)
                raise OSError("profile cleanup failed")

        monkeypatch.setattr(app.tempfile, "TemporaryDirectory", FailingCleanup)
    else:
        real_replace = app.os.replace

        def fail_publish(src, dst):
            if Path(dst) == destination:
                raise OSError("destination busy")
            return real_replace(src, dst)

        monkeypatch.setattr(app.os, "replace", fail_publish)
    assert app.App._office_to_pdf(None, str(source), tmp_path) is None
    assert source.read_bytes() == b"original"
    assert destination.read_bytes() == previous
    assert sorted(path.name for path in tmp_path.iterdir()) == ["source.odt", "source.pdf"]
