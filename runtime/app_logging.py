"""Standard-Logger fuer .SOFTWARE-Apps.

WARUM ES DIESES MODUL GIBT
--------------------------
`START.bat` startet die App **fensterlos** (APP-RUNTIME-STANDARD 5b). Das ist fuer
den Nutzer richtig — aber es bedeutet: Wenn etwas schiefgeht, passiert **sichtbar
gar nichts**. Kein Fenster, keine Meldung, kein Hinweis. Die App ist einfach nicht
da, und niemand weiss, warum.

Das Log ist damit die **einzige Spur** eines Fehlschlags. Deshalb ist es fuer die
fensterlose Variante Pflicht, nicht Kuer. Fensterlos heisst nicht fehlerlos.

DREI FALLEN, DIE HIER ABGEFANGEN SIND
-------------------------------------
1. **Unter `pythonw` ist `sys.stdout` None.** Ein normaler `StreamHandler` wirft
   dort beim ersten Schreiben eine Exception — ausgerechnet der Logger, der den
   Fehler melden soll, wird selbst zum Fehler. Wir haengen den Konsolen-Handler
   deshalb nur an, wenn es einen Stream gibt.

2. **Ein Log ohne `excepthook` faengt genau das nicht, wofuer man es gebaut hat.**
   Ein unbehandelter Absturz geht standardmaessig nach stderr — und das ist unter
   `pythonw` ins Nichts. `install_crash_handler()` schreibt ihn stattdessen ins Log.

3. **Ein Log ohne Rotation waechst unbegrenzt.** Eine Tray-App laeuft wochenlang.

WOHIN GELOGGT WIRD
------------------
`%LOCALAPPDATA%/<App>/logs/app-<PID>.log` — **nicht** in den Projektordner und
**niemals** nach OneDrive: Ein Logfile, das im Sekundentakt beschrieben und
gleichzeitig synchronisiert wird, erzeugt Konfliktkopien und Sync-Last.
"""
from __future__ import annotations

import logging
import logging.handlers
import os
import sys
from pathlib import Path
from typing import Optional

from .app_info import APP_SLUG

DEFAULT_MAX_BYTES = 2 * 1024 * 1024      # 2 MB je Datei
DEFAULT_BACKUP_COUNT = 3                 # -> hoechstens ~8 MB je Prozess
LOG_FORMAT = "%(asctime)s %(levelname)-8s %(name)s: %(message)s"


def log_dir(app_slug: str = APP_SLUG) -> Path:
    """Der Ort des Logs — ausserhalb des Projektordners, ausserhalb von OneDrive."""
    base = os.environ.get("LOCALAPPDATA") or os.environ.get("XDG_STATE_HOME")
    fallback = Path.home() / ("AppData/Local" if os.name == "nt" else ".local/state")
    root = Path(base) if base else fallback
    project = Path(__file__).resolve().parents[1]
    forbidden = [project, Path.home() / "OneDrive"]
    forbidden.extend(Path(value).resolve() for key in ("OneDrive", "OneDriveConsumer", "OneDriveCommercial")
                     if (value := os.environ.get(key)) and Path(value).is_absolute())
    if not root.is_absolute() or any(root.resolve().is_relative_to(path.resolve()) for path in forbidden):
        root = fallback
    if any(root.resolve().is_relative_to(path.resolve()) for path in forbidden):
        raise ValueError("Lokaler Logpfad darf nicht im Projekt oder in OneDrive liegen.")
    return root / app_slug / "logs"


def log_file(app_slug: str = APP_SLUG) -> Path:
    return log_dir(app_slug) / f"app-{os.getpid()}.log"


def _has_console() -> bool:
    """Gibt es ueberhaupt einen Ausgabestrom?

    Unter `pythonw.exe` ist `sys.stderr` None. Ein StreamHandler darauf wuerde
    beim ersten Log-Aufruf sterben — der Logger selbst waere dann der Fehler.
    """
    stream = sys.stderr
    return stream is not None and hasattr(stream, "write")


def setup_logging(level: int = logging.INFO,
                  app_slug: str = APP_SLUG,
                  console: Optional[bool] = None,
                  max_bytes: int = DEFAULT_MAX_BYTES,
                  backup_count: int = DEFAULT_BACKUP_COUNT) -> Path:
    """Richtet das Logging ein. Idempotent — ein zweiter Aufruf verdoppelt nichts.

    Args:
        console: None = automatisch (nur wenn ein Stream existiert).
                 True/False erzwingt.

    Returns:
        Pfad der Logdatei.
    """
    target = log_file(app_slug)
    target.parent.mkdir(parents=True, exist_ok=True)

    root = logging.getLogger()
    root.setLevel(level)

    # Idempotenz: Beim zweiten Aufruf nicht noch einen Handler anhaengen —
    # sonst steht am Ende jede Zeile doppelt im Log.
    for handler in root.handlers:
        if getattr(handler, "_app_logging", False):
            return target

    formatter = logging.Formatter(LOG_FORMAT)

    file_handler = logging.handlers.RotatingFileHandler(
        target, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8")
    file_handler.setFormatter(formatter)
    file_handler._app_logging = True          # type: ignore[attr-defined]
    root.addHandler(file_handler)

    use_console = _has_console() if console is None else console
    if use_console and _has_console():
        # Die Konsole ist auf Windows haeufig cp1252. Ein Umlaut oder ein
        # Gedankenstrich im Logtext loest dort eine UnicodeEncodeError-Kaskade
        # aus — ausgerechnet beim Melden eines Fehlers. errors="replace" macht
        # daraus ein harmloses Ersatzzeichen. Die DATEI bleibt UTF-8 und damit
        # vollstaendig: Man verliert hoechstens ein Zeichen auf der Konsole,
        # nie eine Zeile im Log.
        try:
            sys.stderr.reconfigure(errors="replace")   # Python >= 3.7
        except (AttributeError, ValueError):           # pragma: no cover
            pass
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        stream_handler._app_logging = True    # type: ignore[attr-defined]
        root.addHandler(stream_handler)

    return target


def install_crash_handler(app_slug: str = APP_SLUG) -> None:
    """Schreibt unbehandelte Ausnahmen ins Log statt nach stderr.

    OHNE DAS IST DAS LOG FAST WERTLOS: Ein Absturz geht standardmaessig nach
    stderr — und stderr ist unter `pythonw` ins Nichts. Genau der Fall, fuer den
    man das Log gebaut hat, waere der einzige, den es nicht faengt.

    `KeyboardInterrupt` wird durchgereicht: Ein Strg+C ist kein Absturz.
    """
    logger = logging.getLogger(app_slug)

    def _hook(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        logger.critical("Unbehandelte Ausnahme - die App bricht ab.",
                        exc_info=(exc_type, exc_value, exc_traceback))

    sys.excepthook = _hook

    # Threads haben ihren EIGENEN Hook (Python >= 3.8). Ohne diesen zweiten
    # Haken stirbt ein Worker-Thread lautlos — und die App wirkt nur "haengt",
    # ohne eine Spur zu hinterlassen.
    if hasattr(sys, "excepthook") and hasattr(sys, "__excepthook__"):
        import threading

        def _thread_hook(args):
            if issubclass(args.exc_type, KeyboardInterrupt):
                return
            logger.critical("Unbehandelte Ausnahme in Thread %r.",
                            args.thread.name if args.thread else "?",
                            exc_info=(args.exc_type, args.exc_value,
                                      args.exc_traceback))

        threading.excepthook = _thread_hook


def start(level: int = logging.INFO, app_slug: str = APP_SLUG) -> Path:
    """Der eine Aufruf, den jede App als ERSTES macht.

        from .runtime.app_logging import start
        start()

    Richtet Logging ein UND haengt den Crash-Handler ein. Beides zusammen, weil
    das eine ohne das andere die Haelfte der Faelle verfehlt.
    """
    target = setup_logging(level=level, app_slug=app_slug)
    install_crash_handler(app_slug=app_slug)
    logging.getLogger(app_slug).info("Start. Log: %s", target)
    return target
