"""Start the current desktop source with the standard runtime log already active."""
import ctypes
import logging
import os
from pathlib import Path
import runpy
import sys

ROOT = Path(__file__).resolve().parent


class LogStream:
    encoding = "utf-8"

    def __init__(self, logger, level):
        self.logger, self.level = logger, level

    def write(self, value):
        if value.rstrip("\r\n"):
            self.logger.log(self.level, "%s", value.rstrip("\r\n"))
        return len(value)

    def flush(self):
        for handler in logging.getLogger().handlers:
            handler.flush()

    def isatty(self):
        return False


def show_error(message):
    if os.name == "nt":
        ctypes.windll.user32.MessageBoxW(None, message, "DokuReader – Startfehler", 0x10)


def main(argv=None):
    debug = "--debug" in (sys.argv[1:] if argv is None else argv)
    target = None
    original_stdout, original_stderr = sys.stdout, sys.stderr
    try:
        # File-handler failures must not recursively write through LogStream.
        logging.raiseExceptions = False
        from runtime import app_logging
        target = app_logging.setup_logging(app_slug="DokuReader", console=debug)
        app_logging.install_crash_handler(app_slug="DokuReader")
        logger = logging.getLogger("DokuReader")
        sys.stdout = LogStream(logger, logging.INFO)
        sys.stderr = LogStream(logger, logging.ERROR)
        source = ROOT / "DokuReader.py"
        if not source.is_file():
            raise FileNotFoundError(f"Aktueller Quellcode fehlt: {source}")
        logger.info("Source start: %s; Python: %s", source, sys.executable)
        os.chdir(ROOT)
        sys.path.insert(0, str(ROOT))
        sys.argv = [str(source)]
        try:
            runpy.run_path(str(source), run_name="__main__")
        except SystemExit as exc:
            if exc.code not in (None, 0):
                raise RuntimeError(f"DokuReader wurde mit Fehler beendet: {exc.code}") from exc
        logger.info("Source stopped successfully")
        return 0
    except Exception:
        if target is not None:
            logging.getLogger("DokuReader").exception("DokuReader konnte nicht gestartet werden.")
        elif original_stderr is not None:
            import traceback
            traceback.print_exc(file=original_stderr)
        message = "DokuReader konnte nicht gestartet werden."
        message += f"\n\nProtokoll: {target}" if target is not None else "\nDas lokale Startprotokoll konnte nicht angelegt werden."
        message += "\nBitte debug.bat zur Fehlersuche öffnen."
        if not debug:
            show_error(message)
        return 1
    finally:
        sys.stdout, sys.stderr = original_stdout, original_stderr
        logging.shutdown()


if __name__ == "__main__":
    raise SystemExit(main())
