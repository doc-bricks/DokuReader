import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import DokuReader as app
from DokuReader import (
    LIBRARY_EXPORT_SCHEMA,
    build_library_export_payload,
    write_library_export,
)


class LibraryExportTests(unittest.TestCase):
    def test_build_library_export_payload_collects_metadata(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            existing = tmp_path / "Ärztebrief.txt"
            existing.write_text("Befund", encoding="utf-8")
            os.utime(existing, (1_715_000_000, 1_715_000_000))
            missing = tmp_path / "fehlt.pdf"

            payload = build_library_export_payload(
                {
                    "Ärzte": [
                        {"path": str(existing), "read": True},
                        {"path": str(missing), "read": False},
                    ]
                },
                current_topic="Ärzte",
            )

        self.assertEqual(payload["schema_version"], LIBRARY_EXPORT_SCHEMA)
        self.assertEqual(payload["current_topic"], "Ärzte")
        self.assertEqual(payload["totals"]["topic_count"], 1)
        self.assertEqual(payload["totals"]["document_count"], 2)
        self.assertEqual(payload["totals"]["missing_documents"], 1)

        topic = payload["topics"][0]
        self.assertEqual(topic["name"], "Ärzte")
        self.assertEqual(topic["document_count"], 2)

        records = {record["filename"]: record for record in topic["documents"]}
        present = records["Ärztebrief.txt"]
        self.assertEqual(present["extension"], ".txt")
        self.assertTrue(present["read"])
        self.assertEqual(present["size_bytes"], len("Befund".encode("utf-8")))
        self.assertEqual(present["mtime"], "2024-05-06T12:53:20Z")
        self.assertFalse(present["missing"])

        absent = records["fehlt.pdf"]
        self.assertFalse(absent["read"])
        self.assertIsNone(absent["size_bytes"])
        self.assertIsNone(absent["mtime"])
        self.assertTrue(absent["missing"])

    def test_write_library_export_uses_utf8_without_ascii_escaping(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = Path(tmpdir) / "dokureader-library-v1.json"
            payload = build_library_export_payload({"Überblick": []}, current_topic="Überblick")
            write_library_export(out_path, payload)

            raw_text = out_path.read_text(encoding="utf-8")
            loaded = json.loads(raw_text)

        self.assertIn("Überblick", raw_text)
        self.assertEqual(loaded["current_topic"], "Überblick")
        self.assertEqual(loaded["topics"][0]["name"], "Überblick")


class StateLoadRobustnessTests(unittest.TestCase):
    def test_state_load_tolerates_null_topics(self):
        """Bug #1: topics=null im State-File darf nicht zu AttributeError führen."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = Path(tmpdir) / "state.json"
            state_path.write_text(
                json.dumps({"topics": None, "current_topic": 42}),
                encoding="utf-8",
            )
            original = app.STATE_FILE
            app.STATE_FILE = str(state_path)
            try:
                s = app.State()
                s.load()
            finally:
                app.STATE_FILE = original
        self.assertIsInstance(s.topics, dict)
        self.assertIsNone(s.current_topic)

    def test_state_load_tolerates_list_topics(self):
        """Bug #1: topics=[] im State-File (korrupter Typ) soll {} ergeben."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = Path(tmpdir) / "state.json"
            state_path.write_text(
                json.dumps({"topics": ["eins", "zwei"]}),
                encoding="utf-8",
            )
            original = app.STATE_FILE
            app.STATE_FILE = str(state_path)
            try:
                s = app.State()
                s.load()
            finally:
                app.STATE_FILE = original
        self.assertIsInstance(s.topics, dict)


class MergePDFTests(unittest.TestCase):
    def test_merge_pdfs_closes_writer_on_write_failure(self):
        """Bug #2: writer.close() muss auch bei Schreibfehler aufgerufen werden."""
        mock_writer = MagicMock()
        mock_writer.write.side_effect = OSError("disk full")

        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = Path(tmpdir) / "out.pdf"
            with patch.object(app, "_PdfWriter", return_value=mock_writer):
                result = app.App._merge_pdfs(None, [], out_path)

        self.assertFalse(result)
        mock_writer.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
