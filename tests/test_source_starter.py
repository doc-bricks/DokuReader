"""Exercise starter selection and logging without touching a user library."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

import pytest

ROOT = Path(__file__).resolve().parents[1]
POWERSHELL = Path(os.environ.get("SystemRoot", "C:/Windows")) / "System32/WindowsPowerShell/v1.0/powershell.exe"


def fixture_source(tmp_path, program):
    source = tmp_path / "Ärzte & 100% !"
    source.mkdir()
    shutil.copy2(ROOT / "launch_source.py", source)
    shutil.copytree(ROOT / "runtime", source / "runtime", ignore=shutil.ignore_patterns("__pycache__"))
    (source / "DokuReader.py").write_text(program, encoding="utf-8")
    return source


def bootstrap(source, tmp_path, debug=True):
    env = dict(os.environ, LOCALAPPDATA=str(tmp_path / "logs"), PYTHONUTF8="1")
    command = [sys.executable, str(source / "launch_source.py")]
    if debug:
        command.append("--debug")
    return subprocess.run(command, env=env, capture_output=True, text=True, encoding="utf-8", timeout=15)


def test_source_streams_and_thread_crash_are_logged(tmp_path):
    source = fixture_source(tmp_path, '''import sys, threading
print("Größe: äöü")
print("stderr-marker", file=sys.stderr)
def fail():
    raise RuntimeError("thread-marker")
t = threading.Thread(target=fail)
t.start()
t.join()
raise SystemExit(0)
''')
    result = bootstrap(source, tmp_path)
    assert result.returncode == 0, result.stderr
    logs = list((tmp_path / "logs/DokuReader/logs").glob("app-*.log"))
    assert len(logs) == 1
    text = logs[0].read_text(encoding="utf-8")
    for marker in ("Größe: äöü", "stderr-marker", "thread-marker", "Source stopped successfully"):
        assert marker in text
    assert "Größe: äöü" in result.stderr


@pytest.mark.parametrize("program", ['raise RuntimeError("failure-marker")', 'raise SystemExit(7)'])
def test_debug_failure_has_nonzero_exit_and_traceback(tmp_path, program):
    source = fixture_source(tmp_path, program)
    result = bootstrap(source, tmp_path)
    assert result.returncode == 1
    assert "Traceback" in result.stderr
    assert "DokuReader konnte nicht gestartet werden" in result.stderr
    assert "Traceback" in next((tmp_path / "logs/DokuReader/logs").glob("app-*.log")).read_text(encoding="utf-8")


def test_hidden_failure_reports_message_and_logs(tmp_path):
    source = fixture_source(tmp_path, 'raise RuntimeError("hidden-failure-marker")')
    program = ('import launch_source; from pathlib import Path; '
               'launch_source.show_error = lambda text: Path("dialog.txt").write_text(text, encoding="utf-8"); '
               'raise SystemExit(launch_source.main([]))')
    result = subprocess.run([sys.executable, "-c", program], cwd=source,
                            env=dict(os.environ, LOCALAPPDATA=str(tmp_path / "logs")),
                            capture_output=True, timeout=15)
    assert result.returncode == 1
    assert "debug.bat" in (source / "dialog.txt").read_text(encoding="utf-8")
    assert "hidden-failure-marker" in next((tmp_path / "logs/DokuReader/logs").glob("app-*.log")).read_text(encoding="utf-8")


@pytest.mark.parametrize("kind", ["relative", "project", "onedrive", "absent"])
def test_log_directory_cannot_use_project_or_onedrive(tmp_path, monkeypatch, kind):
    from runtime import app_logging
    home = tmp_path / "home"
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: home))
    monkeypatch.delenv("XDG_STATE_HOME", raising=False)
    for key in ("OneDrive", "OneDriveConsumer", "OneDriveCommercial"):
        monkeypatch.delenv(key, raising=False)
    values = {"relative": "relative", "project": str(ROOT), "onedrive": str(home / "OneDrive"), "absent": ""}
    monkeypatch.setenv("LOCALAPPDATA", values[kind])
    target = app_logging.log_dir()
    assert target == home / ("AppData/Local" if os.name == "nt" else ".local/state") / "DokuReader/logs"


def check_start(bridge, debug=False):
    command = [str(POWERSHELL), "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(bridge / "start_source.ps1"), "-Check"]
    if debug:
        command.append("-Debug")
    return subprocess.run(command, capture_output=True, text=True, encoding="utf-8-sig", timeout=15)


def pointer(source):
    return {"schema": "ellmos-repo-pointer-v1", "repo_id": "doc-bricks/DokuReader", "profile": "plan-d-code", "authority": {"git": "local-checkout-plus-github"}, "local_locator": {"windows_default": str(source)}}


@pytest.mark.skipif(os.name != "nt", reason="Native Windows starter")
def test_pointer_selects_current_source_without_running_app(tmp_path):
    source = fixture_source(tmp_path, 'raise RuntimeError("must not run")')
    bridge = tmp_path / "bridge"
    bridge.mkdir()
    shutil.copy2(ROOT / "start_source.ps1", bridge)
    (bridge / "DokuReader.exe").write_bytes(b"stale exe")
    (bridge / "DokuReader.py").write_text('raise RuntimeError("stale source")')
    (bridge / "REPO.pointer.json").write_text(json.dumps(pointer(source)), encoding="utf-8")
    for debug in (False, True):
        result = check_start(bridge, debug)
        assert result.returncode == 0, result.stderr
        selected = json.loads(result.stdout)
        assert Path(selected["source_root"]) == source
        assert Path(selected["bootstrap"]) == source / "launch_source.py"
        assert Path(selected["python"]).name == ("python.exe" if debug else "pythonw.exe")
    assert not list(source.glob("*.log"))
    assert (bridge / "DokuReader.exe").read_bytes() == b"stale exe"


@pytest.mark.skipif(os.name != "nt", reason="Native Windows starter")
@pytest.mark.parametrize("invalid", ["malformed", "relative", "rootrelative", "wrongrepo", "missing"])
def test_invalid_pointer_fails_without_local_fallback(tmp_path, invalid):
    source = fixture_source(tmp_path, 'raise RuntimeError("must not run")')
    shutil.copy2(ROOT / "start_source.ps1", source)
    data = pointer(source)
    if invalid == "wrongrepo":
        data["repo_id"] = "wrong/repo"
    elif invalid != "malformed":
        data["local_locator"]["windows_default"] = {"relative": "C:relative", "rootrelative": "\\relative", "missing": str(tmp_path / "absent")}[invalid]
    (source / "REPO.pointer.json").write_text("{" if invalid == "malformed" else json.dumps(data), encoding="utf-8")
    result = check_start(source)
    assert result.returncode == 1
    assert result.stderr.strip()
    assert not result.stdout.strip()


@pytest.mark.skipif(os.name != "nt", reason="Native Windows starter")
@pytest.mark.parametrize("desktop", [False, True])
def test_batch_wsh_starts_windowless_source_in_quoted_path(tmp_path, desktop):
    program = '''import ctypes, json, os
from pathlib import Path
Path("ready.json").write_text(json.dumps({"console": ctypes.windll.kernel32.GetConsoleWindow(), "pid": os.getpid(), "cwd": str(Path.cwd())}), encoding="utf-8")
print("Fensterlos: Größe äöü")
'''
    if desktop:
        program = (f'import sys; sys.path.insert(0, {str(ROOT)!r})\n'
                   'import DokuReader\n'
                   'from pathlib import Path\n'
                   'DokuReader.STATE_FILE = str(Path.cwd() / "isolated-library.json")\n'
                   'app = DokuReader.App()\napp.update()\n' + program +
                   'app.after(100, app.on_close)\napp.mainloop()\n')
    source = fixture_source(tmp_path, program)
    bridge = tmp_path / "Öl & 100% ! bridge"
    bridge.mkdir()
    for name in ("START.bat", "launch.vbs", "start_source.ps1"):
        shutil.copy2(ROOT / name, bridge)
    (bridge / "REPO.pointer.json").write_text(json.dumps(pointer(source)), encoding="utf-8")
    env = dict(os.environ, LOCALAPPDATA=str(tmp_path / "logs"))
    command = f'"{os.environ["COMSPEC"]}" /d /s /c ""{bridge / "START.bat"}""'
    result = subprocess.run(command, env=env, capture_output=True, timeout=15)
    assert result.returncode == 0, result.stderr
    deadline = time.monotonic() + 10
    marker = source / "ready.json"
    logs = tmp_path / "logs/DokuReader/logs"
    while time.monotonic() < deadline:
        targets = list(logs.glob("app-*.log"))
        if marker.exists() and targets and "Source stopped successfully" in targets[0].read_text(encoding="utf-8"):
            break
        time.sleep(0.05)
    else:
        pytest.fail("WSH did not finish the isolated source program")
    ready = json.loads(marker.read_text(encoding="utf-8"))
    assert ready["console"] == 0
    assert Path(ready["cwd"]) == source
    assert "Fensterlos: Größe äöü" in targets[0].read_text(encoding="utf-8")
    if desktop:
        assert (source / "isolated-library.json").is_file()


def test_logging_initialization_failure_remains_observable(tmp_path):
    source = fixture_source(tmp_path, 'raise RuntimeError("must not run")')
    program = '''import launch_source
from pathlib import Path
from runtime import app_logging
def fail(**kwargs):
    raise PermissionError("log-permission-marker")
app_logging.setup_logging = fail
launch_source.show_error = lambda message: Path("dialog.txt").write_text(message, encoding="utf-8")
raise SystemExit(launch_source.main([]))
'''
    result = subprocess.run([sys.executable, "-c", program], cwd=source,
                            env=dict(os.environ, PYTHONUTF8="1"),
                            capture_output=True, text=True, encoding="utf-8", timeout=15)
    assert result.returncode == 1
    assert "log-permission-marker" in result.stderr
    assert "konnte nicht angelegt" in (source / "dialog.txt").read_text(encoding="utf-8")
    assert "must not run" not in result.stderr


@pytest.mark.skipif(os.name != "nt", reason="Native Windows starter")
def test_source_virtual_environment_is_preferred(tmp_path):
    source = fixture_source(tmp_path, 'raise RuntimeError("must not run")')
    shutil.copy2(ROOT / "start_source.ps1", source)
    created = subprocess.run([sys.executable, "-m", "venv", "--without-pip", str(source / ".venv")],
                             capture_output=True, timeout=30)
    assert created.returncode == 0, created.stderr
    result = check_start(source, debug=True)
    assert result.returncode == 0, result.stderr
    assert Path(json.loads(result.stdout)["python"]) == source / ".venv/Scripts/python.exe"
