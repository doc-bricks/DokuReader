"""Real LibreOffice PDF output, Unicode paths and failure preservation (no GUI)."""
from pathlib import Path
import hashlib
import shutil
import sys
import tempfile
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import DokuReader as app  # noqa: E402
from pypdf import PdfReader  # noqa: E402


def main():
    if not (shutil.which("soffice") or shutil.which("libreoffice")):
        raise RuntimeError("Real LibreOffice is required for this explicit smoke")
    with tempfile.TemporaryDirectory(prefix="dokureader-native-lo-") as temporary:
        root = Path(temporary) / "Ärzte # 100%"
        root.mkdir()
        source = root / "Überweisung.odt"
        content = '''<?xml version="1.0" encoding="UTF-8"?>
<office:document-content xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"
 xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0" office:version="1.2">
 <office:body><office:text><text:p>Überweisung zur Ölprüfung</text:p></office:text></office:body>
</office:document-content>'''
        manifest = '''<?xml version="1.0" encoding="UTF-8"?>
<manifest:manifest xmlns:manifest="urn:oasis:names:tc:opendocument:xmlns:manifest:1.0" manifest:version="1.2">
 <manifest:file-entry manifest:full-path="/" manifest:media-type="application/vnd.oasis.opendocument.text"/>
 <manifest:file-entry manifest:full-path="content.xml" manifest:media-type="text/xml"/>
</manifest:manifest>'''
        with zipfile.ZipFile(source, "w") as archive:
            archive.writestr("mimetype", "application/vnd.oasis.opendocument.text", compress_type=zipfile.ZIP_STORED)
            archive.writestr("content.xml", content)
            archive.writestr("META-INF/manifest.xml", manifest)
        before = hashlib.sha256(source.read_bytes()).hexdigest()
        result = app.App._office_to_pdf(None, str(source), root)
        assert result == str(root / "Überweisung.pdf"), "Real conversion failed"
        with open(result, "rb") as stream:
            reader = PdfReader(stream, strict=True)
            text = "\n".join(page.extract_text() for page in reader.pages)
        assert "Überweisung" in text and "Ölprüfung" in text, repr(text)
        assert hashlib.sha256(source.read_bytes()).hexdigest() == before
        output_bytes = Path(result).read_bytes()
        missing_output = root / "missing.pdf"
        missing_output.write_bytes(output_bytes)
        assert app.App._office_to_pdf(None, str(root / "missing.odt"), root) is None
        assert Path(result).read_bytes() == output_bytes
        assert missing_output.read_bytes() == output_bytes
        assert not list(root.glob(".dokureader-libreoffice-*"))
        assert sorted(path.name for path in root.iterdir()) == ["missing.pdf", "Überweisung.odt", "Überweisung.pdf"]
        print("libreoffice_native_smoke: OK (real ODT/PDF text, source bytes, Unicode/URI, cleanup, missing source with stale PDF)")


if __name__ == "__main__":
    main()
