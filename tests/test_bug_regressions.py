"""Regressionstests — bugfix-library-transfer 2026-06-21."""
import json
import os
import sys
import tempfile
import threading
import unittest
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
import DokuReader as app  # noqa: E402
import manage_translations as mt  # noqa: E402


class TestD3WorkstationTimeout(unittest.TestCase):
    """BUG-D3: OS open subprocess.run calls need a timeout."""

    def test_open_calls_have_timeout(self):
        src = (ROOT / "DokuReader.py").read_text(encoding="utf-8")
        for cmd in ('"open"', '"xdg-open"'):
            idx = src.find(cmd)
            self.assertGreater(idx, 0, f"{cmd} nicht in DokuReader.py gefunden")
            snippet = src[max(0, idx - 30):idx + 80]
            self.assertIn("timeout", snippet,
                          f"subprocess.run mit {cmd} ohne timeout= — BUG-D3")


class TestU2ManageTranslations(unittest.TestCase):
    """BUG-U2: manage_translations lud korrupte JSON ohne Handler."""

    def test_corrupted_json_does_not_raise(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            trans_file = os.path.join(tmpdir, "locales", "translations.json")
            os.makedirs(os.path.dirname(trans_file), exist_ok=True)
            with open(trans_file, "w", encoding="utf-8") as f:
                f.write("{corrupted json")
            try:
                mt.manage_translations(tmpdir)
            except json.JSONDecodeError:
                self.fail("JSONDecodeError nicht gefangen — BUG-U2 in manage_translations")


class TestD4SplitDndOeffnendeKlammer(unittest.TestCase):
    """BUG-D4: '{' in Dateinamen wurde als DnD-Trennzeichen fehlinterpretiert.

    tkinterdnd2 klammert nur Pfade mit Leerzeichen ein; Pfade ohne Leerzeichen
    kommen ungeklammert an — enthält der Dateiname ein literales '{', brach der
    Parser bisher den Token ab und ignorierte alles davor.
    """

    def test_dateiname_mit_oeffnender_klammer_bleibt_ein_token(self):
        result = app.App._split_dnd_paths(r"C:\Pfad\bericht{2026}.txt")
        self.assertEqual(result, [r"C:\Pfad\bericht{2026}.txt"],
                         "BUG-D4: '{' im Dateinamen zerstört den Pfad-Token")

    def test_normaler_dnd_pfad_mit_leerzeichen_weiterhin_korrekt(self):
        """Sicherstellt, dass normales DnD-Format nach dem Fix noch funktioniert."""
        result = app.App._split_dnd_paths(r"{C:\Pfad mit Leerzeichen\file.pdf}")
        self.assertEqual(result, [r"C:\Pfad mit Leerzeichen\file.pdf"])

    def test_mehrere_dnd_pfade_gemischt(self):
        result = app.App._split_dnd_paths(
            r"C:\einfach.pdf {C:\mit Leerzeichen\dok.pdf}"
        )
        self.assertEqual(result, [r"C:\einfach.pdf", r"C:\mit Leerzeichen\dok.pdf"])


class TestD5SplitDndSchliessendekKlammer(unittest.TestCase):
    """BUG-D5: '}' in Dateinamen ohne öffnende Klammer teilte den Token fälschlicherweise.

    Ein '}' außerhalb eines geklammerten Tokens schloss fälschlicherweise den
    aktuell akkumulierten Puffer und erzeugte zwei Pfade statt eines.
    """

    def test_dateiname_mit_schliessender_klammer_bleibt_ein_token(self):
        result = app.App._split_dnd_paths(r"C:\Pfad\bericht}alt.txt")
        self.assertEqual(result, [r"C:\Pfad\bericht}alt.txt"],
                         "BUG-D5: '}' im Dateinamen teilt den Pfad-Token")

    def test_klammerpaar_in_dateinamen(self):
        """'{...}' mitten in einem ungeklammerten Pfad bleibt intakt."""
        result = app.App._split_dnd_paths(r"C:\Pfad\bericht{2026}final.txt")
        self.assertEqual(result, [r"C:\Pfad\bericht{2026}final.txt"])


class TestThreadSafetyHaertung(unittest.TestCase):
    """Härtung (kein roter Vorgänger): State-Mutationen laufen jetzt unter Lock."""

    def test_state_hat_rename_topic_methode(self):
        s = app.State()
        s.ensure_topic("Alt")
        ok = s.rename_topic("Alt", "Neu")
        self.assertTrue(ok)
        self.assertIn("Neu", s.topics)
        self.assertNotIn("Alt", s.topics)

    def test_rename_topic_aktualisiert_current_topic(self):
        s = app.State()
        s.ensure_topic("Alt")
        s.current_topic = "Alt"
        s.rename_topic("Alt", "Neu")
        self.assertEqual(s.current_topic, "Neu")

    def test_rename_topic_gibt_false_bei_fehlendem_thema(self):
        s = app.State()
        ok = s.rename_topic("NichtVorhanden", "Irgendwas")
        self.assertFalse(ok)

    def test_remove_topic_entfernt_thema(self):
        s = app.State()
        s.ensure_topic("Weg")
        s.remove_topic("Weg")
        self.assertNotIn("Weg", s.topics)

    def test_remove_topic_loescht_current_topic(self):
        s = app.State()
        s.ensure_topic("Weg")
        s.current_topic = "Weg"
        s.remove_topic("Weg")
        self.assertIsNone(s.current_topic)

    def test_save_serialisiert_innerhalb_lock(self):
        """State.save() schreibt korrektes JSON und übersteht gleichzeitige Reads."""
        s = app.State()
        s.ensure_topic("Thema")
        original = app.STATE_FILE
        with tempfile.TemporaryDirectory() as tmpdir:
            app.STATE_FILE = str(Path(tmpdir) / "state.json")
            try:
                # Parallel: viele list_docs-Reads während save() läuft
                errors = []

                def _reader():
                    try:
                        for _ in range(50):
                            s.list_docs("Thema")
                    except Exception as exc:
                        errors.append(exc)

                threads = [threading.Thread(target=_reader) for _ in range(4)]
                for t in threads:
                    t.start()
                s.save()
                for t in threads:
                    t.join()
                self.assertEqual(errors, [])
                raw = Path(app.STATE_FILE).read_text(encoding="utf-8")
                data = json.loads(raw)
                self.assertIn("Thema", data.get("topics", {}))
            finally:
                app.STATE_FILE = original


if __name__ == "__main__":
    unittest.main()
