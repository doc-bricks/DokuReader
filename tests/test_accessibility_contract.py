"""Metadata-first accessibility contract checks without requiring a Tk display."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import DokuReader


class FakeWidget:
    def __init__(self) -> None:
        self.options: dict[str, object] = {}

    def configure(self, **kwargs: object) -> None:
        self.options.update(kwargs)


def test_metadata_helper_keeps_semantic_name_role_and_focus_state() -> None:
    widget = FakeWidget()

    metadata = DokuReader.apply_accessibility_metadata(
        widget,
        name="Dokumentenliste",
        description="Dokumente des aktuellen Themas",
        role="list",
        focusable=True,
    )

    assert metadata["name"] == "Dokumentenliste"
    assert metadata["description"] == "Dokumente des aktuellen Themas"
    assert metadata["role"] == "list"
    assert metadata["contract_version"] == DokuReader.A11Y_CONTRACT_VERSION
    assert widget._dokureader_accessibility == metadata
    assert widget.accessible_name == "Dokumentenliste"
    assert widget.options["takefocus"] == "1"


def test_ui_source_contains_state_and_keyboard_contract() -> None:
    source = (Path(__file__).resolve().parents[1] / "DokuReader.py").read_text(encoding="utf-8")

    for key in (
        '"document_list"',
        '"document_state"',
        '"preview_state"',
        '"preview_text"',
        '"collection_export"',
        '"library_export"',
    ):
        assert key in source
    assert 'self.doc_tree.bind("<Return>", self.on_doc_double_click)' in source
    assert 'self.doc_tree.bind("<Shift-F10>", self.open_selected_doc_menu)' in source
    assert "Keine gültigen Dateipfade im Drag-and-drop-Ereignis erkannt." in source
    assert "self.preview_text = tk.Text(right, height=10, wrap=\"word\", state=\"disabled\")" in source
