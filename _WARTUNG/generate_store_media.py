from __future__ import annotations

import json
import sys
import tempfile
import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageGrab

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import DokuReader as doku  # noqa: E402


SCREENSHOTS = (
    ("library-overview.png", "Themenbibliothek mit Lesestatus und Textvorschau"),
    ("pdf-preview.png", "PDF-Vorschau eines Beispieldokuments in der lokalen Bibliothek"),
    ("collection-export.png", "Themenansicht mit Sammel-PDF- und JSON-Export-Bereich"),
)

STORE_ASSETS = {
    "Square44x44Logo.png": (44, 44),
    "Square150x150Logo.png": (150, 150),
    "Wide310x150Logo.png": (310, 150),
    "Square310x310Logo.png": (310, 310),
}

BACKGROUND = (242, 246, 249, 255)
ACCENT = (47, 92, 142, 255)


def _minimal_pdf_bytes(title: str) -> bytes:
    safe_title = title.encode("latin-1", errors="replace").decode("latin-1")
    lines = [
        "%PDF-1.4",
        "1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj",
        "2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj",
        "3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R /Resources << >> >> endobj",
        f"4 0 obj << /Length 59 >> stream\nBT /F1 18 Tf 72 760 Td ({safe_title}) Tj ET\nendstream endobj",
        "xref",
        "0 5",
        "0000000000 65535 f ",
        "0000000010 00000 n ",
        "0000000063 00000 n ",
        "0000000122 00000 n ",
        "0000000230 00000 n ",
        "trailer << /Root 1 0 R /Size 5 >>",
        "startxref",
        "331",
        "%%EOF",
    ]
    return "\n".join(lines).encode("latin-1")


def create_demo_library(base_dir: Path) -> dict[str, list[dict]]:
    base_dir.mkdir(parents=True, exist_ok=True)

    txt_path = base_dir / "Leseplan_Überblick.txt"
    txt_path.write_text(
        "Forschung\n- Paper sortieren\n- Arztbriefe lesen\n- Export als JSON prüfen\n",
        encoding="utf-8",
    )

    admin_path = base_dir / "Ablagehinweise.txt"
    admin_path.write_text(
        "Verwaltung\n- Kontoauszüge prüfen\n- Unterlagen thematisch bündeln\n",
        encoding="utf-8",
    )

    pdf_path = base_dir / "Paper_Markierungen.pdf"
    pdf_path.write_bytes(_minimal_pdf_bytes("DokuReader Demo PDF"))

    image_path = base_dir / "Ablageplan.png"
    image = Image.new("RGB", (1280, 720), (248, 250, 252))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((70, 90, 1210, 640), radius=36, fill=(255, 255, 255), outline=(214, 223, 235), width=4)
    draw.text((130, 150), "DokuReader", fill=(28, 47, 74))
    draw.text((130, 220), "Ablageplan Verwaltung / Forschung / Privat", fill=(66, 88, 114))
    draw.rounded_rectangle((130, 300, 470, 520), radius=24, fill=(231, 240, 249), outline=ACCENT, width=3)
    draw.rounded_rectangle((510, 300, 850, 520), radius=24, fill=(235, 244, 235), outline=(72, 133, 88), width=3)
    draw.rounded_rectangle((890, 300, 1150, 520), radius=24, fill=(249, 240, 228), outline=(170, 113, 51), width=3)
    draw.text((170, 380), "Forschung", fill=(28, 47, 74))
    draw.text((565, 380), "Verwaltung", fill=(44, 89, 58))
    draw.text((955, 380), "Privat", fill=(133, 84, 29))
    image.save(image_path, "PNG")

    missing_path = base_dir / "Fehlt_noch.pdf"

    return {
        "Forschung": [
            {"path": str(pdf_path), "read": True},
            {"path": str(txt_path), "read": False},
            {"path": str(missing_path), "read": False},
        ],
        "Verwaltung": [
            {"path": str(image_path), "read": True},
            {"path": str(admin_path), "read": False},
        ],
    }


def wait_for_ui(app: doku.App, pause: float = 0.35) -> None:
    app.update_idletasks()
    app.update()
    time.sleep(pause)
    app.update_idletasks()
    app.update()


def select_topic(app: doku.App, topic: str) -> None:
    items = list(app.topic_list.get(0, "end"))
    index = items.index(topic)
    app.topic_list.selection_clear(0, "end")
    app.topic_list.selection_set(index)
    app.topic_list.activate(index)
    app._select_topic(topic)
    wait_for_ui(app)


def select_document(app: doku.App, topic: str, path: str) -> None:
    select_topic(app, topic)
    app.doc_tree.selection_set(path)
    app.doc_tree.focus(path)
    app.show_preview(path)
    wait_for_ui(app, pause=0.45)


def capture_window(app: doku.App, target: Path) -> None:
    app.lift()
    app.attributes("-topmost", True)
    wait_for_ui(app, pause=0.35)
    left = app.winfo_rootx()
    top = app.winfo_rooty()
    right = left + app.winfo_width()
    bottom = top + app.winfo_height()
    image = ImageGrab.grab(bbox=(left, top, right, bottom))
    app.attributes("-topmost", False)
    target.parent.mkdir(parents=True, exist_ok=True)
    image.save(target, "PNG")


def write_screenshot_manifest(output_dir: Path) -> None:
    lines = ["# Store-Screenshots", ""]
    for filename, caption in SCREENSHOTS:
        lines.append(f"- `{filename}` - {caption}")
    (output_dir / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_asset_manifest(output_dir: Path) -> None:
    lines = ["# Store-Assets", ""]
    for filename, size in STORE_ASSETS.items():
        lines.append(f"- `{filename}` - {size[0]}x{size[1]}")
    (output_dir / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def generate_store_assets(output_dir: Path | None = None) -> list[Path]:
    output_dir = output_dir or (PROJECT_ROOT / "store_assets")
    output_dir.mkdir(parents=True, exist_ok=True)

    icon = Image.open(PROJECT_ROOT / "DokuReader.ico").convert("RGBA")
    generated: list[Path] = []
    for filename, size in STORE_ASSETS.items():
        canvas = Image.new("RGBA", size, BACKGROUND)
        accent = Image.new("RGBA", size, (0, 0, 0, 0))
        accent_draw = ImageDraw.Draw(accent)
        margin_x = max(4, size[0] // 18)
        margin_y = max(4, size[1] // 18)
        accent_draw.rounded_rectangle(
            (margin_x, margin_y, size[0] - margin_x, size[1] - margin_y),
            radius=max(10, min(size) // 8),
            outline=ACCENT,
            width=max(2, min(size) // 28),
        )
        canvas.alpha_composite(accent)

        thumbnail = icon.copy()
        max_width = int(size[0] * 0.62)
        max_height = int(size[1] * 0.62)
        thumbnail.thumbnail((max_width, max_height), Image.LANCZOS)
        x = (size[0] - thumbnail.width) // 2
        y = (size[1] - thumbnail.height) // 2
        canvas.alpha_composite(thumbnail, (x, y))

        target = output_dir / filename
        canvas.save(target, "PNG")
        generated.append(target)

    write_asset_manifest(output_dir)
    return generated


def generate_store_screenshots(output_dir: Path | None = None) -> list[Path]:
    output_dir = output_dir or (PROJECT_ROOT / "releases" / "windowsstore" / "screenshots")
    output_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="dokureader-store-") as temp_dir:
        temp_path = Path(temp_dir)
        doku.STATE_FILE = str(temp_path / "demo_state.json")
        topics = create_demo_library(temp_path / "demo_docs")

        app = doku.App()
        app.title("DokuReader - Windows Store Vorschau")
        app.geometry("1580x980+30+30")
        app.state_model.topics = topics
        app.state_model.current_topic = None
        app._reload_topics()
        wait_for_ui(app, pause=0.55)

        targets: list[Path] = []
        try:
            text_path = topics["Forschung"][1]["path"]
            select_document(app, "Forschung", text_path)
            first = output_dir / SCREENSHOTS[0][0]
            capture_window(app, first)
            targets.append(first)

            pdf_path = topics["Forschung"][0]["path"]
            select_document(app, "Forschung", pdf_path)
            second = output_dir / SCREENSHOTS[1][0]
            capture_window(app, second)
            targets.append(second)

            image_path = topics["Verwaltung"][0]["path"]
            select_document(app, "Verwaltung", image_path)
            app.filter_var.set("gelesene")
            wait_for_ui(app)
            third = output_dir / SCREENSHOTS[2][0]
            capture_window(app, third)
            targets.append(third)
        finally:
            app.destroy()

    readme_main = PROJECT_ROOT / "README" / "screenshots" / "main.png"
    readme_main.parent.mkdir(parents=True, exist_ok=True)
    readme_main.write_bytes((output_dir / SCREENSHOTS[0][0]).read_bytes())
    write_screenshot_manifest(output_dir)
    return targets


def main() -> int:
    screenshots = generate_store_screenshots()
    assets = generate_store_assets()
    print(json.dumps({"screenshots": [str(path) for path in screenshots], "assets": [str(path) for path in assets]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
