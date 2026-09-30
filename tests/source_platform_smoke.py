from __future__ import annotations

import sys
import tempfile
from pathlib import Path
from unittest import mock


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import DokuReader  # noqa: E402


class SmokeFailure(RuntimeError):
    pass


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise SmokeFailure(message)


def _preview_text(app: DokuReader.App) -> str:
    return app.preview_text.get("1.0", "end").strip()


def _fake_soffice_run(tmpdir: Path):
    def runner(cmd, stdout=None, stderr=None, timeout=None, check=None):
        target = tmpdir / (Path(cmd[-1]).stem + ".pdf")
        target.write_bytes(b"%PDF-1.4\n1 0 obj<</Type/Catalog>>endobj\ntrailer<</Root 1 0 R>>\n%%EOF\n")
        return mock.Mock(returncode=0)

    return runner


def main() -> None:
    if not DokuReader.REPORTLAB_AVAILABLE:
        raise SmokeFailure("ReportLab fehlt; Sammel-PDF-Smoke kann nicht laufen.")
    if DokuReader._PdfWriter is None:
        raise SmokeFailure("PdfWriter fehlt; Sammel-PDF-Smoke kann nicht laufen.")

    with tempfile.TemporaryDirectory() as tmpdir_str:
        tmpdir = Path(tmpdir_str)
        txt_path = tmpdir / "Ärztebrief.txt"
        txt_path.write_text("Überweisung für Ölprüfung\nNächster Schritt: Rücksprache.", encoding="utf-8")
        office_path = tmpdir / "Bericht.odt"
        office_path.write_text("LibreOffice-Ersatz für den Smoke.", encoding="utf-8")

        original_state_file = DokuReader.STATE_FILE
        DokuReader.STATE_FILE = str(tmpdir / "state.json")
        for damaged_state in (b"null", b"\xffinvalid", b'{"topics": {"Broken": [null]}}'):
            Path(DokuReader.STATE_FILE).write_bytes(damaged_state)
            with mock.patch.object(DokuReader.messagebox, "showwarning") as warning:
                startup_app = DokuReader.App()
                warning.assert_called_once()
            try:
                startup_app.update()
                _assert(startup_app.state_model.topics == {}, "Ungültige Bibliothek wurde übernommen.")
                _assert(Path(DokuReader.STATE_FILE).read_bytes() == damaged_state,
                        "Der Start hat die beschädigte Bibliotheksdatei verändert.")
                _assert(Path(startup_app.state_model.recovery_path).read_bytes() == damaged_state,
                        "Die Sicherung enthält nicht die vollständige beschädigte Bibliothek.")
            finally:
                startup_app.destroy()
        Path(DokuReader.STATE_FILE).write_text('{"topics": {}}', encoding="utf-8")
        app = DokuReader.App()
        app.update()
        app.update_idletasks()

        try:
            pdf_path_str = app._txt_to_pdf(str(txt_path), tmpdir)
            _assert(pdf_path_str is not None, "TXT->PDF-Konvertierung lieferte keine Datei.")
            pdf_path = Path(pdf_path_str)
            _assert(pdf_path.exists(), "TXT->PDF-Ausgabe fehlt.")

            app.state_model.topics = {
                "Ärzte": [
                    {"path": str(txt_path), "read": True},
                    {"path": str(pdf_path), "read": False},
                ]
            }
            app.state_model.current_topic = "Ärzte"
            app._reload_topics()
            app._select_topic("Ärzte")
            app.preview.configure(width=600, height=320)
            app.update()
            app.update_idletasks()

            app.show_preview(str(txt_path))
            app.update_idletasks()
            text_preview = _preview_text(app)
            _assert("Überweisung" in text_preview and "Ölprüfung" in text_preview, "Textvorschau enthält die erwarteten Umlaute nicht.")

            app.show_preview(str(pdf_path))
            app.update_idletasks()
            pdf_preview = _preview_text(app)
            _assert(pdf_path.name in pdf_preview, "PDF-Vorschau meldet den Dateinamen nicht.")

            app.doc_tree.selection_set(str(txt_path))
            with mock.patch.object(DokuReader.platform, "system", return_value="Darwin"), \
                 mock.patch.object(DokuReader.subprocess, "run") as open_mock:
                app.on_doc_double_click()
                open_mock.assert_called_once_with(["open", str(txt_path)], check=False, timeout=30)

            app.doc_tree.selection_set(str(txt_path))
            with mock.patch.object(DokuReader.platform, "system", return_value="Linux"), \
                 mock.patch.object(DokuReader.subprocess, "run") as xdg_mock:
                app.on_doc_double_click()
                xdg_mock.assert_called_once_with(["xdg-open", str(txt_path)], check=False, timeout=30)

            with mock.patch.object(DokuReader.shutil, "which", side_effect=lambda name: "/usr/bin/soffice" if name == "soffice" else None), \
                 mock.patch.object(DokuReader.subprocess, "run", side_effect=_fake_soffice_run(tmpdir)) as soffice_mock:
                office_pdf = app._office_to_pdf(str(office_path), tmpdir)
                _assert(office_pdf is not None, "LibreOffice-Fallback erzeugte keine PDF.")
                _assert(Path(office_pdf).exists(), "LibreOffice-Fallback-Ausgabe fehlt.")
                soffice_mock.assert_called_once()

            messages: list[tuple[str, str]] = []

            def run_after(_delay, callback=None, *args):
                if callback is not None:
                    callback(*args)
                return "after-id"

            with mock.patch.object(DokuReader, "desktop_path", return_value=tmpdir), \
                 mock.patch.object(DokuReader.messagebox, "showinfo", side_effect=lambda title, msg: messages.append((title, msg))), \
                 mock.patch.object(app, "after", side_effect=run_after):
                app._create_collection_pdf_worker("Ärzte", "alle")
                previous_pdf = (tmpdir / "Ärzte_alle.pdf").read_bytes()
                previous_successes = sum(title == "Erfolg" for title, _msg in messages)
                damaged_pdf = tmpdir / "beschädigt.pdf"
                damaged_pdf.write_bytes(b"not a PDF")
                app.state_model.topics["Ärzte"].append({"path": str(damaged_pdf), "read": False})
                app._create_collection_pdf_worker("Ärzte", "alle")
                _assert((tmpdir / "Ärzte_alle.pdf").read_bytes() == previous_pdf,
                        "Fehlgeschlagener Merge hat die vorhandene Ausgabe verändert.")
                _assert(sum(title == "Erfolg" for title, _msg in messages) == previous_successes,
                        "Fehlgeschlagener Merge hat Erfolg gemeldet.")
                app.state_model.topics["Ärzte"].pop()
                omitted_office = tmpdir / "nicht-konvertierbar.docx"
                app.state_model.topics["Ärzte"].append({"path": str(omitted_office), "read": False})
                with mock.patch.object(app, "_office_to_pdf", return_value=None), \
                     mock.patch.object(DokuReader.messagebox, "showwarning") as partial_warning:
                    app._create_collection_pdf_worker("Ärzte", "alle")
                    partial_warning.assert_called_once()
                    _assert(str(omitted_office) in partial_warning.call_args.args[1],
                            "Warnung nennt die ausgelassene Office-Datei nicht.")
                    _assert("2 von 3" in partial_warning.call_args.args[1],
                            "Warnung nennt den Umfang des Teilergebnisses nicht.")
                _assert(sum(title == "Erfolg" for title, _msg in messages) == previous_successes,
                        "Teilergebnis hat vollständigen Erfolg gemeldet.")

            merged_pdf = tmpdir / "Ärzte_alle.pdf"
            _assert(merged_pdf.exists(), "Sammel-PDF wurde nicht erzeugt.")
            _assert(any("Sammel-PDF erstellt" in msg for _title, msg in messages), "Erfolgsmeldung für Sammel-PDF fehlt.")
            json_export = tmpdir / "bibliothek.json"
            with mock.patch.object(DokuReader.filedialog, "asksaveasfilename", return_value=str(json_export)), \
                 mock.patch.object(DokuReader.messagebox, "showinfo") as export_success, \
                 mock.patch.object(DokuReader.messagebox, "showerror") as export_error:
                app.export_library_json()
                export_success.assert_called_once()
                previous_json = json_export.read_bytes()
                with mock.patch.object(DokuReader.os, "replace", side_effect=PermissionError("Zieldatei gesperrt")):
                    app.export_library_json()
                export_success.assert_called_once()
                export_error.assert_called_once()
                _assert(json_export.read_bytes() == previous_json,
                        "Fehlgeschlagener JSON-Export hat die vorherige Ausgabe verändert.")
                for protected_target in (Path(DokuReader.STATE_FILE), txt_path):
                    protected_bytes = protected_target.read_bytes()
                    with mock.patch.object(DokuReader.filedialog, "asksaveasfilename", return_value=str(protected_target)):
                        app.export_library_json()
                    _assert(protected_target.read_bytes() == protected_bytes,
                            "JSON-Export hat eine geschützte Bibliotheksdatei verändert.")
                export_success.assert_called_once()
                _assert(export_error.call_count == 3,
                        "JSON-Export hat nicht beide geschützten Ziele sichtbar abgewiesen.")
        finally:
            app.destroy()
            DokuReader.STATE_FILE = original_state_file

    print("source_platform_smoke: OK")


if __name__ == "__main__":
    main()
