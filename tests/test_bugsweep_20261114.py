"""Regressionstests — Bugsweep DokuReader 2026-11-14."""

from types import SimpleNamespace
from unittest.mock import Mock

from pypdf import PdfReader, PdfWriter

import DokuReader as app


def write_pdf(path, width, password=None):
    writer = PdfWriter()
    writer.add_blank_page(width=width, height=200)
    if password:
        writer.encrypt(user_password=password, owner_password=password)
    with path.open("wb") as stream:
        writer.write(stream)
    writer.close()


def test_protected_pdf_is_skipped_instead_of_failing_the_whole_collection(tmp_path, monkeypatch):
    """Eine einzige passwortgeschützte PDF ließ das ganze Sammel-PDF scheitern (ohne Hinweis, welche)."""
    normal = tmp_path / "normal.pdf"
    protected = tmp_path / "geschuetzt.pdf"
    broken = tmp_path / "kaputt.pdf"
    write_pdf(normal, 111)
    write_pdf(protected, 222, password="geheim")
    broken.write_bytes(b"%PDF-1.4 kein echtes PDF")
    state = app.State()
    state.topics = {"Topic": [{"path": str(p), "read": False} for p in (normal, protected, broken)]}
    monkeypatch.setattr(app, "desktop_path", lambda: tmp_path)
    warning = Mock()
    monkeypatch.setattr(app.messagebox, "showwarning", warning)
    status = Mock()
    window = SimpleNamespace(
        state_model=state, _set_busy=Mock(), status_info=status,
        _merge_pdfs=lambda parts, output, **kwargs: app.App._merge_pdfs(None, parts, output, **kwargs),
        after=lambda delay, callback: callback(),
    )

    app.App._create_collection_pdf_worker(window, "Topic", "alle")

    status.assert_not_called()  # kein „Konnte Sammel-PDF nicht vollständig erstellen“
    with (tmp_path / "Topic_alle.pdf").open("rb") as stream:
        widths = [float(page.mediabox.width) for page in PdfReader(stream).pages]
    assert widths == [111]
    message = warning.call_args.args[1]
    assert "Enthalten: 1 von 3" in message
    assert str(protected) in message and str(broken) in message
    assert "Passwortgeschützt" in message


def test_state_save_syncs_data_before_replacing_the_library(tmp_path, monkeypatch):
    """Bibliothek wurde ohne fsync ersetzt: nach Stromausfall drohte eine leere/kaputte Datei.

    Export, Sammel-PDF und LibreOffice-Ergebnis synchronisieren bereits vor dem Ersetzen.
    """
    import os

    monkeypatch.setattr(app, "STATE_FILE", str(tmp_path / "state.json"))
    events = []
    real_fsync, real_replace = os.fsync, os.replace
    monkeypatch.setattr(app.os, "fsync", lambda fd: (events.append("fsync"), real_fsync(fd))[1])
    monkeypatch.setattr(app.os, "replace", lambda a, b: (events.append("replace"), real_replace(a, b))[1])
    state = app.State()
    state.topics = {"Bücher": [{"path": "C:/a.pdf", "read": True}]}
    assert state.save() is True
    assert events == ["fsync", "replace"]


def test_windows_text_encodings_are_read_correctly(tmp_path):
    """ANSI-€/„“, UTF-16 („Unicode“ im alten Editor) und UTF-8-BOM erschienen als Zeichensalat."""
    text = "Rechnung „Müller“ – 5 €\nZeile 2"
    cases = {
        "ansi.txt": text.encode("cp1252"),
        "utf16.txt": text.encode("utf-16"),
        "utf8bom.txt": text.encode("utf-8-sig"),
        "utf8.txt": text.encode("utf-8"),
    }
    for name, data in cases.items():
        (tmp_path / name).write_bytes(data)
        assert app.read_text_with_fallback(str(tmp_path / name)) == text, name
    # Nicht-Text bleibt lesbar ohne Absturz (latin-1 nimmt jedes Byte).
    (tmp_path / "binary.txt").write_bytes(bytes(range(256)))
    assert app.read_text_with_fallback(str(tmp_path / "binary.txt")) is not None


def test_pdf_preview_falls_back_to_pymupdf_without_poppler(tmp_path, monkeypatch):
    """pdf2image ohne Poppler (Windows-Normalfall) wirft PDFInfoNotInstalledError (kein OSError):
    die Vorschau brach ab, bevor der PyMuPDF-Fallback lief."""
    import pytest

    if not (app.PDF2IMG_AVAILABLE and app.PYMUPDF_AVAILABLE and app.PIL_AVAILABLE):
        pytest.skip("pdf2image, PyMuPDF und Pillow nötig")
    from pdf2image.exceptions import PDFInfoNotInstalledError

    def no_poppler(*_args, **_kwargs):
        raise PDFInfoNotInstalledError("Unable to get page count. Is poppler installed and in PATH?")

    monkeypatch.setattr(app, "convert_from_path", no_poppler)
    monkeypatch.setattr(app.ImageTk, "PhotoImage", lambda img: ("photo", img.size))
    pdf = tmp_path / "vertrag.pdf"
    write_pdf(pdf, 300)
    preview = Mock()
    preview.winfo_width.return_value = 600
    preview.winfo_height.return_value = 320
    states = []
    window = SimpleNamespace(
        preview=preview, _theme={"muted": "#777"}, _preview_img=None,
        _set_preview_text=Mock(), _set_preview_state=states.append,
    )

    app.App.show_preview(window, str(pdf))

    preview.create_image.assert_called_once()
    assert states == ["PDF-Vorschau geladen: vertrag.pdf"]


def test_logging_prunes_old_per_process_logs(tmp_path, monkeypatch):
    """Jeder Start schrieb eine neue app-<PID>.log; alte wurden nie entfernt (unbegrenzt viele Dateien)."""
    import logging
    import os
    import time

    from runtime import app_logging

    # tmp_path liegt hier im Projekt (--basetemp=.pytest_temp); log_dir würde dann bewusst
    # auf das echte LOCALAPPDATA ausweichen. Deshalb den Logordner direkt umlenken.
    logs = tmp_path / "logs"
    monkeypatch.setattr(app_logging, "log_dir", lambda app_slug=None: logs)
    logs.mkdir(parents=True)
    old_time = time.time() - 40 * 86400
    for name in ("app-111.log", "app-111.log.1", "app-222.log"):
        (logs / name).write_text("alt", encoding="utf-8")
        os.utime(logs / name, (old_time, old_time))
    (logs / "app-333.log").write_text("frisch", encoding="utf-8")
    (logs / "notizen.txt").write_text("fremd", encoding="utf-8")
    os.utime(logs / "notizen.txt", (old_time, old_time))

    root = logging.getLogger()
    before = list(root.handlers)
    try:
        target = app_logging.setup_logging(app_slug="DokuReaderTest", console=False)
    finally:
        for handler in list(root.handlers):
            if handler not in before:
                root.removeHandler(handler)
                handler.close()

    remaining = sorted(p.name for p in logs.iterdir())
    assert remaining == sorted(["app-333.log", "notizen.txt", target.name])


def test_desktop_path_uses_the_windows_known_folder(tmp_path, monkeypatch):
    """Mit OneDrive-Ordnersicherung ist der echte Desktop …\\OneDrive\\Desktop; Path.home()/Desktop
    ist dann ein alter, unsichtbarer Ordner — das Sammel-PDF landete dort."""
    import pytest

    real_desktop = tmp_path / "OneDrive" / "Desktop"
    real_desktop.mkdir(parents=True)
    monkeypatch.setattr(app, "_known_desktop_folder", lambda: str(real_desktop), raising=False)
    if not hasattr(app, "_known_desktop_folder") or app.platform.system() != "Windows":
        pytest.skip("nur Windows")
    assert app.desktop_path() == real_desktop
    monkeypatch.setattr(app, "_known_desktop_folder", lambda: None)
    assert app.desktop_path() in {app.Path.home() / "Desktop", app.Path.home()}


def test_transparent_image_keeps_a_white_background_in_the_pdf(tmp_path):
    """Transparente PNG-Bereiche (Logos, Screenshots) wurden im Sammel-PDF schwarz."""
    import pytest

    fitz = pytest.importorskip("fitz")
    from PIL import Image

    image = Image.new("RGBA", (200, 200), (0, 0, 0, 0))
    image.paste((255, 0, 0, 255), (80, 80, 120, 120))
    image.save(tmp_path / "logo.png")
    out = app.App._image_to_pdf(object(), str(tmp_path / "logo.png"), tmp_path)
    pixmap = fitz.open(out)[0].get_pixmap()
    w, h = pixmap.width, pixmap.height
    assert pixmap.pixel(w // 2, h // 2) == (255, 0, 0)
    assert pixmap.pixel(w // 2 - int(w * 0.3), h // 2) == (255, 255, 255)


def test_text_pdf_keeps_blank_lines_and_stays_inside_the_page(tmp_path):
    """Leerzeilen verschwanden (Absätze klebten zusammen); breite Zeichen liefen über den Rand
    (Schätzung 6 pt/Zeichen) und wurden am Seitenrand abgeschnitten."""
    import pytest

    fitz = pytest.importorskip("fitz")
    if not app.REPORTLAB_AVAILABLE:
        pytest.skip("ReportLab nötig")
    source = tmp_path / "brief.txt"
    source.write_text("W" * 150 + "\n\nAbsatz zwei\n", encoding="utf-8")
    out = app.App._txt_to_pdf(object(), str(source), tmp_path)
    page = fitz.open(out)[0]
    words = page.get_text("words")  # (x0, y0, x1, y1, word, ...)
    right_edge = page.rect.width - 2 * 72 / 2.54  # 2 cm Rand
    assert max(w[2] for w in words) <= right_edge + 1, "Text läuft über den rechten Rand"
    assert sum(len(w[4]) for w in words if set(w[4]) == {"W"}) == 150, "Zeichen abgeschnitten"
    w_lines = sorted({round(w[1]) for w in words if set(w[4]) == {"W"}})
    absatz_y = min(w[1] for w in words if w[4] == "Absatz")
    assert absatz_y - w_lines[-1] >= 2 * 12 - 1, "Leerzeile zwischen den Absätzen fehlt"


def test_current_topic_is_highlighted_so_rename_works_right_after_adding(tmp_path, monkeypatch):
    """Das aktuelle Thema wurde nie in der Liste markiert: direkt nach „Neues Thema“ (oder nach dem
    Start) blieben „Umbenennen“/„Löschen“ ohne Wirkung, weil sie die Listenauswahl lesen."""
    import os
    import sys

    import pytest

    if not (sys.platform.startswith("win") or os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")):
        pytest.skip("Tk UI requires a display")
    monkeypatch.setattr(app, "STATE_FILE", str(tmp_path / "state.json"))
    monkeypatch.setattr(app.messagebox, "showinfo", Mock())
    monkeypatch.setattr(app.messagebox, "showerror", Mock())
    answers = iter(["Neu", "Umbenannt"])
    monkeypatch.setattr(app.simpledialog, "askstring", lambda *a, **k: next(answers))
    try:
        ui = app.App()
    except (app.tk.TclError, RuntimeError) as exc:
        pytest.skip(f"Tk nicht verfügbar: {exc}")
    try:
        ui.withdraw()
        ui.state_model.topics = {"Alt": []}
        ui._reload_topics()
        ui.add_topic()  # wird aktuelles Thema
        assert [ui.topic_list.get(i) for i in ui.topic_list.curselection()] == ["Neu"]
        ui.rename_topic()
        assert "Umbenannt" in ui.state_model.topics and "Neu" not in ui.state_model.topics
        assert [ui.topic_list.get(i) for i in ui.topic_list.curselection()] == ["Umbenannt"]
    finally:
        ui.destroy()


def test_pdf_part_problem_names_the_reason(tmp_path):
    normal = tmp_path / "ok.pdf"
    protected = tmp_path / "pw.pdf"
    write_pdf(normal, 100)
    write_pdf(protected, 100, password="x")
    assert app.pdf_part_problem(str(normal)) is None
    assert "Passwortgeschützt" in app.pdf_part_problem(str(protected))
    assert app.pdf_part_problem(str(tmp_path / "verschoben.pdf")) == "Datei fehlt"
