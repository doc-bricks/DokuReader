"""Bound an owned LibreOffice job/session without inherited output pipes."""
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time

from office_conversion import run_windows_job


def helper_command(result, command):
    if getattr(sys, "frozen", False):
        prefix = [sys.executable, "--libreoffice-process-helper"]
    else:
        prefix = [sys.executable, str(Path(__file__).resolve())]
    return prefix + [str(result), str(os.getpid()), *command]


def run_libreoffice_process(command, timeout=180):
    """Return success only after owned cleanup; raise on cleanup failure.

    POSIX targets stay in a private session. Detached descendants are outside
    that boundary; only the directly owned session leader can be reaped here.
    """
    if os.name == "nt":
        return run_windows_job(command, timeout)
    if signal.getsignal(signal.SIGCHLD) != signal.SIG_DFL:
        raise OSError("Owned process groups require the default SIGCHLD handler")
    with tempfile.TemporaryDirectory(prefix="dokureader-lo-process-") as temporary:
        result = Path(temporary) / "result.json"
        started = time.monotonic()
        process = subprocess.Popen(helper_command(result, command), start_new_session=True,
                                   stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                   stderr=subprocess.DEVNULL)
        succeeded = False
        try:
            while time.monotonic() - started < timeout:
                if result.exists():
                    code = json.loads(result.read_text(encoding="utf-8"))
                    succeeded = type(code) is int and code == 0
                    break
                time.sleep(0.02)
        finally:
            # Never poll/wait/reap the leader before this signal. Even a crashed
            # leader reserves its PID while unreaped, preventing PGID reuse.
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            finally:
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired as exc:
                    raise OSError("Owned LibreOffice supervisor did not exit") from exc
        return succeeded


def helper_main(argv):
    """Report converter exit atomically, retain the leader until parent cleanup."""
    if os.name == "nt" or len(argv) < 3:
        return 1
    result, parent, command = Path(argv[0]), int(argv[1]), argv[2:]
    if (os.getsid(0) != os.getpid() or os.getpgrp() != os.getpid()
            or parent <= 0 or os.getppid() != parent):
        return 1
    try:
        child = subprocess.Popen(command, stdin=subprocess.DEVNULL,
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        while child.poll() is None:
            if os.getppid() != parent:
                os.killpg(os.getpgrp(), signal.SIGKILL)
            time.sleep(0.02)
        code = child.returncode
    except OSError:
        code = -1
    staging = result.with_suffix(".tmp")
    staging.write_text(json.dumps(code), encoding="utf-8")
    os.replace(staging, result)
    while True:
        if os.getppid() != parent:
            os.killpg(os.getpgrp(), signal.SIGKILL)
        time.sleep(0.02)


if __name__ == "__main__":
    raise SystemExit(helper_main(sys.argv[1:]))
