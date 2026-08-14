#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dokumentenbibliothek mit Themen, Vorschau, Gelesen/ungelesen, Doppelklick-Öffnen
und Sammel-PDF-Export (alle/gelesene/ungelesene) mit vielen Fallbacks.

Features:
- GUI mit Tkinter (eine einzelne .py-Datei)
- Themen anlegen/umbenennen/löschen
- Dateien pro Thema verwalten (nur Verweise, Originaldateien bleiben unberührt)
- Drag & Drop hinzufügen (optional: tkinterdnd2)
- Rechtsklick: als gelesen markieren (grün + ✓), Markierung entfernen, aus Bibliothek entfernen
- Doppelklick: Datei im Standardprogramm des OS öffnen (Windows/macOS/Linux)
- Vorschau:
  * Bilder (Pillow)
  * Textdateien (UTF-8 -> Latin-1 -> Hexdump-Fallback)
  * PDF (pdf2image oder PyMuPDF; sonst Metadaten)
  * DOCX (python-docx), ODT (odfpy); sonst Metadaten
- Export Sammel-PDF auf Desktop: Thema_alle.pdf / Thema_gelesene.pdf / Thema_ungelesene.pdf
  * PDFs direkt
  * TXT/Bilder -> PDF (ReportLab und/oder Pillow)
  * DOC/DOCX/ODT/RTF -> PDF via LibreOffice (headless) oder Word COM (Windows, pywin32)
  * Merge via pypdf oder PyPDF2
- Persistenz: JSON im Home-Verzeichnis (.dokubibliothek_state.json)
"""

import os
import json
import shutil
import subprocess
import tempfile
import platform
import threading
from datetime import datetime, timezone
from pathlib import Path

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog

# Optionale Bibliotheken
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except Exception:
    PIL_AVAILABLE = False

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas as rl_canvas
    from reportlab.lib.units import cm
    from reportlab.lib.utils import ImageReader
    REPORTLAB_AVAILABLE = True
except Exception:
    REPORTLAB_AVAILABLE = False

try:
    from pypdf import PdfWriter as _PdfWriter
except Exception:
    try:
        from PyPDF2 import PdfWriter as _PdfWriter
    except Exception:
        _PdfWriter = None

# PDF-Vorschau optional
try:
    from pdf2image import convert_from_path
    PDF2IMG_AVAILABLE = True
except Exception:
    PDF2IMG_AVAILABLE = False

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except Exception:
    PYMUPDF_AVAILABLE = False

# Office-Textauszug optional
try:
    import docx
    DOCPREVIEW_AVAILABLE = True
except Exception:
    DOCPREVIEW_AVAILABLE = False

try:
    from odf import text as odf_text, teletype
    from odf.opendocument import load as odf_load
    ODFPREVIEW_AVAILABLE = True
except Exception:
    ODFPREVIEW_AVAILABLE = False

# Drag&Drop optional
try:
    import tkinterdnd2 as tkdnd
    TKDND_AVAILABLE = True
except Exception:
    TKDND_AVAILABLE = False


def read_text_with_fallback(path, max_chars=None):
    """Liest eine Textdatei mit Encoding-Fallback: UTF-8 -> Latin-1 -> Hexdump."""
    for enc in ["utf-8", "latin-1"]:
        try:
            with open(path, "r", encoding=enc) as f:
                return f.read(max_chars) if max_chars is not None else f.read()
        except (OSError, UnicodeDecodeError):
            continue
    try:
        with open(path, "rb") as f:
            return f.read(256).hex(" ")
    except OSError:
        return None


APP_NAME = "Dokumentenbibliothek"
APP_VERSION = "1.0.1-dev"
STATE_FILE = str(Path.home() / ".dokubibliothek_state.json")
LIBRARY_EXPORT_SCHEMA = "dokureader-library-v1"

SUPPORTED_EXTS = {
    ".txt", ".doc", ".docx", ".pdf", ".odt", ".rtf",
    ".jpg", ".jpeg", ".gif", ".png"
}
IMAGE_EXTS = {".jpg", ".jpeg", ".gif", ".png"}
WORD_EXTS = {".doc", ".docx", ".odt", ".rtf"}
TXT_EXTS = {".txt"}
PDF_EXTS = {".pdf"}

# Vorschau-Einstellungen
TXT_PREVIEW_CHARS = 5000
OFFICE_PREVIEW_PARAGRAPHS = 30

# Tkinter has no portable ``accessibleName`` option.  Keep the semantic
# contract next to each widget so native labels/states/focus order and future
# accessibility bridges have one authoritative source of metadata.
A11Y_CONTRACT_VERSION = "1.0"


def apply_accessibility_metadata(widget, *, name: str, description: str, role: str, focusable: bool) -> dict[str, object]:
    """Attach the metadata-first accessibility contract to a Tk widget.

    The metadata is intentionally plain Python data: Tk/ttk expose native
    text, state and keyboard focus to the platform, while this contract keeps
    the semantic name, description and role testable and bridgeable without
    pretending that a local Tk smoke is a screen-reader acceptance test.
    """
    metadata = {
        "name": name,
        "description": description,
        "role": role,
        "focusable": bool(focusable),
        "contract_version": A11Y_CONTRACT_VERSION,
    }
    setattr(widget, "_dokureader_accessibility", metadata)
    setattr(widget, "accessible_name", name)
    setattr(widget, "accessible_description", description)
    setattr(widget, "accessible_role", role)
    try:
        widget.configure(takefocus="1" if focusable else "0")
    except (AttributeError, tk.TclError):
        # Small test doubles and a few Tk platform widgets may not expose the
        # option; their semantic metadata remains useful and verifiable.
        pass
    return metadata


def human_size(num_bytes: int) -> str:
    for unit in ["B", "KB", "MB", "GB"]:
        if num_bytes < 1024:
            return f"{num_bytes:.1f} {unit}"
        num_bytes /= 1024
    return f"{num_bytes:.1f} TB"


def desktop_path() -> Path:
    p = Path.home() / "Desktop"
    return p if p.exists() else Path.home()


def isoformat_utc(timestamp: float) -> str:
    """Formatiert einen Unix-Timestamp als UTC-ISO-8601-Zeitstempel."""
    return datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat().replace("+00:00", "Z")


def build_library_document_record(doc: dict) -> dict | None:
    """Leitet aus einem State-Dokument einen exportierbaren Metadatensatz ab."""
    path = doc.get("path")
    if not isinstance(path, str) or not path:
        return None

    record = {
        "path": path,
        "filename": os.path.basename(path),
        "extension": Path(path).suffix.lower(),
        "read": bool(doc.get("read", False)),
        "size_bytes": None,
        "mtime": None,
        "missing": True,
    }
    try:
        stat_result = os.stat(path)
    except OSError:
        return record

    record["size_bytes"] = stat_result.st_size
    record["mtime"] = isoformat_utc(stat_result.st_mtime)
    record["missing"] = False
    return record


def build_library_export_payload(topics: dict[str, list[dict]], current_topic: str | None = None) -> dict:
    """Erstellt das Austauschformat `dokureader-library-v1` aus dem aktuellen State."""
    export_topics: list[dict] = []
    document_total = 0
    missing_total = 0

    for topic_name in sorted(topics.keys(), key=str.lower):
        records: list[dict] = []
        docs = topics.get(topic_name, [])
        sorted_docs = sorted(
            docs,
            key=lambda d: (
                os.path.basename(str(d.get("path", ""))).lower(),
                str(d.get("path", "")).lower(),
            ),
        )
        for doc in sorted_docs:
            record = build_library_document_record(doc)
            if record is None:
                continue
            records.append(record)
            document_total += 1
            if record["missing"]:
                missing_total += 1
        export_topics.append(
            {
                "name": topic_name,
                "document_count": len(records),
                "documents": records,
            }
        )

    return {
        "schema_version": LIBRARY_EXPORT_SCHEMA,
        "exported_at": isoformat_utc(datetime.now(tz=timezone.utc).timestamp()),
        "app_name": APP_NAME,
        "app_version": APP_VERSION,
        "current_topic": current_topic,
        "topics": export_topics,
        "totals": {
            "topic_count": len(export_topics),
            "document_count": document_total,
            "missing_documents": missing_total,
        },
    }


def write_library_export(path: str | os.PathLike[str], payload: dict) -> None:
    """Schreibt den Bibliotheksexport als UTF-8-JSON-Datei."""
    out_path = Path(path)
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


class State:
    """
    Verwaltet den Anwendungszustand (Themen, Dokumente, Gelesen-Status).

    Attributes:
        topics: dict[str, list[dict]] - Themen mit zugeordneten Dokumenten
        current_topic: str | None - Aktuell ausgewähltes Thema
    """
    def __init__(self):
        self.topics: dict[str, list[dict]] = {}
        self.current_topic: str | None = None
        self._lock = threading.Lock()

    def load(self):
        """Lädt den Zustand aus der JSON-Datei (~/.dokubibliothek_state.json)."""
        if os.path.isfile(STATE_FILE):
            try:
                with open(STATE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    loaded_topics = data.get("topics")
                    self.topics = loaded_topics if isinstance(loaded_topics, dict) else {}
                    ct = data.get("current_topic")
                    self.current_topic = ct if isinstance(ct, str) else None
            except (OSError, json.JSONDecodeError):
                # Ignorieren, falls Zustand nicht gelesen werden kann
                pass

    def save(self):
        """Speichert den aktuellen Zustand in die JSON-Datei (thread-sicher).

        Der JSON-String wird innerhalb des Locks serialisiert, damit kein anderer Thread
        self.topics mutieren kann, während json.dumps läuft.
        """
        with self._lock:
            serialized = json.dumps(
                {"topics": self.topics, "current_topic": self.current_topic},
                ensure_ascii=False,
                indent=2,
            )
        try:
            with open(STATE_FILE, "w", encoding="utf-8") as f:
                f.write(serialized)
        except (OSError, TypeError):
            pass

    def ensure_topic(self, topic: str):
        """
        Stellt sicher, dass ein Thema existiert (erstellt leere Liste falls nicht vorhanden).

        Args:
            topic: Name des Themas
        """
        with self._lock:
            if topic not in self.topics:
                self.topics[topic] = []

    def add_docs(self, topic: str, paths) -> int:
        """
        Fügt Dokumente zu einem Thema hinzu (nur unterstützte Dateitypen, keine Duplikate).

        Args:
            topic: Name des Themas
            paths: Liste von Dateipfaden

        Returns:
            Anzahl der tatsächlich hinzugefügten Dokumente
        """
        with self._lock:
            if topic not in self.topics:
                self.topics[topic] = []
            known = {d["path"] for d in self.topics[topic]}
            added = 0
            for p in paths:
                if os.path.isfile(p) and Path(p).suffix.lower() in SUPPORTED_EXTS and p not in known:
                    self.topics[topic].append({"path": p, "read": False})
                    known.add(p)
                    added += 1
            return added

    def remove_doc(self, topic: str, path: str):
        """
        Entfernt ein Dokument aus einem Thema.

        Args:
            topic: Name des Themas
            path: Pfad des zu entfernenden Dokuments
        """
        with self._lock:
            self.topics[topic] = [d for d in self.topics.get(topic, []) if d["path"] != path]

    def set_read(self, topic: str, path: str, is_read: bool):
        """
        Setzt den Gelesen-Status eines Dokuments.

        Args:
            topic: Name des Themas
            path: Pfad des Dokuments
            is_read: True = gelesen, False = ungelesen
        """
        with self._lock:
            for d in self.topics.get(topic, []):
                if d["path"] == path:
                    d["read"] = is_read

    def list_docs(self, topic: str):
        """
        Gibt eine Kopie aller Dokumente eines Themas zurück (thread-sicher).

        Args:
            topic: Name des Themas

        Returns:
            Liste von Dokumenten (dicts mit 'path' und 'read')
        """
        with self._lock:
            return list(self.topics.get(topic, []))

    def rename_topic(self, old: str, new: str) -> bool:
        """
        Benennt ein Thema atomar um (thread-sicher).

        Args:
            old: Bisheriger Themenname
            new: Neuer Themenname

        Returns:
            True bei Erfolg, False wenn old nicht existiert
        """
        with self._lock:
            if old not in self.topics:
                return False
            self.topics[new] = self.topics.pop(old)
            if self.current_topic == old:
                self.current_topic = new
            return True

    def remove_topic(self, topic: str):
        """
        Entfernt ein Thema atomar (thread-sicher).

        Args:
            topic: Name des zu entfernenden Themas
        """
        with self._lock:
            self.topics.pop(topic, None)
            if self.current_topic == topic:
                self.current_topic = None


class App(tk.Tk if not TKDND_AVAILABLE else tkdnd.Tk):
    """
    Hauptanwendung der Dokumentenbibliothek.

    Verwaltet Themen und Dokumente über eine dreispaltige GUI:
    - Links: Themenliste mit Verwaltungsbuttons
    - Mitte: Dokumentenliste (sortierbar) mit Drag-&-Drop-Unterstützung
    - Rechts: Vorschau und Sammel-PDF-Export
    """

    def __init__(self):
        """Initialisiert die App: Fenster konfigurieren, State laden, GUI aufbauen."""
        super().__init__()
        self._a11y_registry: dict[str, dict[str, object]] = {}
        self.title(APP_NAME)
        self.geometry("1200x700")
        self.minsize(1000, 600)
        self._apply_window_icon()
        self._theme = self._build_theme()
        self.configure(bg=self._theme["window_bg"])
        self._configure_styles()

        self.state_model = State()
        self.state_model.load()

        self._build_ui()
        self._reload_topics()
        if self.state_model.current_topic:
            self._select_topic(self.state_model.current_topic)

        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def _register_accessibility(self, key: str, widget, *, name: str, description: str, role: str, focusable: bool):
        """Registriert ein Widget im metadata-first-A11y-Vertrag."""
        self._a11y_registry[key] = apply_accessibility_metadata(
            widget,
            name=name,
            description=description,
            role=role,
            focusable=focusable,
        )
        return widget

    def _apply_window_icon(self):
        """Setzt nach Möglichkeit das Windows-App-Icon aus dem Projektordner."""
        icon_path = Path(__file__).with_name("DokuReader.ico")
        if not icon_path.exists():
            return
        try:
            self.iconbitmap(default=str(icon_path))
        except tk.TclError:
            pass

    def _build_theme(self) -> dict[str, str]:
        """Definiert die Farb- und Stilwerte für den ersten UI-Refresh-Slice."""
        return {
            "window_bg": "#eef1f6",
            "shell_bg": "#f7f8fb",
            "card_bg": "#ffffff",
            "card_alt_bg": "#f4f6fb",
            "border": "#d6dce8",
            "text": "#172033",
            "muted": "#5f6c86",
            "accent": "#275efe",
            "accent_soft": "#eaf0ff",
            "success": "#0d6b42",
            "success_soft": "#e6f5ec",
            "preview_bg": "#fbfcfe",
            "preview_text_bg": "#f8f9fc",
            "button_neutral": "#edf1f7",
            "button_neutral_hover": "#e4eaf4",
        }

    def _configure_styles(self):
        """Konfiguriert eine ruhige, modernere Tk/ttk-Oberfläche."""
        style = ttk.Style(self)
        try:
            if "clam" in style.theme_names():
                style.theme_use("clam")
        except tk.TclError:
            pass

        self.option_add("*TCombobox*Listbox*Font", "TkDefaultFont 10")

        style.configure("Shell.TFrame", background=self._theme["shell_bg"])
        style.configure("Column.TFrame", background=self._theme["card_bg"])
        style.configure("Toolbar.TFrame", background=self._theme["card_bg"])
        style.configure("SectionTitle.TLabel", background=self._theme["card_bg"], foreground=self._theme["text"], font=("TkDefaultFont", 11, "bold"))
        style.configure("SectionSubtitle.TLabel", background=self._theme["card_bg"], foreground=self._theme["muted"], font=("TkDefaultFont", 9))
        style.configure("Hero.TFrame", background=self._theme["shell_bg"])
        style.configure("HeroTitle.TLabel", background=self._theme["shell_bg"], foreground=self._theme["text"], font=("TkDefaultFont", 20, "bold"))
        style.configure("HeroSubtitle.TLabel", background=self._theme["shell_bg"], foreground=self._theme["muted"], font=("TkDefaultFont", 10))
        style.configure("HeroBadge.TLabel", background=self._theme["accent_soft"], foreground=self._theme["accent"], font=("TkDefaultFont", 9, "bold"), padding=(10, 4))
        style.configure("TLabel", background=self._theme["card_bg"], foreground=self._theme["text"])
        style.configure("TButton", background=self._theme["button_neutral"], foreground=self._theme["text"], bordercolor=self._theme["border"], focusthickness=1, focuscolor=self._theme["accent"], padding=(12, 7))
        style.map("TButton", background=[("active", self._theme["button_neutral_hover"])], bordercolor=[("focus", self._theme["accent"])])
        style.configure("Accent.TButton", background=self._theme["accent"], foreground="#ffffff", bordercolor=self._theme["accent"], padding=(12, 7))
        style.map("Accent.TButton", background=[("active", "#1e4ed8")], foreground=[("disabled", "#d7dff7")])
        style.configure("Treeview", background=self._theme["card_bg"], fieldbackground=self._theme["card_bg"], foreground=self._theme["text"], bordercolor=self._theme["border"], rowheight=26)
        style.configure("Treeview.Heading", background=self._theme["card_alt_bg"], foreground=self._theme["text"], bordercolor=self._theme["border"], relief="flat", font=("TkDefaultFont", 9, "bold"))
        style.map("Treeview", background=[("selected", self._theme["accent_soft"])], foreground=[("selected", self._theme["text"])])
        style.map("Treeview.Heading", background=[("active", self._theme["button_neutral_hover"])])
        style.configure("Card.TLabelframe", background=self._theme["card_bg"], bordercolor=self._theme["border"], relief="solid")
        style.configure("Card.TLabelframe.Label", background=self._theme["card_bg"], foreground=self._theme["text"], font=("TkDefaultFont", 10, "bold"))
        style.configure("TRadiobutton", background=self._theme["card_bg"], foreground=self._theme["text"], padding=(2, 2))
        style.map("TRadiobutton", background=[("active", self._theme["card_bg"])])
        style.configure("App.Horizontal.TPanedwindow", background=self._theme["shell_bg"], sashrelief="flat", sashwidth=10)

    def _build_section_header(self, parent, title: str, subtitle: str | None = None):
        """Rendert eine einheitliche Abschnittsüberschrift mit optionalem Untertitel."""
        wrapper = ttk.Frame(parent, style="Column.TFrame")
        wrapper.pack(fill=tk.X, padx=14, pady=(14, 6))
        ttk.Label(wrapper, text=title, style="SectionTitle.TLabel").pack(anchor="w")
        if subtitle:
            ttk.Label(wrapper, text=subtitle, style="SectionSubtitle.TLabel", wraplength=340, justify="left").pack(anchor="w", pady=(2, 0))
        return wrapper

    def _build_ui(self):
        """Erstellt alle GUI-Widgets (PanedWindow, Themenliste, Dokumententree, Vorschau, Export)."""
        shell = ttk.Frame(self, style="Shell.TFrame", padding=(18, 16, 18, 18))
        shell.pack(fill=tk.BOTH, expand=True)

        hero = ttk.Frame(shell, style="Hero.TFrame")
        hero.pack(fill=tk.X, pady=(0, 14))
        hero_copy = ttk.Frame(hero, style="Hero.TFrame")
        hero_copy.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.app_title_label = ttk.Label(hero_copy, text="DokuReader", style="HeroTitle.TLabel")
        self.app_title_label.pack(anchor="w")
        self._register_accessibility(
            "app_title",
            self.app_title_label,
            name="DokuReader",
            description="Lokale Dokumentenbibliothek",
            role="heading",
            focusable=False,
        )
        self.app_subtitle_label = ttk.Label(
            hero_copy,
            text="Lokale Dokumentbibliothek mit Lesestatus, Vorschau und ruhigem Arbeitsfluss.",
            style="HeroSubtitle.TLabel",
        )
        self.app_subtitle_label.pack(anchor="w", pady=(4, 0))
        self._register_accessibility(
            "app_subtitle",
            self.app_subtitle_label,
            name="DokuReader Beschreibung",
            description="Lokale Bibliothek mit Lesestatus, Vorschau und Export",
            role="description",
            focusable=False,
        )
        self.hero_badge_label = ttk.Label(hero, text="Desktop-Refresh", style="HeroBadge.TLabel")
        self.hero_badge_label.pack(side=tk.RIGHT, anchor="n")
        self._register_accessibility(
            "hero_badge",
            self.hero_badge_label,
            name="Desktop-Refresh",
            description="Aktueller Desktop-Oberflächenstand",
            role="status",
            focusable=False,
        )

        paned = ttk.Panedwindow(shell, orient=tk.HORIZONTAL, style="App.Horizontal.TPanedwindow")
        paned.pack(fill=tk.BOTH, expand=True)

        # Linke Spalte: Themen
        left = ttk.Frame(paned, style="Column.TFrame")
        paned.add(left, weight=1)
        self.topic_section_header = self._build_section_header(
            left,
            "Themen",
            "Strukturiere deine Leselisten nach Projekten, Fachgebieten oder Ordnern.",
        )
        self.topic_list = tk.Listbox(left)
        self.topic_list.configure(
            bg=self._theme["card_alt_bg"],
            fg=self._theme["text"],
            selectbackground=self._theme["accent"],
            selectforeground="#ffffff",
            relief="flat",
            borderwidth=0,
            highlightthickness=1,
            highlightbackground=self._theme["border"],
            highlightcolor=self._theme["accent"],
            activestyle="none",
        )
        self.topic_list.pack(fill=tk.BOTH, expand=True, padx=14, pady=(0, 10))
        self._register_accessibility(
            "topic_list",
            self.topic_list,
            name="Themenliste",
            description="Wähle ein Thema für die zugehörige Dokumentenliste",
            role="list",
            focusable=True,
        )
        self.topic_list.bind("<<ListboxSelect>>", self.on_topic_select)
        btns = ttk.Frame(left, style="Toolbar.TFrame")
        btns.pack(fill=tk.X, padx=14, pady=(0, 14))
        self.add_topic_button = ttk.Button(btns, text="Neu", command=self.add_topic, style="Accent.TButton")
        self.add_topic_button.pack(side=tk.LEFT)
        self.rename_topic_button = ttk.Button(btns, text="Umbenennen", command=self.rename_topic)
        self.rename_topic_button.pack(side=tk.LEFT, padx=(8, 0))
        self.delete_topic_button = ttk.Button(btns, text="Löschen", command=self.delete_topic)
        self.delete_topic_button.pack(side=tk.LEFT, padx=(8, 0))
        self._register_accessibility("add_topic", self.add_topic_button, name="Thema neu", description="Legt ein neues Thema an", role="button", focusable=True)
        self._register_accessibility("rename_topic", self.rename_topic_button, name="Thema umbenennen", description="Benennt das ausgewählte Thema um", role="button", focusable=True)
        self._register_accessibility("delete_topic", self.delete_topic_button, name="Thema löschen", description="Löscht das ausgewählte Thema; Originaldateien bleiben erhalten", role="button", focusable=True)

        # Mitte: Dokumente
        center = ttk.Frame(paned, style="Column.TFrame")
        paned.add(center, weight=3)
        self.document_section_header = self._build_section_header(
            center,
            "Dokumente im Thema",
            "Suche, sortiere und markiere Einträge direkt aus der Bibliothek heraus.",
        )

        # Suchleiste
        search_frame = ttk.Frame(center, style="Toolbar.TFrame")
        search_frame.pack(fill=tk.X, padx=14, pady=(0, 8))
        self.search_label = ttk.Label(search_frame, text="Suche:")
        self.search_label.pack(side=tk.LEFT, padx=(0, 4))
        self._register_accessibility(
            "search_label",
            self.search_label,
            name="Suche",
            description="Beschriftung des Dokumente-Suchfelds",
            role="label",
            focusable=False,
        )
        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", self._on_search_changed)
        self.search_entry = ttk.Entry(search_frame, textvariable=self._search_var)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.search_entry.bind("<Escape>", self.clear_search)
        self._register_accessibility(
            "search_entry",
            self.search_entry,
            name="Dokumente suchen",
            description="Filtert die Dokumente des ausgewählten Themas nach Dateiname; Escape leert die Suche",
            role="searchbox",
            focusable=True,
        )
        self.clear_search_button = ttk.Button(
            search_frame,
            text="Leeren",
            width=8,
            command=self.clear_search,
        )
        self.clear_search_button.pack(side=tk.LEFT, padx=(4, 0))
        self._register_accessibility(
            "clear_search",
            self.clear_search_button,
            name="Suche leeren",
            description="Entfernt den Suchfilter und setzt den Fokus zurück ins Suchfeld",
            role="button",
            focusable=True,
        )
        self._update_search_controls()

        self.doc_tree = ttk.Treeview(center, columns=("typ", "größe"), show="tree headings", selectmode="browse")
        self.doc_tree.heading("#0", text="Name", anchor="w",
                              command=lambda: self._sort_docs("name"))
        self.doc_tree.heading("typ", text="Typ",
                              command=lambda: self._sort_docs("typ"))
        self.doc_tree.heading("größe", text="Größe",
                              command=lambda: self._sort_docs("größe"))
        self.doc_tree.column("#0", width=550, anchor="w")
        self.doc_tree.column("typ", width=100, anchor="w")
        self.doc_tree.column("größe", width=100, anchor="e")
        self.doc_tree.pack(fill=tk.BOTH, expand=True, padx=14, pady=(0, 8))
        self._register_accessibility(
            "document_list",
            self.doc_tree,
            name="Dokumentenliste",
            description="Dokumente des Themas; Enter öffnet die Datei, Shift+F10 öffnet Aktionen",
            role="list",
            focusable=True,
        )
        self._sort_key = "name"
        self._sort_reverse = False

        # Tag für gelesene Einträge: grün + fett
        self.doc_tree.tag_configure(
            "read",
            foreground=self._theme["success"],
            background=self._theme["success_soft"],
            font=("TkDefaultFont", 9, "bold"),
        )
        # Optionaler Hintergrund statt Textfarbe:
        # self.doc_tree.tag_configure("read", background="#d9f7d9")

        # Binds
        self.doc_tree.bind("<Button-3>", self.on_doc_right_click)
        self.doc_tree.bind("<Double-1>", self.on_doc_double_click)
        self.doc_tree.bind("<<TreeviewSelect>>", self.on_doc_select)
        self.doc_tree.bind("<Shift-F10>", self.open_selected_doc_menu)
        self.doc_tree.bind("<Menu>", self.open_selected_doc_menu)
        self.doc_tree.bind("<Return>", self.on_doc_double_click)
        self.doc_tree.bind("<KP_Enter>", self.on_doc_double_click)

        # Drag & Drop
        addbar = ttk.Frame(center, style="Toolbar.TFrame")
        addbar.pack(fill=tk.X, padx=14, pady=(0, 14))
        self.doc_actions_button = ttk.Button(
            addbar,
            text="Aktionen…",
            command=self.open_selected_doc_menu,
            state="disabled",
        )
        self.doc_actions_button.pack(side=tk.LEFT)
        self._register_accessibility(
            "document_actions",
            self.doc_actions_button,
            name="Dokumentaktionen",
            description="Öffnet Aktionen für das ausgewählte Dokument; ohne Auswahl deaktiviert",
            role="button",
            focusable=True,
        )
        self.add_files_button = ttk.Button(addbar, text="Hinzufügen", command=self.add_files_dialog, style="Accent.TButton")
        self.add_files_button.pack(side=tk.RIGHT)
        self._register_accessibility(
            "add_files",
            self.add_files_button,
            name="Dateien hinzufügen",
            description="Öffnet einen Dateidialog oder nimmt Dateien per Drag-and-drop auf",
            role="button",
            focusable=True,
        )
        self.doc_state_label = ttk.Label(
            center,
            text="Wähle zuerst ein Thema; danach kannst du Dateien hinzufügen oder hierher ziehen.",
            style="SectionSubtitle.TLabel",
            anchor="w",
        )
        self.doc_state_label.pack(fill=tk.X, padx=14, pady=(0, 5), before=addbar)
        self._register_accessibility(
            "document_state",
            self.doc_state_label,
            name="Dokumentenstatus",
            description="Erklärt leere, gefilterte und Drag-and-drop-Zustände der Dokumentenliste",
            role="status",
            focusable=False,
        )
        if TKDND_AVAILABLE:
            self.doc_tree.drop_target_register('*')  # type: ignore
            self.doc_tree.dnd_bind('<<Drop>>', self.on_drop)  # type: ignore

        # Rechte Spalte: Vorschau + Export
        right = ttk.Frame(paned, style="Column.TFrame")
        paned.add(right, weight=2)
        self.preview_section_header = self._build_section_header(
            right,
            "Vorschau",
            "Prüfe Inhalte und exportiere nur den Stand, den du wirklich weitergeben willst.",
        )
        self.preview = tk.Canvas(
            right,
            bg=self._theme["preview_bg"],
            height=320,
            borderwidth=0,
            highlightthickness=1,
            highlightbackground=self._theme["border"],
        )
        self.preview.pack(fill=tk.BOTH, expand=False, padx=14, pady=(0, 8))
        self._register_accessibility(
            "preview_canvas",
            self.preview,
            name="Vorschaubildfläche",
            description="Zeigt eine Bild- oder Dokumentvorschau, wenn verfügbar",
            role="presentation",
            focusable=False,
        )
        self.preview_state_label = ttk.Label(
            right,
            text="Keine Datei ausgewählt.",
            style="SectionSubtitle.TLabel",
            anchor="w",
        )
        self.preview_state_label.pack(fill=tk.X, padx=14, pady=(0, 4))
        self._register_accessibility(
            "preview_state",
            self.preview_state_label,
            name="Vorschau-Status",
            description="Erklärt Vorschau-, Leer- und Fehlerzustände",
            role="status",
            focusable=False,
        )
        self.preview_text = tk.Text(right, height=10, wrap="word", state="disabled")
        self.preview_text.configure(
            bg=self._theme["preview_text_bg"],
            fg=self._theme["text"],
            relief="flat",
            borderwidth=0,
            highlightthickness=1,
            highlightbackground=self._theme["border"],
            highlightcolor=self._theme["accent"],
            insertbackground=self._theme["text"],
            padx=10,
            pady=10,
        )
        self.preview_text.pack(fill=tk.BOTH, expand=True, padx=14, pady=(0, 10))
        self._register_accessibility(
            "preview_text",
            self.preview_text,
            name="Vorschautext",
            description="Nicht editierbare Text- und Metadatenvorschau des ausgewählten Dokuments",
            role="document",
            focusable=True,
        )

        export_frame = ttk.LabelFrame(right, text="Sammel-PDF", style="Card.TLabelframe")
        export_frame.pack(fill=tk.X, padx=14, pady=(0, 10))
        self._register_accessibility(
            "collection_export_frame",
            export_frame,
            name="Sammel-PDF",
            description="Filter und Aktion für den Sammel-PDF-Export",
            role="group",
            focusable=False,
        )
        self.filter_var = tk.StringVar(value="alle")
        self.filter_var.trace_add("write", self._on_collection_filter_changed)
        self.collection_filter_buttons = [
            ttk.Radiobutton(export_frame, text="Alle", variable=self.filter_var, value="alle"),
            ttk.Radiobutton(export_frame, text="Gelesene", variable=self.filter_var, value="gelesene"),
            ttk.Radiobutton(export_frame, text="Ungelesene", variable=self.filter_var, value="ungelesene"),
        ]
        for button in self.collection_filter_buttons:
            button.pack(side=tk.LEFT, padx=6, pady=6)
        filter_metadata = (
            ("all_documents", "Alle Dokumente", "Exportiert alle Dokumente des Themas", "radio"),
            ("read_documents", "Gelesene Dokumente", "Beschränkt den Export auf gelesene Dokumente", "radio"),
            ("unread_documents", "Ungelesene Dokumente", "Beschränkt den Export auf ungelesene Dokumente", "radio"),
        )
        for (key, name, description, role), button in zip(filter_metadata, self.collection_filter_buttons):
            self._register_accessibility(key, button, name=name, description=description, role=role, focusable=True)
        self.collection_export_button = ttk.Button(
            export_frame,
            text="Sammel-PDF erzeugen",
            command=self.create_collection_pdf,
            style="Accent.TButton",
        )
        self.collection_export_button.pack(side=tk.RIGHT, padx=6, pady=6)
        self._register_accessibility(
            "collection_export",
            self.collection_export_button,
            name="Sammel-PDF erzeugen",
            description="Erzeugt ein PDF aus der gewählten Dokumentmenge; ohne passende Dokumente deaktiviert",
            role="button",
            focusable=True,
        )
        self.collection_export_hint_label = ttk.Label(
            export_frame,
            text="Wähle zuerst ein Thema mit passenden Dokumenten aus.",
            style="SectionSubtitle.TLabel",
        )
        self.collection_export_hint_label.pack(anchor="w", padx=8, pady=(0, 8))
        self._register_accessibility(
            "collection_export_status",
            self.collection_export_hint_label,
            name="Sammel-PDF-Status",
            description="Erklärt die aktuelle Exportverfügbarkeit",
            role="status",
            focusable=False,
        )

        library_export_frame = ttk.LabelFrame(right, text="Bibliothek (JSON)", style="Card.TLabelframe")
        library_export_frame.pack(fill=tk.X, padx=14, pady=(0, 14))
        self._register_accessibility(
            "library_export_frame",
            library_export_frame,
            name="Bibliothek JSON",
            description="Exportiert Metadaten und Lesestatus ohne Dokumentinhalte",
            role="group",
            focusable=False,
        )
        self.library_export_desc_label = ttk.Label(
            library_export_frame,
            text="Exportiert Themen, Pfade, Metadaten und Lesestatus ohne Dokumentinhalte.",
            wraplength=340,
            justify="left",
        )
        self.library_export_desc_label.pack(anchor="w", padx=8, pady=(8, 4))
        self._register_accessibility(
            "library_export_description",
            self.library_export_desc_label,
            name="Bibliothek JSON Beschreibung",
            description="Erklärender Text zum Metadatenexport",
            role="description",
            focusable=False,
        )
        self.library_export_button = ttk.Button(
            library_export_frame,
            text="JSON-Export…",
            command=self.export_library_json,
            style="Accent.TButton",
        )
        self.library_export_button.pack(anchor="e", padx=8, pady=(0, 8))
        self._register_accessibility(
            "library_export",
            self.library_export_button,
            name="Bibliothek als JSON exportieren",
            description="Öffnet einen Speicherndialog für den Metadaten- und Lesestatus-Export",
            role="button",
            focusable=True,
        )

        # Kontextmenü
        self.doc_menu = tk.Menu(self, tearoff=0)
        self.doc_menu.add_command(label="Als gelesen markieren", command=lambda: self.set_selected_read(True))
        self.doc_menu.add_command(label="Gelesen-Markierung entfernen", command=lambda: self.set_selected_read(False))
        self.doc_menu.add_separator()
        self.doc_menu.add_command(label="Aus Bibliothek entfernen", command=self.remove_selected_doc)

    # Themen-Handling
    def _reload_topics(self):
        """Aktualisiert die Themenliste aus dem State (alphabetisch sortiert)."""
        self.topic_list.delete(0, tk.END)
        for t in sorted(self.state_model.topics.keys(), key=str.lower):
            self.topic_list.insert(tk.END, t)

    def _on_search_changed(self, *_args):
        """Aktualisiert Trefferliste und Suchleisten-Status bei Eingaben."""
        self._reload_docs()
        self._update_search_controls()

    def _update_search_controls(self):
        """Aktiviert die Leeren-Schaltfläche nur bei aktiver Suche."""
        if not hasattr(self, "clear_search_button"):
            return
        has_query = bool(self._search_var.get().strip())
        self.clear_search_button.state(["!disabled"] if has_query else ["disabled"])

    def _update_doc_action_controls(self):
        """Aktiviert Dokumentaktionen nur bei ausgewähltem Dokument."""
        if not hasattr(self, "doc_actions_button"):
            return
        has_selection = bool(self.doc_tree.selection())
        self.doc_actions_button.state(["!disabled"] if has_selection else ["disabled"])

    def _on_collection_filter_changed(self, *_args):
        """Aktualisiert den Sammel-PDF-Zustand bei Filterwechseln."""
        self._update_collection_export_controls()

    def _matching_collection_docs(self) -> list[dict]:
        """Liefert die zur aktuellen Exportauswahl passenden Dokumente."""
        topic = self.state_model.current_topic
        if not topic:
            return []
        docs = self.state_model.list_docs(topic)
        filter_mode = self.filter_var.get()
        if filter_mode == "gelesene":
            return [d for d in docs if d.get("read")]
        if filter_mode == "ungelesene":
            return [d for d in docs if not d.get("read")]
        return docs

    def _update_collection_export_controls(self):
        """Spiegelt Export-Verfügbarkeit direkt im UI statt erst nach dem Klick."""
        if not hasattr(self, "collection_export_button"):
            return
        topic = self.state_model.current_topic
        if not topic:
            hint = "Wähle zuerst ein Thema mit passenden Dokumenten aus."
            enabled = False
        else:
            matching_docs = self._matching_collection_docs()
            if matching_docs:
                filter_labels = {
                    "alle": "alle",
                    "gelesene": "gelesenen",
                    "ungelesene": "ungelesenen",
                }
                hint = (
                    f"Exportiert {len(matching_docs)} {filter_labels.get(self.filter_var.get(), 'alle')} "
                    f"Dokumente aus „{topic}“."
                )
                enabled = True
            else:
                empty_labels = {
                    "alle": f"Im Thema „{topic}“ sind noch keine Dokumente.",
                    "gelesene": f"Im Thema „{topic}“ gibt es noch keine gelesenen Dokumente.",
                    "ungelesene": f"Im Thema „{topic}“ gibt es noch keine ungelesenen Dokumente.",
                }
                hint = empty_labels.get(self.filter_var.get(), f"Im Thema „{topic}“ sind noch keine Dokumente.")
                enabled = False

        self.collection_export_hint_label.configure(text=hint)
        self.collection_export_button.state(["!disabled"] if enabled else ["disabled"])
        for button in self.collection_filter_buttons:
            button.state(["!disabled"] if topic else ["disabled"])

    def _set_document_state(self, text: str) -> None:
        """Setzt den sichtbaren und semantischen Dokumentlistenstatus."""
        if hasattr(self, "doc_state_label"):
            self.doc_state_label.configure(text=text)

    def _set_preview_text(self, text: str) -> None:
        """Schreibt Vorschautext kontrolliert in das nicht editierbare Textfeld."""
        self.preview_text.configure(state="normal")
        self.preview_text.delete("1.0", tk.END)
        if text:
            self.preview_text.insert("1.0", text)
        self.preview_text.configure(state="disabled")

    def _set_preview_state(self, text: str) -> None:
        """Aktualisiert den kurzen Status oberhalb der Vorschautextfläche."""
        if hasattr(self, "preview_state_label"):
            self.preview_state_label.configure(text=text)

    def clear_search(self, _event=None):
        """Leert die Suche tastaturfreundlich und behält den Fokus im Suchfeld."""
        self._search_var.set("")
        if hasattr(self, "search_entry"):
            self.search_entry.focus_set()
        return "break"

    def _select_topic(self, topic: str):
        """Setzt das aktuelle Thema und lädt die zugehörigen Dokumente."""
        self.state_model.current_topic = topic
        self._reload_docs()

    def on_topic_select(self, _=None):
        """Callback: Thema in der Listbox ausgewählt; lädt zugehörige Dokumente und speichert State."""
        sel = self.topic_list.curselection()
        if not sel:
            return
        topic = self.topic_list.get(sel[0])
        self._select_topic(topic)
        self.state_model.save()

    def add_topic(self):
        """Dialog zum Anlegen eines neuen Themas; prüft auf leeren Namen und Duplikate."""
        name = simpledialog.askstring("Neues Thema", "Name:")
        if not name:
            return
        name = name.strip()
        if not name:
            return
        if name in self.state_model.topics:
            messagebox.showwarning("Hinweis", "Thema existiert bereits.")
            return
        self.state_model.ensure_topic(name)
        self.state_model.save()
        self._reload_topics()
        self._select_topic(name)

    def rename_topic(self):
        """Dialog zum Umbenennen des aktuell gewählten Themas; prüft auf Duplikate."""
        sel = self.topic_list.curselection()
        if not sel:
            return
        old = self.topic_list.get(sel[0])
        new = simpledialog.askstring("Thema umbenennen", "Neuer Name:", initialvalue=old)
        if not new:
            return
        new = new.strip()
        if not new or new == old:
            return
        if new in self.state_model.topics:
            messagebox.showwarning("Hinweis", "Ein Thema mit diesem Namen existiert bereits.")
            return
        self.state_model.rename_topic(old, new)
        self.state_model.save()
        self._reload_topics()
        self._select_topic(new)

    def delete_topic(self):
        """Löscht das aktuell gewählte Thema nach Bestätigung (Originaldateien bleiben erhalten)."""
        sel = self.topic_list.curselection()
        if not sel:
            return
        topic = self.topic_list.get(sel[0])
        if messagebox.askyesno("Bestätigen", f"Thema '{topic}' entfernen? (Dateien bleiben am Originalort)"):
            self.state_model.remove_topic(topic)
            self.state_model.save()
            self._reload_topics()
            self.doc_tree.delete(*self.doc_tree.get_children())
            self.clear_preview()

    # Dokumente-Handling
    def _sort_docs(self, key):
        """Sortiert Dokumente nach Spalte. Erneuter Klick kehrt Reihenfolge um."""
        if self._sort_key == key:
            self._sort_reverse = not self._sort_reverse
        else:
            self._sort_key = key
            self._sort_reverse = False
        self._reload_docs()

    def _reload_docs(self):
        """Füllt den Dokument-Treeview neu (aktuelle Sortierung und Suchfilter werden berücksichtigt)."""
        self.doc_tree.delete(*self.doc_tree.get_children())
        topic = self.state_model.current_topic
        if not topic:
            self._set_document_state("Wähle zuerst ein Thema; danach kannst du Dateien hinzufügen oder hierher ziehen.")
            self.clear_preview()
            self._update_doc_action_controls()
            self._update_collection_export_controls()
            return
        all_docs = self.state_model.list_docs(topic)
        docs = list(all_docs)
        # Suchfilter anwenden (case-insensitiv, nach Dateiname)
        search = getattr(self, "_search_var", None)
        query = ""
        if search:
            query = search.get().strip().lower()
            if query:
                docs = [d for d in docs if query in os.path.basename(d["path"]).lower()]
        # Sortierung anwenden
        sort_key = getattr(self, "_sort_key", "name")
        sort_reverse = getattr(self, "_sort_reverse", False)
        if sort_key == "name":
            docs.sort(key=lambda d: os.path.basename(d["path"]).lower(),
                      reverse=sort_reverse)
        elif sort_key == "typ":
            docs.sort(key=lambda d: Path(d["path"]).suffix.lower(),
                      reverse=sort_reverse)
        elif sort_key == "größe":
            def _size(d):
                try:
                    return os.path.getsize(d["path"])
                except OSError:
                    return 0
            docs.sort(key=_size, reverse=sort_reverse)
        for d in docs:
            path = d["path"]
            name = os.path.basename(path)
            ext = Path(path).suffix.lower()
            try:
                size = human_size(os.path.getsize(path))
            except OSError:
                size = "?"
            tags = ()
            if d.get("read"):
                tags = ("read",)
                name = "✓ " + name
            self.doc_tree.insert("", "end", iid=path, text=name,
                                 values=(ext[1:].upper(), size), tags=tags)
        if not all_docs:
            self._set_document_state(
                f"Im Thema „{topic}“ sind noch keine Dokumente. Nutze „Hinzufügen“ oder ziehe Dateien hierher."
            )
        elif not docs and query:
            self._set_document_state(f"Keine Treffer für „{query}“. Drücke Escape, um die Suche zu leeren.")
        else:
            self._set_document_state(
                f"{len(docs)} Dokumente sichtbar. Enter öffnet die Auswahl, Shift+F10 öffnet Aktionen."
            )
        self.clear_preview()
        self._update_doc_action_controls()
        self._update_collection_export_controls()

    def add_files_dialog(self):
        """Öffnet einen Dateidialog und fügt ausgewählte Dateien dem aktuellen Thema hinzu."""
        topic = self.state_model.current_topic
        if not topic:
            messagebox.showinfo("Hinweis", "Bitte zuerst ein Thema auswählen.")
            return
        paths = filedialog.askopenfilenames(
            title="Dateien hinzufügen",
            filetypes=[("Unterstützte Dateien", "*.txt;*.doc;*.docx;*.pdf;*.odt;*.rtf;*.jpg;*.jpeg;*.gif;*.png")]
        )
        if not paths:
            return
        added = self.state_model.add_docs(topic, paths)
        self.state_model.save()
        self._reload_docs()
        if added == 0:
            messagebox.showinfo("Hinweis", "Keine neuen unterstützten Dateien hinzugefügt.")

    def on_drop(self, event):
        """Callback für Drag-&-Drop: Fügt gedropte Dateien dem aktuellen Thema hinzu."""
        topic = self.state_model.current_topic
        if not topic:
            self._set_document_state("Wähle zuerst ein Thema, bevor du Dateien per Drag-and-drop hinzufügst.")
            return "break"
        paths = self._split_dnd_paths(event.data)
        if not paths:
            self._set_document_state("Keine gültigen Dateipfade im Drag-and-drop-Ereignis erkannt.")
            return "break"
        added = self.state_model.add_docs(topic, paths)
        self.state_model.save()
        self._reload_docs()
        if added == 0:
            self._set_document_state("Keine neuen unterstützten Dateien per Drag-and-drop hinzugefügt.")
        return "break"

    @staticmethod
    def _split_dnd_paths(data: str):
        """Parst den Drag-&-Drop-Datenpfad (unterstützt geschweifte Klammern für Leerzeichen).

        Args:
            data: Rohstring aus dem Drop-Event (z.B. '{C:\\Pfad mit Leerzeichen\\file.pdf} /home/x.pdf')

        Returns:
            Liste von bereinigten Dateipfaden
        """
        # Formate wie {C:\Pfad mit Leerzeichen\file.pdf} /home/user/x.pdf ...
        # BUG-D4/D5-Fix: '{' nur als DnD-Trennzeichen werten, wenn cur leer ist (Tokenanfang).
        # '}' nur als Trennzeichen werten, wenn aktuell eine Klammer geöffnet ist.
        # Literal-{} in Dateinamen (z.B. "bericht{2026}.txt") werden so korrekt behandelt.
        res = []
        cur = []
        in_brace = False
        for ch in data:
            if ch == "{" and not in_brace and not cur:
                # DnD-Klammer öffnen – nur am Tokenanfang (cur leer, nicht schon in Klammer)
                in_brace = True
            elif ch == "}" and in_brace:
                # Klammer schließen
                in_brace = False
                res.append("".join(cur))
                cur = []
            elif ch == " " and not in_brace:
                if cur:
                    res.append("".join(cur))
                    cur = []
            else:
                cur.append(ch)
        if cur:
            res.append("".join(cur))
        return [p.strip() for p in res if p.strip()]

    def on_doc_right_click(self, event):
        """Zeigt das Kontextmenü beim Rechtsklick auf einen Dokumenteintrag."""
        iid = self.doc_tree.identify_row(event.y)
        if iid:
            self.doc_tree.selection_set(iid)
            self.doc_tree.focus(iid)
            self._update_doc_action_controls()
            return self.open_selected_doc_menu(event)
        return "break"

    def open_selected_doc_menu(self, event=None):
        """Öffnet Dokumentaktionen per Tastatur, Schaltfläche oder Rechtsklick."""
        sel = self.doc_tree.selection()
        if not sel:
            self._update_doc_action_controls()
            return "break"
        if event is not None and getattr(event, "x_root", 0) and getattr(event, "y_root", 0):
            x_root = event.x_root
            y_root = event.y_root
        else:
            bbox = self.doc_tree.bbox(sel[0])
            if bbox:
                x, y, width, height = bbox
                x_root = self.doc_tree.winfo_rootx() + x + max(width // 2, 16)
                y_root = self.doc_tree.winfo_rooty() + y + height
            else:
                x_root = self.doc_tree.winfo_rootx() + 16
                y_root = self.doc_tree.winfo_rooty() + 16
        self.doc_menu.tk_popup(x_root, y_root)
        return "break"

    def on_doc_double_click(self, _=None):
        """Öffnet die ausgewählte Datei im Standard-Programm des Betriebssystems."""
        sel = self.doc_tree.selection()
        if not sel:
            return
        path = sel[0]
        try:
            if platform.system() == "Windows":
                os.startfile(path)  # type: ignore
            elif platform.system() == "Darwin":
                subprocess.run(["open", path], check=False, timeout=30)
            else:
                subprocess.run(["xdg-open", path], check=False, timeout=30)
        except Exception as e:
            messagebox.showerror("Fehler", f"Konnte Datei nicht öffnen:\n{e}")

    def set_selected_read(self, is_read: bool):
        """Setzt den Gelesen-Status des ausgewählten Dokuments und aktualisiert die Ansicht.

        Args:
            is_read: True = gelesen markieren, False = Markierung entfernen
        """
        topic = self.state_model.current_topic
        sel = self.doc_tree.selection()
        if not topic or not sel:
            return
        path = sel[0]
        self.state_model.set_read(topic, path, is_read)
        self.state_model.save()
        self._reload_docs()

    def remove_selected_doc(self):
        """Entfernt das ausgewählte Dokument aus der Bibliothek nach Bestätigung (Datei bleibt erhalten)."""
        topic = self.state_model.current_topic
        sel = self.doc_tree.selection()
        if not topic or not sel:
            return
        path = sel[0]
        if messagebox.askyesno("Entfernen", "Dokument aus der Bibliothek entfernen?\n(Originaldatei bleibt erhalten)"):
            self.state_model.remove_doc(topic, path)
            self.state_model.save()
            self._reload_docs()

    def on_doc_select(self, _=None):
        """Callback: Dokument im Treeview ausgewählt; zeigt Vorschau oder löscht sie."""
        sel = self.doc_tree.selection()
        self._update_doc_action_controls()
        if not sel:
            self.clear_preview()
            return
        self.show_preview(sel[0])

    # Vorschau
    def clear_preview(self):
        """Leert Canvas und Textfeld der Vorschau und zeigt Platzhaltertext."""
        self._update_doc_action_controls()
        self.preview.delete("all")
        self._set_preview_text("")
        self.preview.create_text(
            14,
            14,
            anchor="nw",
            text="Keine Vorschau\nWähle ein Dokument aus der Liste.",
            fill=self._theme["muted"],
            font=("TkDefaultFont", 10),
        )
        self._set_preview_state("Keine Datei ausgewählt.")

    def show_preview(self, path: str):
        """Zeigt eine Vorschau der Datei (Bild, Text, PDF, DOCX, ODT) je nach Dateityp.

        Args:
            path: Absoluter Pfad zur anzuzeigenden Datei
        """
        self.preview.delete("all")
        self._set_preview_text("")
        ext = Path(path).suffix.lower()
        try:
            if ext in IMAGE_EXTS and PIL_AVAILABLE:
                img = Image.open(path)
                cw = self.preview.winfo_width() or 600
                ch = self.preview.winfo_height() or 320
                img.thumbnail((cw - 20, ch - 20))
                self._preview_img = ImageTk.PhotoImage(img)
                self.preview.create_image(10, 10, anchor="nw", image=self._preview_img)
                self._set_preview_text(f"Bild: {img.width}x{img.height}px\n{path}")
                self._set_preview_state(f"Bildvorschau geladen: {os.path.basename(path)}")
            elif ext in TXT_EXTS:
                content = read_text_with_fallback(path, max_chars=TXT_PREVIEW_CHARS)
                self.preview.create_text(14, 14, anchor="nw", text="Textdatei", fill=self._theme["muted"], font=("TkDefaultFont", 10))
                self._set_preview_text(content if content else "(Leer)")
                self._set_preview_state(
                    f"Textvorschau geladen: {os.path.basename(path)}"
                    if content
                    else f"Textdatei ist leer: {os.path.basename(path)}"
                )
            elif ext in PDF_EXTS and (PDF2IMG_AVAILABLE or PYMUPDF_AVAILABLE) and PIL_AVAILABLE:
                img = None
                if PDF2IMG_AVAILABLE:
                    try:
                        pages = convert_from_path(path, first_page=1, last_page=1)
                        if pages:
                            img = pages[0]
                    except (OSError, ValueError, RuntimeError):
                        img = None
                if img is None and PYMUPDF_AVAILABLE:
                    try:
                        doc = fitz.open(path)
                        try:
                            if len(doc) > 0:
                                page = doc[0]
                                pix = page.get_pixmap()
                                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                        finally:
                            doc.close()
                    except (OSError, ValueError, RuntimeError):
                        img = None
                if img is not None:
                    cw = self.preview.winfo_width() or 600
                    ch = self.preview.winfo_height() or 320
                    img.thumbnail((cw - 20, ch - 20))
                    self._preview_img = ImageTk.PhotoImage(img)
                    self.preview.create_image(10, 10, anchor="nw", image=self._preview_img)
                self._set_preview_text(f"PDF: {os.path.basename(path)}\n{path}")
                self._set_preview_state(f"PDF-Vorschau geladen: {os.path.basename(path)}")
            elif ext == ".docx" and DOCPREVIEW_AVAILABLE:
                try:
                    doc = docx.Document(path)
                    text = "\n".join(p.text for p in doc.paragraphs[:OFFICE_PREVIEW_PARAGRAPHS])
                    self.preview.create_text(14, 14, anchor="nw", text="DOCX-Vorschau", fill=self._theme["muted"], font=("TkDefaultFont", 10))
                    self._set_preview_text(text if text.strip() else "(Kein Textinhalt erkannt)")
                    self._set_preview_state(f"DOCX-Vorschau geladen: {os.path.basename(path)}")
                except (OSError, ValueError, KeyError) as e:
                    self._set_preview_text(f"(Keine DOCX-Vorschau möglich)\n{e}")
                    self._set_preview_state(f"DOCX-Vorschau fehlgeschlagen: {os.path.basename(path)}")
            elif ext == ".odt" and ODFPREVIEW_AVAILABLE:
                try:
                    odt_doc = odf_load(path)
                    paras = odt_doc.getElementsByType(odf_text.P)  # type: ignore
                    text_content = "\n".join(teletype.extractText(p) for p in paras[:OFFICE_PREVIEW_PARAGRAPHS])
                    self.preview.create_text(14, 14, anchor="nw", text="ODT-Vorschau", fill=self._theme["muted"], font=("TkDefaultFont", 10))
                    self._set_preview_text(text_content if text_content.strip() else "(Kein Textinhalt erkannt)")
                    self._set_preview_state(f"ODT-Vorschau geladen: {os.path.basename(path)}")
                except (OSError, ValueError, KeyError) as e:
                    self._set_preview_text(f"(Keine ODT-Vorschau möglich)\n{e}")
                    self._set_preview_state(f"ODT-Vorschau fehlgeschlagen: {os.path.basename(path)}")
            else:
                # Generische Metadaten
                try:
                    size = human_size(os.path.getsize(path))
                except OSError:
                    size = "?"
                self.preview.create_text(14, 14, anchor="nw", text="Keine Vorschau verfügbar", fill=self._theme["muted"], font=("TkDefaultFont", 10))
                self._set_preview_text(f"Datei: {os.path.basename(path)}\nTyp: {ext}\nGröße: {size}\nPfad: {path}")
                self._set_preview_state(f"Keine Vorschau verfügbar: {os.path.basename(path)}")
        except (OSError, ValueError, RuntimeError) as e:
            self.preview.create_text(14, 14, anchor="nw", text="Vorschau-Fehler", fill=self._theme["muted"], font=("TkDefaultFont", 10))
            self._set_preview_text(f"Fehler: {e}")
            self._set_preview_state(f"Vorschaufehler: {os.path.basename(path)}")

    # Export Sammel-PDF
    def create_collection_pdf(self):
        """Startet den Sammel-PDF-Export als Hintergrund-Thread (gelesene/ungelesene/alle)."""
        topic = self.state_model.current_topic
        if not topic:
            messagebox.showinfo("Hinweis", "Bitte zuerst ein Thema auswählen.")
            return
        filter_mode = self.filter_var.get()
        threading.Thread(target=self._create_collection_pdf_worker, args=(topic, filter_mode), daemon=True).start()

    def _create_collection_pdf_worker(self, topic: str, filter_mode: str):
        """Hintergrund-Worker: Konvertiert Dokumente in PDF und merged sie zu einer Datei.

        Args:
            topic: Name des Themas
            filter_mode: 'alle', 'gelesene' oder 'ungelesene'
        """
        self._set_busy(True)
        try:
            docs = self.state_model.list_docs(topic)
            if filter_mode == "gelesene":
                docs = [d for d in docs if d.get("read")]
            elif filter_mode == "ungelesene":
                docs = [d for d in docs if not d.get("read")]

            if not docs:
                self.status_info("Keine passenden Dokumente für das Sammel-PDF.")
                return

            out_path = desktop_path() / f"{topic}_{filter_mode}.pdf"

            with tempfile.TemporaryDirectory() as tmpdir:
                tmpdir = Path(tmpdir)
                pdf_parts: list[str] = []
                log_lines: list[str] = []

                for d in docs:
                    src = d["path"]
                    ext = Path(src).suffix.lower()
                    try:
                        if ext in PDF_EXTS:
                            pdf_parts.append(src)
                            log_lines.append(f"OK: PDF übernommen: {src}")
                        elif ext in TXT_EXTS:
                            pdfp = self._txt_to_pdf(src, tmpdir)
                            if pdfp:
                                pdf_parts.append(pdfp)
                                log_lines.append(f"OK: TXT -> PDF: {src}")
                            else:
                                log_lines.append(f"Übersprungen (TXT ohne ReportLab): {src}")
                        elif ext in IMAGE_EXTS:
                            pdfp = self._image_to_pdf(src, tmpdir)
                            if pdfp:
                                pdf_parts.append(pdfp)
                                log_lines.append(f"OK: Bild -> PDF: {src}")
                            else:
                                log_lines.append(f"Übersprungen (Bild ohne ReportLab/Pillow): {src}")
                        elif ext in WORD_EXTS:
                            pdfp = self._office_to_pdf(src, tmpdir)
                            if pdfp:
                                pdf_parts.append(pdfp)
                                log_lines.append(f"OK: Office -> PDF: {src}")
                            else:
                                log_lines.append(f"Übersprungen (LibreOffice/Word nicht verfügbar): {src}")
                        else:
                            log_lines.append(f"Übersprungen (nicht unterstützt): {src}")
                    except Exception as e:
                        log_lines.append(f"Fehler bei {src}: {e}")

                if not pdf_parts:
                    self.status_info("Keine Dateien konnten in PDF überführt werden.")
                    return

                if not self._merge_pdfs(pdf_parts, out_path):
                    self.status_info("Konnte Sammel-PDF nicht erstellen (PDF-Merge-Bibliothek fehlt?).")
                    return

                summary = "Sammel-PDF erstellt:\n" + str(out_path)
                self.after(0, lambda: messagebox.showinfo("Erfolg", summary))
        finally:
            self._set_busy(False)

    # Busy/Status
    def _set_busy(self, busy: bool):
        """Setzt den Warte-Cursor (thread-sicher via after()).

        Args:
            busy: True = Warte-Cursor, False = normaler Cursor
        """
        def apply():
            self.config(cursor="watch" if busy else "")
            self.update_idletasks()
        self.after(0, apply)

    def status_info(self, msg: str):
        """Zeigt eine Info-Meldung thread-sicher im Hauptthread an.

        Args:
            msg: Anzuzeigende Nachricht
        """
        self.after(0, lambda: messagebox.showinfo("Info", msg))

    def export_library_json(self):
        """Exportiert die gesamte Bibliothek als `dokureader-library-v1.json`."""
        initialfile = f"{LIBRARY_EXPORT_SCHEMA}.json"
        out_path = filedialog.asksaveasfilename(
            title="Bibliothek als JSON exportieren",
            defaultextension=".json",
            initialdir=str(desktop_path()),
            initialfile=initialfile,
            filetypes=[("JSON-Dateien", "*.json"), ("Alle Dateien", "*.*")],
        )
        if not out_path:
            return
        payload = build_library_export_payload(
            self.state_model.topics,
            current_topic=self.state_model.current_topic,
        )
        try:
            write_library_export(out_path, payload)
        except OSError as exc:
            messagebox.showerror("Fehler", f"JSON-Export fehlgeschlagen:\n{exc}")
            return
        messagebox.showinfo("Erfolg", f"Bibliothek exportiert:\n{out_path}")

    # Konvertierungen
    def _txt_to_pdf(self, path: str, tmpdir: Path) -> str | None:
        """Konvertiert eine Textdatei in eine PDF via ReportLab.

        Args:
            path: Pfad zur Quelldatei (.txt)
            tmpdir: Temporäres Verzeichnis für die Ausgabe-PDF

        Returns:
            Pfad zur erstellten PDF oder None bei Fehler/fehlender Bibliothek
        """
        if not REPORTLAB_AVAILABLE:
            return None
        out = tmpdir / (Path(path).stem + "_txt.pdf")
        try:
            c = rl_canvas.Canvas(str(out), pagesize=A4)
            width, height = A4
            margin = 2 * cm
            y = height - margin
            line_height = 12
            c.setFont("Helvetica", 11)
            content = read_text_with_fallback(path)
            if content is None:
                return None
            for line in content.splitlines() or [""]:
                while line:
                    max_chars = int((width - 2 * margin) / 6)  # Näherung
                    part = line[:max_chars]
                    c.drawString(margin, y, part)
                    y -= line_height
                    line = line[len(part):]
                    if y < margin:
                        c.showPage()
                        c.setFont("Helvetica", 11)
                        y = height - margin
            c.showPage()
            c.save()
            return str(out)
        except (OSError, ValueError, RuntimeError):
            try:
                if out.exists():
                    out.unlink()
            except OSError:
                pass
            return None

    def _image_to_pdf(self, path: str, tmpdir: Path) -> str | None:
        """Konvertiert ein Bild in eine PDF (ReportLab bevorzugt, Pillow als Fallback).

        Args:
            path: Pfad zum Quellbild
            tmpdir: Temporäres Verzeichnis für die Ausgabe-PDF

        Returns:
            Pfad zur erstellten PDF oder None bei Fehler
        """
        out = tmpdir / (Path(path).stem + "_img.pdf")
        # Bevorzugt ReportLab (saubere Skalierung)
        if REPORTLAB_AVAILABLE:
            try:
                c = rl_canvas.Canvas(str(out), pagesize=A4)
                width, height = A4
                img = ImageReader(path)
                iw, ih = img.getSize()
                max_w = width - 2 * cm
                max_h = height - 2 * cm
                scale = min(max_w / iw, max_h / ih)
                w = iw * scale
                h = ih * scale
                x = (width - w) / 2
                y = (height - h) / 2
                c.drawImage(img, x, y, w, h, preserveAspectRatio=True)
                c.showPage()
                c.save()
                return str(out)
            except (OSError, ValueError, RuntimeError):
                pass
        # Fallback: Pillow direkt nach PDF
        if PIL_AVAILABLE:
            try:
                img = Image.open(path).convert("RGB")
                img.save(out, "PDF", resolution=150.0)
                return str(out)
            except (OSError, ValueError):
                pass
        return None

    def _office_to_pdf(self, path: str, tmpdir: Path) -> str | None:
        """Konvertiert ein Office-Dokument in PDF (LibreOffice headless oder Word COM).

        Args:
            path: Pfad zum Office-Dokument (.doc, .docx, .odt, .rtf)
            tmpdir: Temporäres Verzeichnis für die Ausgabe-PDF

        Returns:
            Pfad zur erstellten PDF oder None bei Fehler/fehlenden Programmen
        """
        # 1) LibreOffice headless (soffice/libreoffice)
        for cand in ["soffice", "libreoffice"]:
            if shutil.which(cand):
                try:
                    subprocess.run(
                        [cand, "--headless", "--convert-to", "pdf", "--outdir", str(tmpdir), path],
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=180, check=False
                    )
                    out = tmpdir / (Path(path).stem + ".pdf")
                    if out.exists():
                        return str(out)
                except (OSError, subprocess.SubprocessError):
                    pass
        # 2) Microsoft Word COM (nur Windows; öffnet DOC/DOCX/RTF; ODT oft nicht)
        if platform.system() == "Windows":
            word = None
            doc = None
            try:
                import win32com.client  # pywin32
                word = win32com.client.Dispatch("Word.Application")
                word.Visible = False
                doc = word.Documents.Open(path)
                out_path = str(tmpdir / (Path(path).stem + ".pdf"))
                wdFormatPDF = 17
                doc.SaveAs(out_path, FileFormat=wdFormatPDF)
                doc.Close(False)
                doc = None
                word.Quit()
                word = None
                if os.path.exists(out_path):
                    return out_path
            except (OSError, ImportError, AttributeError):
                pass
            finally:
                # COM-Objekte freigeben, falls durch Exception nicht geschlossen
                try:
                    if doc is not None:
                        doc.Close(False)
                except Exception:
                    pass
                try:
                    if word is not None:
                        word.Quit()
                except Exception:
                    pass
        return None

    def _merge_pdfs(self, pdf_paths: list[str], out_path: Path) -> bool:
        """Merged mehrere PDFs zu einer Ausgabedatei via pypdf oder PyPDF2.

        Args:
            pdf_paths: Liste von Pfaden zu den Einzel-PDFs
            out_path: Pfad für die zusammengeführte PDF

        Returns:
            True bei Erfolg, False bei fehlendem PdfWriter oder Fehler
        """
        if not _PdfWriter:
            return False
        writer = _PdfWriter()
        try:
            for p in pdf_paths:
                try:
                    writer.append(p)
                except (OSError, ValueError):
                    # Ignoriere defekte Einzel-PDFs
                    continue
            with open(out_path, "wb") as f:
                writer.write(f)
            return True
        except (OSError, ValueError, RuntimeError):
            return False
        finally:
            try:
                writer.close()
            except (OSError, ValueError):
                pass

    def on_close(self):
        """Callback beim Schließen des Fensters: State speichern und App beenden."""
        self.state_model.save()
        self.destroy()


if __name__ == "__main__":
    app = App()
    app.mainloop()
