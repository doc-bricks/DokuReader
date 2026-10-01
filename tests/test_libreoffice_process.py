"""Real process lifetime probes; only test-owned processes/files are used."""
import os
import ctypes
import json
from pathlib import Path
import subprocess
import sys
import time

import pytest

import libreoffice_process as office


def running(pid):
    if os.name == "nt":
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.OpenProcess.argtypes = [ctypes.c_ulong, ctypes.c_int, ctypes.c_ulong]
        kernel.OpenProcess.restype = ctypes.c_void_p
        kernel.WaitForSingleObject.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
        kernel.CloseHandle.argtypes = [ctypes.c_void_p]
        handle = kernel.OpenProcess(0x100000, False, pid)
        if not handle:
            assert ctypes.get_last_error() == 87
            return False
        try:
            status = kernel.WaitForSingleObject(handle, 0)
            assert status in (0, 258), "Process wait failed; termination is unproven"
            return status == 258
        finally:
            kernel.CloseHandle(handle)
    result = subprocess.run(["ps", "-p", str(pid), "-o", "stat="],
                            capture_output=True, text=True, timeout=2)
    state = result.stdout.strip()
    assert result.returncode in (0, 1), result.stderr
    assert result.returncode != 0 or state, "Empty process state is not termination proof"
    return bool(state) and not state.startswith("Z")


@pytest.mark.parametrize("mode", ["timeout", "success", "nonzero"])
def test_descendant_pipes_do_not_extend_deadline(tmp_path, mode):
    marker = tmp_path / "descendant.pid"
    child = tmp_path / "Öl & child.py"
    child.write_text("import os,sys,time; from pathlib import Path; "
                     "p=Path(sys.argv[1]); staging=p.with_suffix('.tmp'); "
                     "staging.write_text(str(os.getpid())); os.replace(staging,p); time.sleep(8)", encoding="utf-8")
    script = tmp_path / "Ärzte converter.py"
    script.write_text('''import subprocess, sys, time
from pathlib import Path
subprocess.Popen([sys.executable, sys.argv[1], sys.argv[3]])
while not Path(sys.argv[3]).exists():
    time.sleep(0.01)
if sys.argv[2] == "timeout":
    time.sleep(10)
raise SystemExit(7 if sys.argv[2] == "nonzero" else 0)
''', encoding="utf-8")
    reference = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"])
    try:
        started = time.monotonic()
        result = office.run_libreoffice_process([sys.executable, str(script), str(child), mode, str(marker)], timeout=3)
        assert result is (mode == "success")
        assert time.monotonic() - started < 6
        assert marker.exists()
        pid = int(marker.read_text())
        deadline = time.monotonic() + 1
        while running(pid) and time.monotonic() < deadline:
            time.sleep(0.02)
        assert not running(pid), "Owned descendant survived runner cleanup"
        assert reference.poll() is None
    finally:
        reference.kill()
        reference.wait(timeout=5)


def test_start_failure_is_not_success(tmp_path):
    try:
        result = office.run_libreoffice_process([str(tmp_path / "missing executable")], timeout=1)
    except OSError:
        return
    assert result is False


@pytest.mark.skipif(os.name == "nt", reason="POSIX supervisor identity")
def test_crashed_unreaped_supervisor_still_allows_group_cleanup(tmp_path):
    marker = tmp_path / "pids.json"
    script = tmp_path / "converter.py"
    script.write_text('''import json, os, signal, subprocess, sys, time
from pathlib import Path
child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(8)"])
p = Path(sys.argv[1])
staging = p.with_suffix('.tmp')
staging.write_text(json.dumps([os.getpid(), child.pid]))
os.replace(staging, p)
os.kill(os.getppid(), signal.SIGKILL)
time.sleep(8)
''', encoding="utf-8")
    started = time.monotonic()
    assert office.run_libreoffice_process([sys.executable, str(script), str(marker)], timeout=3) is False
    assert time.monotonic() - started < 6
    assert marker.exists()
    for pid in json.loads(marker.read_text()):
        deadline = time.monotonic() + 1
        while running(pid) and time.monotonic() < deadline:
            time.sleep(0.02)
        assert not running(pid)


@pytest.mark.skipif(os.name == "nt", reason="POSIX process group protocol")
def test_signal_happens_before_leader_reaping(tmp_path, monkeypatch):
    events = []

    class Process:
        pid = 123

        def wait(self, timeout):
            events.append("wait")
            assert timeout == 5

        def poll(self):
            pytest.fail("Leader must never be polled before group termination")

    monkeypatch.setattr(office.subprocess, "Popen", lambda *args, **kwargs: Process())
    monkeypatch.setattr(office.os, "killpg", lambda pid, sig: events.append("signal"))
    assert office.run_libreoffice_process(["unused"], timeout=0) is False
    assert events == ["signal", "wait"]


@pytest.mark.skipif(os.name == "nt", reason="POSIX child auto-reaping")
def test_custom_sigchld_handler_is_rejected_before_start(monkeypatch):
    monkeypatch.setattr(office.signal, "getsignal", lambda sig: office.signal.SIG_IGN)
    monkeypatch.setattr(office.subprocess, "Popen", lambda *args, **kwargs: pytest.fail("Unsafe leader started"))
    with pytest.raises(OSError, match="SIGCHLD"):
        office.run_libreoffice_process(["unused"])


@pytest.mark.skipif(os.name == "nt", reason="POSIX session ownership")
def test_unisolated_helper_cannot_spawn_or_signal(tmp_path, monkeypatch):
    monkeypatch.setattr(office.os, "getsid", lambda pid: os.getpid() + 1)
    monkeypatch.setattr(office.os, "killpg", lambda *args: pytest.fail("Foreign group signalled"))
    monkeypatch.setattr(office.subprocess, "Popen", lambda *args, **kwargs: pytest.fail("Unisolated child started"))
    assert office.helper_main([str(tmp_path / "result"), str(os.getppid()), "unused"]) == 1


@pytest.mark.skipif(os.name == "nt", reason="POSIX supervisor parent death")
def test_parent_death_stops_its_session(tmp_path):
    marker = tmp_path / "pids.json"
    converter = tmp_path / "converter.py"
    converter.write_text('''import json, os, sys, time
from pathlib import Path
p = Path(sys.argv[1])
staging = p.with_suffix('.tmp')
staging.write_text(json.dumps([os.getppid(), os.getpid()]))
os.replace(staging, p)
time.sleep(15)
''', encoding="utf-8")
    program = "import sys; from libreoffice_process import run_libreoffice_process; run_libreoffice_process(sys.argv[1:], timeout=20)"
    owner = subprocess.Popen([sys.executable, "-c", program, sys.executable, str(converter), str(marker)],
                             cwd=Path(office.__file__).parent)
    pids = []
    try:
        deadline = time.monotonic() + 5
        while not marker.exists() and time.monotonic() < deadline:
            time.sleep(0.02)
        assert marker.exists()
        pids = json.loads(marker.read_text())
        owner.kill()
        owner.wait(timeout=5)
        deadline = time.monotonic() + 3
        while any(running(pid) for pid in pids) and time.monotonic() < deadline:
            time.sleep(0.02)
        assert all(not running(pid) for pid in pids)
    finally:
        if owner.poll() is None:
            owner.kill()
            owner.wait(timeout=5)
        if pids and running(pids[0]):
            # A failed probe may leave its known helper alive. Confirm the unique
            # scratch converter argument and group leadership before cleanup.
            command = subprocess.run(["ps", "-p", str(pids[0]), "-o", "command="],
                                     capture_output=True, text=True, timeout=2).stdout
            assert str(converter) in command and os.getpgid(pids[0]) == pids[0]
            os.killpg(pids[0], office.signal.SIGKILL)


def test_frozen_helper_command_preserves_argument_boundaries(tmp_path, monkeypatch):
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    result = tmp_path / "Ärzte result.json"
    command = ["space & executable", "Öl # 100% argument"]
    assert office.helper_command(result, command) == [
        sys.executable, "--libreoffice-process-helper", str(result), str(os.getpid()), *command]


def test_early_helper_path_does_not_import_gui():
    source = Path(office.__file__).with_name("DokuReader.py")
    program = '''import builtins,runpy,sys
original = builtins.__import__
def guarded(name, *args, **kwargs):
    if name.startswith(("tkinter", "PIL", "fitz")):
        raise AssertionError("GUI import in helper")
    return original(name,*args,**kwargs)
builtins.__import__ = guarded
sys.argv = [sys.argv[1], "--libreoffice-process-helper"]
runpy.run_path(sys.argv[0], run_name="__main__")
'''
    result = subprocess.run([sys.executable, "-c", program, str(source)],
                            capture_output=True, timeout=10)
    assert result.returncode == 1
    assert not result.stderr
