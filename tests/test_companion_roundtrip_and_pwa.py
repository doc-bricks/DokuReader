"""End-to-end tests for Desktop <-> Web/PWA Companion read-status roundtrip."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from unittest import mock

import pytest

import DokuReader


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WEB_COMPANION_DIR = PROJECT_ROOT / "web_companion"


def test_desktop_export_node_companion_toggle_and_desktop_reconcile_roundtrip(tmp_path: Path) -> None:
    """Verifies real cross-runtime roundtrip: Python export -> Node library.js setRead/serialize -> Python reconcile."""
    doc_a = tmp_path / "Ärztlicher_Befund.pdf"
    doc_b = tmp_path / "Notizen.txt"
    local_only = tmp_path / "Lokal_Behalten.txt"
    doc_a.write_bytes(b"%PDF-1.4\n%%EOF\n")
    doc_b.write_text("Ursprungstext unverändert", encoding="utf-8")
    local_only.write_text("Nur lokal", encoding="utf-8")
    original_bytes_a = doc_a.read_bytes()
    original_bytes_b = doc_b.read_bytes()

    state = DokuReader.State()
    state.topics = {
        "Medizin": [
            {"path": str(doc_a), "read": False},
            {"path": str(doc_b), "read": True},
        ],
        "Privat": [
            {"path": str(doc_a), "read": False},  # gleiches Dokument in zweitem Thema!
            {"path": str(local_only), "read": False},
        ],
    }
    state.current_topic = "Medizin"

    export_path = tmp_path / "desktop_out.json"
    payload = DokuReader.build_library_export_payload(state.topics, current_topic=state.current_topic)
    DokuReader.write_library_export(export_path, payload)

    node_exe = shutil.which("node")
    if node_exe:
        companion_out = tmp_path / "companion_out.json"
        script = (
            "import fs from 'node:fs';\n"
            "import { parseLibrary, setRead, serializeLibrary, saveLibrarySnapshot, loadLibrarySnapshot } from './library.js';\n"
            "const raw = JSON.parse(fs.readFileSync(process.argv[1], 'utf8'));\n"
            "const lib = parseLibrary(raw);\n"
            "setRead(lib, process.argv[2], true, 'Medizin');\n"
            "setRead(lib, process.argv[3], false, 'Medizin');\n"
            "const mem = new Map();\n"
            "const storage = { getItem: k => mem.get(k) ?? null, setItem: (k, v) => mem.set(k, String(v)), removeItem: k => mem.delete(k) };\n"
            "saveLibrarySnapshot(storage, lib, 'Medizin');\n"
            "const restored = loadLibrarySnapshot(storage);\n"
            "const out = serializeLibrary(restored.library);\n"
            "out.topics.push({ name: 'Fremdthema', documents: [{ path: 'C:/Fremd/Geheim.pdf', filename: 'Geheim.pdf', read: true }] });\n"
            "fs.writeFileSync(process.argv[4], JSON.stringify(out, null, 2), 'utf8');\n"
        )
        completed = subprocess.run(
            [node_exe, "--input-type=module", "-e", script, str(export_path), str(doc_a), str(doc_b), str(companion_out)],
            cwd=str(WEB_COMPANION_DIR),
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=20,
            check=True,
        )
        assert completed.returncode == 0
        reimported_payload = DokuReader.read_library_export(companion_out)
    else:
        raw = json.loads(export_path.read_text(encoding="utf-8"))
        raw["topics"][0]["documents"][0]["read"] = True
        raw["topics"][0]["documents"][1]["read"] = False
        raw["topics"].append(
            {"name": "Fremdthema", "documents": [{"path": "C:/Fremd/Geheim.pdf", "read": True}]}
        )
        reimported_payload = raw

    # Füge vor dem Reimport noch ein neues lokales Dokument hinzu — darf beim Reimport NICHT verschwinden!
    extra_local = tmp_path / "Neu_Hinzugefügt.txt"
    extra_local.write_text("Neu", encoding="utf-8")
    state.topics["Medizin"].append({"path": str(extra_local), "read": False})

    summary = state.reconcile_from_export(reimported_payload)

    assert summary == {"matched": 4, "updated": 2, "unchanged": 2, "unmatched": 1}
    medizin_by_path = {d["path"]: d["read"] for d in state.list_docs("Medizin")}
    privat_by_path = {d["path"]: d["read"] for d in state.list_docs("Privat")}

    assert medizin_by_path[str(doc_a)] is True
    assert medizin_by_path[str(doc_b)] is False
    assert medizin_by_path[str(extra_local)] is False
    # Gleiche Datei in 'Privat' blieb unangetastet!
    assert privat_by_path[str(doc_a)] is False
    assert privat_by_path[str(local_only)] is False
    assert "Fremdthema" not in state.topics
    # INV-INPLACE-03: Originaldateien bytegleich unverändert
    assert doc_a.read_bytes() == original_bytes_a
    assert doc_b.read_bytes() == original_bytes_b


def test_reconcile_matches_slash_aliases_for_absolute_paths_but_blocks_relative_cwd_confusion(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    target_doc = tmp_path / "Bericht.pdf"
    target_doc.write_bytes(b"%PDF-1.4\n%%EOF\n")

    state = DokuReader.State()
    state.topics = {"Forschung": [{"path": str(target_doc), "read": False}]}

    # 1) Relativer Dateiname darf NICHT gegen CWD aufgelöst werden
    relative_payload = {
        "schema_version": DokuReader.LIBRARY_EXPORT_SCHEMA,
        "topics": [
            {"name": "Forschung", "documents": [{"path": "Bericht.pdf", "read": True}]}
        ],
    }
    summary_rel = state.reconcile_from_export(relative_payload)
    assert summary_rel["updated"] == 0
    assert summary_rel["unmatched"] == 1
    assert state.list_docs("Forschung")[0]["read"] is False

    # 1b) Laufwerksrelativer Wurzelpfad '/Bericht.pdf' unter Windows darf NICHT gegen CWD-Laufwerk aufgelöst werden
    if os.name == "nt":
        drive_rel_payload = {
            "schema_version": DokuReader.LIBRARY_EXPORT_SCHEMA,
            "topics": [
                {"name": "Forschung", "documents": [{"path": "/Bericht.pdf", "read": True}]}
            ],
        }
        summary_drive_rel = state.reconcile_from_export(drive_rel_payload)
        assert summary_drive_rel["updated"] == 0
        assert summary_drive_rel["unmatched"] == 1
        assert state.list_docs("Forschung")[0]["read"] is False

    # 2) Absoluter Pfad mit Forward-Slashes wird sauber abgeglichen
    slash_alias = str(target_doc).replace("\\", "/")
    alias_payload = {
        "schema_version": DokuReader.LIBRARY_EXPORT_SCHEMA,
        "topics": [
            {"name": "Forschung", "documents": [{"path": slash_alias, "read": True}]}
        ],
    }
    summary_abs = state.reconcile_from_export(alias_payload)
    assert summary_abs == {"matched": 1, "updated": 1, "unchanged": 0, "unmatched": 0}
    assert state.list_docs("Forschung")[0]["read"] is True


@pytest.mark.parametrize(
    "bad_payload",
    [
        [],
        {"schema_version": "other-schema", "topics": []},
        {"topics": {}},  # internal .dokubibliothek_state.json without schema_version
        {"schema_version": "dokureader-library-v1", "topics": "not-a-list"},
        {"schema_version": "dokureader-library-v1", "current_topic": 123, "topics": []},
        {"schema_version": "dokureader-library-v1", "topics": [{"name": "", "documents": []}]},
        {
            "schema_version": "dokureader-library-v1",
            "topics": [{"name": "A", "documents": [{"path": "C:/x.pdf", "read": 1}]}],
        },
        {
            "schema_version": "dokureader-library-v1",
            "topics": [{"name": "A", "documents": [{"path": "", "read": True}]}],
        },
    ],
)
def test_reconcile_rejects_invalid_payloads_atomically(bad_payload: object) -> None:
    state = DokuReader.State()
    state.topics = {"A": [{"path": "C:/x.pdf", "read": False}]}

    with pytest.raises(ValueError):
        state.reconcile_from_export(bad_payload)  # type: ignore[arg-type]

    assert state.topics == {"A": [{"path": "C:/x.pdf", "read": False}]}


def test_read_library_export_enforces_size_limit_and_utf8(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    invalid_utf8 = tmp_path / "bad_utf8.json"
    invalid_utf8.write_bytes(b"\xff\xfe\x00\x00invalid")
    with pytest.raises(ValueError, match="UTF-8|JSON"):
        DokuReader.read_library_export(invalid_utf8)

    oversized = tmp_path / "oversized.json"
    oversized.write_text(
        json.dumps({"schema_version": DokuReader.LIBRARY_EXPORT_SCHEMA, "topics": []}),
        encoding="utf-8",
    )
    monkeypatch.setattr(DokuReader, "MAX_LIBRARY_IMPORT_BYTES", 10)
    with pytest.raises(ValueError, match="Größenlimit"):
        DokuReader.read_library_export(oversized)


def test_read_library_export_wraps_deep_nesting_recursion_error(tmp_path: Path) -> None:
    deeply_nested = tmp_path / "deep.json"
    deeply_nested.write_text("[" * 5000 + "]" * 5000, encoding="utf-8")
    with pytest.raises(ValueError, match="verschachtelt|Ungültiges"):
        DokuReader.read_library_export(deeply_nested)


@pytest.mark.skipif(
    not (
        os.name == "nt"
        or bool(os.environ.get("DISPLAY"))
        or bool(os.environ.get("WAYLAND_DISPLAY"))
    ),
    reason="Tkinter display required",
)
def test_gui_import_library_json_updates_state_and_reports_save_failures() -> None:
    import tkinter as tk

    with tempfile.TemporaryDirectory() as tmpdir_str:
        tmpdir = Path(tmpdir_str)
        original_state = DokuReader.STATE_FILE
        DokuReader.STATE_FILE = str(tmpdir / "state.json")
        doc_path = tmpdir / "Kapitel_1.txt"
        doc_path.write_text("Inhalt", encoding="utf-8")

        app = None
        for _ in range(3):
            try:
                app = DokuReader.App()
                break
            except (tk.TclError, RuntimeError):
                partial = getattr(tk, "_default_root", None)
                if partial is not None:
                    try:
                        partial.destroy()
                    except tk.TclError:
                        pass
        if app is None:
            DokuReader.STATE_FILE = original_state
            pytest.skip("Tkinter unavailable after 3 retries")

        try:
            app.withdraw()
            app.state_model.topics = {"Studium": [{"path": str(doc_path), "read": False}]}
            app.state_model.current_topic = "Studium"
            app._reload_topics()
            app._select_topic("Studium")

            assert app._a11y_registry["library_import"]["role"] == "button"
            assert app._a11y_registry["library_import"]["focusable"] is True

            import_file = tmpdir / "companion.json"
            import_file.write_text(
                json.dumps(
                    {
                        "schema_version": DokuReader.LIBRARY_EXPORT_SCHEMA,
                        "current_topic": "Studium",
                        "topics": [
                            {
                                "name": "Studium",
                                "documents": [{"path": str(doc_path), "read": True}],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            with mock.patch.object(
                DokuReader.filedialog, "askopenfilename", return_value=str(import_file)
            ), mock.patch.object(DokuReader.messagebox, "showinfo") as info_mock:
                app.library_import_button.invoke()
                info_mock.assert_called_once()
                assert "Geändert: 1" in info_mock.call_args.args[1]

            assert app.state_model.list_docs("Studium")[0]["read"] is True
            saved_disk = json.loads(Path(DokuReader.STATE_FILE).read_text(encoding="utf-8"))
            assert saved_disk["topics"]["Studium"][0]["read"] is True
            disk_before_failure = Path(DokuReader.STATE_FILE).read_bytes()

            # Negativpfad 1: os.replace wirft PermissionError beim Speichern nach Statusimport
            toggle_back_file = tmpdir / "companion_unread.json"
            toggle_back_file.write_text(
                json.dumps(
                    {
                        "schema_version": DokuReader.LIBRARY_EXPORT_SCHEMA,
                        "current_topic": "Studium",
                        "topics": [
                            {
                                "name": "Studium",
                                "documents": [{"path": str(doc_path), "read": False}],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            with mock.patch.object(
                DokuReader.filedialog, "askopenfilename", return_value=str(toggle_back_file)
            ), mock.patch.object(
                DokuReader.os, "replace", side_effect=PermissionError("disk locked")
            ), mock.patch.object(
                DokuReader.messagebox, "showerror"
            ) as err_mock, mock.patch.object(
                DokuReader.messagebox, "showinfo"
            ) as info_fail_mock:
                app.library_import_button.invoke()
                err_mock.assert_called_once()
                info_fail_mock.assert_not_called()

            # In-Memory-Änderung bleibt für Strg+S-Wiederholung erhalten, Disk bleibt unverändert!
            assert app.state_model.list_docs("Studium")[0]["read"] is False
            assert Path(DokuReader.STATE_FILE).read_bytes() == disk_before_failure
            assert "nicht gespeichert" in app.save_status_label.cget("text")

            # Negativpfad 2: load_failed=True ohne recovery_path sperrt Veröffentlichung ebenfalls sauber
            app.state_model.load_failed = True
            app.state_model.recovery_path = None
            with mock.patch.object(
                DokuReader.filedialog, "askopenfilename", return_value=str(import_file)
            ), mock.patch.object(
                DokuReader.messagebox, "showerror"
            ) as err_locked_mock, mock.patch.object(
                DokuReader.messagebox, "showinfo"
            ) as info_locked_mock:
                app.library_import_button.invoke()
                err_locked_mock.assert_called_once()
                info_locked_mock.assert_not_called()
            assert Path(DokuReader.STATE_FILE).read_bytes() == disk_before_failure
        finally:
            app.destroy()
            DokuReader.STATE_FILE = original_state
