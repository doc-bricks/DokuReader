"""Capture a synthetic, local-only visual smoke for the metadata-first UI.

This is a visual layout/state check, not a screen-reader acceptance test.  It
uses a temporary state file and a synthetic text document, then records three
PNG states plus a machine-readable receipt.
"""

from __future__ import annotations

import hashlib
import json
import platform
import sys
import tempfile
import ctypes
from ctypes import wintypes
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

from PIL import Image, ImageGrab


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import DokuReader  # noqa: E402


OUTPUT_DIR = ROOT / "README" / "screenshots"
RECEIPT = ROOT / "UI_POLISH_SMOKE.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _print_window(app: DokuReader.App) -> Image.Image:
    """Render the Tk toplevel through Win32 when desktop grabbing is blocked."""
    if not sys.platform.startswith("win"):
        raise OSError("PrintWindow fallback is available on Windows only")

    user32 = ctypes.windll.user32
    gdi32 = ctypes.windll.gdi32
    hwnd = int(app.winfo_id())
    while True:
        parent = int(user32.GetParent(hwnd))
        if not parent:
            break
        hwnd = parent

    rect = wintypes.RECT()
    if not user32.GetWindowRect(hwnd, ctypes.byref(rect)):
        raise OSError("GetWindowRect failed")
    width = rect.right - rect.left
    height = rect.bottom - rect.top
    window_dc = user32.GetWindowDC(hwnd)
    memory_dc = gdi32.CreateCompatibleDC(window_dc)
    bitmap = gdi32.CreateCompatibleBitmap(window_dc, width, height)
    previous = gdi32.SelectObject(memory_dc, bitmap)

    class BitmapInfoHeader(ctypes.Structure):
        _fields_ = [
            ("biSize", wintypes.DWORD),
            ("biWidth", wintypes.LONG),
            ("biHeight", wintypes.LONG),
            ("biPlanes", wintypes.WORD),
            ("biBitCount", wintypes.WORD),
            ("biCompression", wintypes.DWORD),
            ("biSizeImage", wintypes.DWORD),
            ("biXPelsPerMeter", wintypes.LONG),
            ("biYPelsPerMeter", wintypes.LONG),
            ("biClrUsed", wintypes.DWORD),
            ("biClrImportant", wintypes.DWORD),
        ]

    class BitmapInfo(ctypes.Structure):
        _fields_ = [
            ("bmiHeader", BitmapInfoHeader),
            ("bmiColors", wintypes.DWORD * 3),
        ]

    try:
        if not user32.PrintWindow(hwnd, memory_dc, 2):
            raise OSError("PrintWindow failed")
        info = BitmapInfo()
        info.bmiHeader.biSize = ctypes.sizeof(BitmapInfoHeader)
        info.bmiHeader.biWidth = width
        info.bmiHeader.biHeight = -height
        info.bmiHeader.biPlanes = 1
        info.bmiHeader.biBitCount = 32
        info.bmiHeader.biCompression = 0
        buffer = (ctypes.c_ubyte * (width * height * 4))()
        rows = gdi32.GetDIBits(
            memory_dc,
            bitmap,
            0,
            height,
            buffer,
            ctypes.byref(info),
            0,
        )
        if rows != height:
            raise OSError(f"GetDIBits returned {rows} of {height} rows")
        return Image.frombuffer(
            "RGB",
            (width, height),
            bytes(buffer),
            "raw",
            "BGRX",
            0,
            1,
        )
    finally:
        gdi32.SelectObject(memory_dc, previous)
        gdi32.DeleteObject(bitmap)
        gdi32.DeleteDC(memory_dc)
        user32.ReleaseDC(hwnd, window_dc)


def capture(app: DokuReader.App, filename: str) -> dict[str, object]:
    app.deiconify()
    app.lift()
    app.attributes("-topmost", True)
    app.update_idletasks()
    app.update()
    app.attributes("-topmost", False)
    left = app.winfo_rootx()
    top = app.winfo_rooty()
    width = app.winfo_width()
    height = app.winfo_height()
    target = OUTPUT_DIR / filename
    method = "ImageGrab"
    try:
        image = ImageGrab.grab(
            bbox=(left, top, left + width, top + height),
            all_screens=True,
        )
    except OSError:
        image = _print_window(app)
        method = "Win32 PrintWindow"
    image.save(target, format="PNG", optimize=True)
    return {
        "path": f"README/screenshots/{filename}",
        "width": image.width,
        "height": image.height,
        "bytes": target.stat().st_size,
        "sha256": sha256(target),
        "capture_method": method,
    }


def build_app() -> DokuReader.App:
    last_error: Exception | None = None
    for _attempt in range(3):
        try:
            return DokuReader.App()
        except Exception as exc:  # bounded diagnostic retry; re-raised below
            last_error = exc
    raise RuntimeError("Tk UI failed after three initialization attempts") from last_error


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    original_state_file = DokuReader.STATE_FILE
    states: dict[str, object] = {}

    with tempfile.TemporaryDirectory(prefix="dokureader-ui-smoke-") as temporary:
        temp = Path(temporary)
        DokuReader.STATE_FILE = str(temp / "state.json")
        document = temp / "Beispielnotiz.txt"
        document.write_text(
            "DokuReader Visual-Smoke\n\n"
            "Dieser synthetische Text prüft Vorschau, Status und Lesbarkeit.",
            encoding="utf-8",
        )
        app = build_app()
        try:
            app.geometry("1400x840+60+60")
            app.state_model.topics = {}
            app.state_model.current_topic = None
            app._reload_topics()
            app._reload_docs()
            app.clear_preview()
            app.update_idletasks()
            states["empty"] = {
                "document_state": app.doc_state_label.cget("text"),
                "preview_state": app.preview_state_label.cget("text"),
                "screenshot": capture(app, "ui-polish-empty.png"),
            }

            app.on_drop(SimpleNamespace(data=str(document)))
            app.update_idletasks()
            states["drag_drop_without_topic"] = {
                "document_state": app.doc_state_label.cget("text"),
                "screenshot": capture(app, "ui-polish-drag-drop.png"),
            }

            app.state_model.topics = {
                "Visual-Smoke": [{"path": str(document), "read": False}]
            }
            app.state_model.current_topic = "Visual-Smoke"
            app._reload_topics()
            app._select_topic("Visual-Smoke")
            app.show_preview(str(document))
            app.update_idletasks()
            states["text_preview"] = {
                "document_state": app.doc_state_label.cget("text"),
                "preview_state": app.preview_state_label.cget("text"),
                "preview_read_only": app.preview_text.cget("state") == "disabled",
                "screenshot": capture(app, "main.png"),
            }
            window_right = app.winfo_rootx() + app.winfo_width()
            window_bottom = app.winfo_rooty() + app.winfo_height()
            layout_bounds = {
                "delete_topic_button_inside_window": (
                    app.delete_topic_button.winfo_rootx()
                    + app.delete_topic_button.winfo_width()
                    <= window_right
                ),
                "library_export_button_inside_window": (
                    app.library_export_button.winfo_rooty()
                    + app.library_export_button.winfo_height()
                    <= window_bottom
                ),
                "library_export_frame_mapped": bool(
                    app.library_export_button.winfo_ismapped()
                ),
            }
            registry = {
                "entries": len(app._a11y_registry),
                "names_nonempty": all(
                    bool(item.get("name")) for item in app._a11y_registry.values()
                ),
                "descriptions_nonempty": all(
                    bool(item.get("description"))
                    for item in app._a11y_registry.values()
                ),
            }
        finally:
            app.destroy()
            DokuReader.STATE_FILE = original_state_file

    receipt = {
        "schema": "dokureader-ui-polish-smoke-v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "environment": {
            "platform": platform.platform(),
            "python": platform.python_version(),
            "tk": str(DokuReader.tk.TkVersion),
            "pillow": __import__("PIL").__version__,
        },
        "source": {
            "DokuReader.py": sha256(ROOT / "DokuReader.py"),
            "tests/test_ui_accessibility.py": sha256(
                ROOT / "tests" / "test_ui_accessibility.py"
            ),
            "_WARTUNG/capture_ui_polish_smoke.py": sha256(Path(__file__)),
        },
        "fixtures": "synthetic temporary state and UTF-8 text document",
        "states": states,
        "accessibility_registry": registry,
        "layout_bounds": layout_bounds,
        "claims": {
            "visual_layout_smoke": "captured for review",
            "screen_reader_acceptance": "not run",
            "keyboard_hardware_acceptance": "not run",
        },
    }
    RECEIPT.write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    if not all(layout_bounds.values()):
        raise RuntimeError(f"visual layout is clipped: {layout_bounds}")
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
