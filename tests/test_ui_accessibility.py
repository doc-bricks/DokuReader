from __future__ import annotations

import os
import sys
import tempfile
import tkinter as tk
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import DokuReader


TK_DISPLAY_AVAILABLE = (
    sys.platform.startswith("win")
    or bool(os.environ.get("DISPLAY"))
    or bool(os.environ.get("WAYLAND_DISPLAY"))
)


@unittest.skipUnless(TK_DISPLAY_AVAILABLE, "Tkinter UI-Tests brauchen eine Anzeige.")
class SearchUiAccessibilityTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        tmp_path = Path(self._tmpdir.name)
        self._original_state_file = DokuReader.STATE_FILE
        DokuReader.STATE_FILE = str(tmp_path / "state.json")

        self._first_doc = tmp_path / "Leseplan Überblick.txt"
        self._first_doc.write_text("Ärztlicher Überblick", encoding="utf-8")
        self._second_doc = tmp_path / "Paper_Markierungen.pdf"
        self._second_doc.write_bytes(b"%PDF-1.4\n%%EOF\n")

        try:
            self.app = DokuReader.App()
        except tk.TclError as exc:
            DokuReader.STATE_FILE = self._original_state_file
            self._tmpdir.cleanup()
            self.skipTest(f"Tkinter ist in dieser Umgebung nicht stabil verfügbar: {exc}")
        self.app.withdraw()
        self.app.state_model.topics = {
            "Forschung": [
                {"path": str(self._first_doc), "read": False},
                {"path": str(self._second_doc), "read": True},
            ]
        }
        self.app.state_model.current_topic = "Forschung"
        self.app._reload_topics()
        self.app._select_topic("Forschung")
        self.app.update()
        self.app.update_idletasks()

    def tearDown(self) -> None:
        self.app.destroy()
        DokuReader.STATE_FILE = self._original_state_file
        self._tmpdir.cleanup()

    def test_clear_search_button_is_labeled_and_disabled_without_query(self):
        self.assertEqual(self.app.app_title_label.cget("text"), "DokuReader")
        self.assertIn("Lokale Dokumentbibliothek", self.app.app_subtitle_label.cget("text"))
        self.assertEqual(self.app.clear_search_button.cget("text"), "Leeren")
        self.assertIn("disabled", self.app.clear_search_button.state())
        self.assertEqual(len(self.app.doc_tree.get_children()), 2)

    def test_escape_clears_search_and_restores_full_document_list(self):
        self.app._search_var.set("leseplan")
        self.app.update()
        self.app.update_idletasks()

        self.assertEqual(len(self.app.doc_tree.get_children()), 1)
        self.assertNotIn("disabled", self.app.clear_search_button.state())
        self.assertTrue(self.app.search_entry.bind("<Escape>"))

        result = self.app.clear_search()
        self.app.update()
        self.app.update_idletasks()

        self.assertEqual(result, "break")
        self.assertEqual(self.app._search_var.get(), "")
        self.assertIn("disabled", self.app.clear_search_button.state())
        self.assertEqual(len(self.app.doc_tree.get_children()), 2)

    def test_doc_actions_button_and_keyboard_menu_are_available(self):
        self.assertEqual(self.app.doc_actions_button.cget("text"), "Aktionen…")
        self.assertIn("disabled", self.app.doc_actions_button.state())
        self.assertTrue(self.app.doc_tree.bind("<Shift-F10>"))
        self.assertTrue(self.app.doc_tree.bind("<Menu>"))

        popup_calls: list[tuple[int, int]] = []
        original_popup = self.app.doc_menu.tk_popup
        self.app.doc_menu.tk_popup = lambda x, y: popup_calls.append((x, y))
        self.addCleanup(setattr, self.app.doc_menu, "tk_popup", original_popup)

        self.app.doc_tree.selection_set(str(self._first_doc))
        self.app.on_doc_select()
        self.app.update()
        self.app.update_idletasks()

        self.assertNotIn("disabled", self.app.doc_actions_button.state())
        result = self.app.open_selected_doc_menu()

        self.assertEqual(result, "break")
        self.assertEqual(len(popup_calls), 1)
        self.assertGreaterEqual(popup_calls[0][0], self.app.doc_tree.winfo_rootx())
        self.assertGreaterEqual(popup_calls[0][1], self.app.doc_tree.winfo_rooty())


if __name__ == "__main__":
    unittest.main()
