"""Bounded conversion, private outputs and native Windows process ownership."""
import ctypes
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
from types import ModuleType, SimpleNamespace

import pytest
from pypdf import PdfWriter

import office_conversion as office


def write_pdf(path):
    with PdfWriter() as writer:
        writer.add_blank_page(width=200, height=200)
        writer.write(path)


@pytest.mark.parametrize("result", [False, True])
def test_timeout_or_incomplete_output_keeps_existing_conversion(tmp_path, monkeypatch, result):
    source = tmp_path / "document.docx"
    source.write_bytes(b"original source")
    destination = tmp_path / "document.pdf"
    write_pdf(destination)
    before = destination.read_bytes()

    def run(command, timeout):
        assert timeout == 180
        output = Path(command[-1])
        output.write_bytes(b"%PDF-incomplete")
        return result

    monkeypatch.setattr(office, "_is_windows", lambda: True)
    monkeypatch.setattr(office, "run_windows_job", run)
    assert office.convert_word_to_pdf(source, tmp_path) is None
    assert source.read_bytes() == b"original source"
    assert destination.read_bytes() == before
    assert not list(tmp_path.glob(".dokureader-word-*"))


def test_success_requires_readable_pdf_and_job_completion(tmp_path, monkeypatch):
    source = tmp_path / "document.docx"
    source.write_bytes(b"source")

    def run(command, timeout):
        assert timeout == 180
        write_pdf(Path(command[-1]))
        return True

    monkeypatch.setattr(office, "_is_windows", lambda: True)
    monkeypatch.setattr(office, "run_windows_job", run)
    result = office.convert_word_to_pdf(source, tmp_path)
    assert result == str(tmp_path / "document.pdf")
    assert office.valid_pdf(result)
    assert not list(tmp_path.glob(".dokureader-word-*"))


def test_start_failure_removes_private_directory(tmp_path, monkeypatch):
    def fail(*_):
        raise OSError("Job assignment rejected")

    monkeypatch.setattr(office, "_is_windows", lambda: True)
    monkeypatch.setattr(office, "run_windows_job", fail)
    assert office.convert_word_to_pdf(tmp_path / "source.docx", tmp_path) is None
    assert list(tmp_path.iterdir()) == []


def test_frozen_command_uses_executable_without_source_script(monkeypatch):
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    command = office.helper_command("source.docx", "output.pdf")
    assert command == [sys.executable, "--word-conversion-helper", "source.docx", "output.pdf"]


def test_helper_entry_precedes_tk_imports():
    script = """
import importlib.abc, runpy, sys
class BlockTk(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path, target=None):
        if fullname == 'tkinter' or fullname.startswith('tkinter.'):
            raise AssertionError('Tk imported by Word helper')
sys.meta_path.insert(0, BlockTk())
sys.argv = [sys.argv[1], '--word-conversion-helper']
try:
    runpy.run_path(sys.argv[0], run_name='__main__')
except SystemExit as exc:
    assert exc.code == 2
else:
    raise AssertionError('helper did not exit')
"""
    result = subprocess.run([sys.executable, "-c", script, str(Path(office.__file__).with_name("DokuReader.py"))],
                            capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stderr


def test_helper_cleanup_exception_exits_without_unhandled_traceback():
    script = """
import runpy, sys, types
helper = types.ModuleType('office_conversion')
def fail(_):
    raise RuntimeError('simulated Word.Quit failure')
helper.word_helper_main = fail
sys.modules['office_conversion'] = helper
sys.argv = [sys.argv[1], '--word-conversion-helper', 'source', 'output']
try:
    runpy.run_path(sys.argv[0], run_name='__main__')
except SystemExit as exc:
    assert exc.code == 1
else:
    raise AssertionError('helper did not exit')
assert 'tkinter' not in sys.modules
"""
    result = subprocess.run([sys.executable, "-c", script, str(Path(office.__file__).with_name("DokuReader.py"))],
                            capture_output=True, text=True, timeout=10)
    assert result.returncode == 0 and result.stderr == ""


@pytest.mark.parametrize("owner", ["owned", "foreign_child", "foreign_application"])
def test_native_binding_uses_only_live_owned_window(monkeypatch, owner):
    window = SimpleNamespace(Hwnd=88, Application=SimpleNamespace(ActiveWindow=SimpleNamespace(Hwnd=99)))
    pythoncom = ModuleType("pythoncom")
    pythoncom.IID_IDispatch = object()
    native = object()
    pythoncom.ObjectFromLresult = lambda *_: native
    package, client = ModuleType("win32com"), ModuleType("win32com.client")
    calls = []

    def dispatch(value):
        assert value is native  # Never a ProgID that could activate another Word.
        calls.append(value)
        return window

    client.Dispatch = dispatch
    package.client = client
    gui, process = ModuleType("win32gui"), ModuleType("win32process")
    gui.EnumWindows = lambda callback, argument: callback(1, argument)
    gui.EnumChildWindows = lambda _, callback, argument: callback(2, argument)
    gui.GetClassName = lambda _: "_WwG"
    gui.SendMessage = lambda *_: 27
    owners = {1: 101, 2: 200 if owner == "foreign_child" else 101,
              88: 101, 99: 200 if owner == "foreign_application" else 101}
    process.GetWindowThreadProcessId = lambda hwnd: (0, owners[hwnd])
    for name, module in [("pythoncom", pythoncom), ("win32com", package),
                         ("win32com.client", client), ("win32gui", gui), ("win32process", process)]:
        monkeypatch.setitem(sys.modules, name, module)
    result = office._owned_word_application(SimpleNamespace(pid=101, poll=lambda: None))
    if owner == "owned":
        assert result is window.Application
    else:
        assert result is None
    if owner == "foreign_child":
        assert not calls


def test_office_fallback_uses_bounded_converter(tmp_path, monkeypatch):
    import DokuReader as app
    monkeypatch.setattr(app.shutil, "which", lambda _: None)
    monkeypatch.setattr(app.platform, "system", lambda: "Windows")
    calls = []
    monkeypatch.setattr(app, "convert_word_to_pdf", lambda source, directory: calls.append((source, directory)))
    assert app.App._office_to_pdf(None, "source.docx", tmp_path) is None
    assert calls == [("source.docx", tmp_path)]


windows = pytest.mark.skipif(os.name != "nt", reason="Native Windows process jobs")


@windows
def test_native_job_success_and_failure():
    assert office.run_windows_job([sys.executable, "-c", "pass"], 3) is True
    assert office.run_windows_job([sys.executable, "-c", "raise SystemExit(7)"], 3) is False


@windows
def test_native_timeout_reaps_descendants_and_preserves_unrelated_process(tmp_path):
    marker = tmp_path / "pids.json"
    script = """
import json, os, pathlib, subprocess, sys, time
child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)'], creationflags=subprocess.CREATE_NO_WINDOW)
marker = pathlib.Path(sys.argv[1])
temporary = marker.with_suffix('.tmp')
temporary.write_text(json.dumps([os.getpid(), child.pid]))
os.replace(temporary, marker)
time.sleep(30)
"""
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.OpenProcess.argtypes = [ctypes.c_ulong, ctypes.c_int, ctypes.c_ulong]
    kernel.OpenProcess.restype = ctypes.c_void_p
    kernel.WaitForSingleObject.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
    kernel.WaitForSingleObject.restype = ctypes.c_ulong
    kernel.CloseHandle.argtypes = [ctypes.c_void_p]
    handles, results = [], []
    unrelated = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"],
                                 creationflags=subprocess.CREATE_NO_WINDOW)
    worker = threading.Thread(target=lambda: results.append(office.run_windows_job(
        [sys.executable, "-c", script, str(marker)], 1.5)))
    started = time.monotonic()
    try:
        worker.start()
        deadline = time.monotonic() + 1
        while not marker.exists() and time.monotonic() < deadline:
            time.sleep(0.01)
        assert marker.exists()
        for pid in json.loads(marker.read_text()):
            handle = kernel.OpenProcess(0x100000, False, pid)  # SYNCHRONIZE
            assert handle
            handles.append(handle)
        worker.join(7)
        assert not worker.is_alive()
        assert results == [False]
        assert time.monotonic() - started < 7
        assert all(kernel.WaitForSingleObject(handle, 0) == 0 for handle in handles)
        assert unrelated.poll() is None
    finally:
        worker.join(7)
        unrelated.terminate()
        unrelated.wait(3)
        for handle in handles:
            kernel.CloseHandle(handle)


@windows
def test_native_helper_exit_cleans_surviving_descendant(tmp_path):
    marker = tmp_path / "child.json"
    script = """
import json, os, pathlib, subprocess, sys, time
child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)'], creationflags=subprocess.CREATE_NO_WINDOW)
marker = pathlib.Path(sys.argv[1])
temporary = marker.with_suffix('.tmp')
temporary.write_text(json.dumps(child.pid))
os.replace(temporary, marker)
while not marker.with_suffix('.ack').exists():
    time.sleep(.01)
"""
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.OpenProcess.argtypes = [ctypes.c_ulong, ctypes.c_int, ctypes.c_ulong]
    kernel.OpenProcess.restype = ctypes.c_void_p
    kernel.WaitForSingleObject.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
    kernel.WaitForSingleObject.restype = ctypes.c_ulong
    kernel.CloseHandle.argtypes = [ctypes.c_void_p]
    results = []
    handle = None
    worker = threading.Thread(target=lambda: results.append(office.run_windows_job(
        [sys.executable, "-c", script, str(marker)], 5)))
    try:
        worker.start()
        deadline = time.monotonic() + 3
        while not marker.exists() and time.monotonic() < deadline:
            time.sleep(.01)
        assert marker.exists()
        handle = kernel.OpenProcess(0x100000, False, json.loads(marker.read_text()))
        assert handle
        marker.with_suffix('.ack').touch()
        worker.join(7)
        assert results == [True]
        assert kernel.WaitForSingleObject(handle, 0) == 0
    finally:
        worker.join(7)
        if handle:
            kernel.CloseHandle(handle)


@windows
def test_rejected_atomic_job_assignment_never_starts_helper(tmp_path, monkeypatch):
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    marker = tmp_path / "unexpected.txt"

    def reject(*_):
        ctypes.set_last_error(5)
        return 0

    class RejectAssignment:
        def __getattr__(self, name):
            if name == "UpdateProcThreadAttribute":
                return reject
            return getattr(kernel, name)

    monkeypatch.setattr(office.ctypes, "WinDLL", lambda *_, **__: RejectAssignment())
    with pytest.raises(OSError):
        office.run_windows_job([sys.executable, "-c", "import pathlib,sys;pathlib.Path(sys.argv[1]).touch()",
                                str(marker)], 1)
    assert not marker.exists()


@windows
def test_parent_crash_closes_job_and_ends_helper_and_child(tmp_path):
    marker = tmp_path / "crash-pids.json"
    helper = """
import json, os, pathlib, subprocess, sys, time
child = subprocess.Popen([sys.executable, '-c', 'import time;time.sleep(30)'], creationflags=subprocess.CREATE_NO_WINDOW)
marker = pathlib.Path(sys.argv[1])
temporary = marker.with_suffix('.tmp')
temporary.write_text(json.dumps([os.getpid(), child.pid]))
os.replace(temporary, marker)
time.sleep(30)
"""
    parent_code = """
import office_conversion, sys
office_conversion.run_windows_job([sys.executable, '-c', sys.argv[1], sys.argv[2]], 30)
"""
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.OpenProcess.argtypes = [ctypes.c_ulong, ctypes.c_int, ctypes.c_ulong]
    kernel.OpenProcess.restype = ctypes.c_void_p
    kernel.WaitForSingleObject.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
    kernel.WaitForSingleObject.restype = ctypes.c_ulong
    kernel.CloseHandle.argtypes = [ctypes.c_void_p]
    handles = []
    parent = subprocess.Popen([sys.executable, "-c", parent_code, helper, str(marker)],
                              cwd=Path(office.__file__).parent, creationflags=subprocess.CREATE_NO_WINDOW)
    try:
        deadline = time.monotonic() + 3
        while not marker.exists() and time.monotonic() < deadline:
            time.sleep(.01)
        assert marker.exists()
        for pid in json.loads(marker.read_text()):
            handle = kernel.OpenProcess(0x100000, False, pid)
            assert handle
            handles.append(handle)
        parent.terminate()
        parent.wait(3)
        assert all(kernel.WaitForSingleObject(handle, 3000) == 0 for handle in handles)
    finally:
        if parent.poll() is None:
            parent.terminate()
        parent.wait(3)
        for handle in handles:
            kernel.CloseHandle(handle)


@windows
@pytest.mark.parametrize("phase", ["initialize", "binding", "open", "export", "close", "quit", "uninitialize"])
def test_deadline_covers_blocked_automation_and_teardown(tmp_path, phase):
    """Simulated COM calls in real owned Windows processes, never installed Office."""
    marker = tmp_path / "stage.json"
    script = """
import json, os, pathlib, subprocess, sys, time, types
import office_conversion as office
from pypdf import PdfWriter
phase, marker_name, output_name = sys.argv[1:]
marker, output = pathlib.Path(marker_name), pathlib.Path(output_name)
children = []
def block(name):
    if phase == name:
        temporary = marker.with_suffix('.tmp')
        temporary.write_text(json.dumps([os.getpid(), *[child.pid for child in children]]))
        os.replace(temporary, marker)
        time.sleep(30)
pythoncom = types.ModuleType('pythoncom')
pythoncom.COINIT_APARTMENTTHREADED = 2
pythoncom.CoInitializeEx = lambda _: block('initialize')
pythoncom.CoUninitialize = lambda: block('uninitialize')
sys.modules['pythoncom'] = pythoncom
class Document:
    def ExportAsFixedFormat(self, path, format):
        block('export')
        with PdfWriter() as writer:
            writer.add_blank_page(width=200, height=200)
            writer.write(path)
    def Close(self, save):
        assert save is False
        block('close')
class Documents:
    def Open(self, path, **kwargs):
        assert kwargs == {'ReadOnly': True, 'AddToRecentFiles': False}
        block('open')
        return Document()
class Word:
    Documents = Documents()
    def Quit(self, save):
        assert save is False
        block('quit')
word = Word()
original_popen = subprocess.Popen
def own_process(*args, **kwargs):
    child = original_popen([sys.executable, '-c', 'import time;time.sleep(30)'],
                           creationflags=subprocess.CREATE_NO_WINDOW)
    children.append(child)
    return child
subprocess.Popen = own_process
office._word_executable = lambda: 'own simulated Word'
def bind(process):
    block('binding')
    return word
office._owned_word_application = bind
raise SystemExit(office.word_helper_main(['own-source.docx', str(output)]))
"""
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.OpenProcess.argtypes = [ctypes.c_ulong, ctypes.c_int, ctypes.c_ulong]
    kernel.OpenProcess.restype = ctypes.c_void_p
    kernel.WaitForSingleObject.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
    kernel.WaitForSingleObject.restype = ctypes.c_ulong
    kernel.CloseHandle.argtypes = [ctypes.c_void_p]
    handles, results = [], []
    worker = threading.Thread(target=lambda: results.append(office.run_windows_job(
        [sys.executable, "-c", script, phase, str(marker), str(tmp_path / "output.pdf")], 3)))
    try:
        worker.start()
        deadline = time.monotonic() + 2
        while not marker.exists() and time.monotonic() < deadline:
            time.sleep(.01)
        assert marker.exists(), f"Automation never reached {phase}"
        for pid in json.loads(marker.read_text()):
            handle = kernel.OpenProcess(0x100000, False, pid)
            assert handle
            handles.append(handle)
        worker.join(9)
        assert not worker.is_alive()
        assert results == [False]
        assert all(kernel.WaitForSingleObject(handle, 0) == 0 for handle in handles)
    finally:
        worker.join(9)
        for handle in handles:
            kernel.CloseHandle(handle)
