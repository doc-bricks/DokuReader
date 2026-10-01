"""Bound Word automation inside an owned Windows process job."""
import ctypes
from ctypes import wintypes
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

WORD_TIMEOUT_SECONDS = 180


def _is_windows():
    return os.name == "nt"


def run_windows_job(command, timeout):
    """Start in a kill-on-close job, terminate it and wait for observed handles."""
    if not _is_windows():
        raise OSError("Windows process jobs are unavailable")
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)

    class StartupInfo(ctypes.Structure):
        _fields_ = [("cb", wintypes.DWORD), ("lpReserved", wintypes.LPWSTR),
                    ("lpDesktop", wintypes.LPWSTR), ("lpTitle", wintypes.LPWSTR),
                    ("dwX", wintypes.DWORD), ("dwY", wintypes.DWORD),
                    ("dwXSize", wintypes.DWORD), ("dwYSize", wintypes.DWORD),
                    ("dwXCountChars", wintypes.DWORD), ("dwYCountChars", wintypes.DWORD),
                    ("dwFillAttribute", wintypes.DWORD), ("dwFlags", wintypes.DWORD),
                    ("wShowWindow", wintypes.WORD), ("cbReserved2", wintypes.WORD),
                    ("lpReserved2", ctypes.POINTER(ctypes.c_byte)),
                    ("hStdInput", wintypes.HANDLE), ("hStdOutput", wintypes.HANDLE),
                    ("hStdError", wintypes.HANDLE)]

    class StartupInfoEx(ctypes.Structure):
        _fields_ = [("StartupInfo", StartupInfo), ("lpAttributeList", ctypes.c_void_p)]

    class ProcessInfo(ctypes.Structure):
        _fields_ = [("hProcess", wintypes.HANDLE), ("hThread", wintypes.HANDLE),
                    ("dwProcessId", wintypes.DWORD), ("dwThreadId", wintypes.DWORD)]

    class BasicLimits(ctypes.Structure):
        _fields_ = [("PerProcessUserTimeLimit", ctypes.c_longlong),
                    ("PerJobUserTimeLimit", ctypes.c_longlong), ("LimitFlags", wintypes.DWORD),
                    ("MinimumWorkingSetSize", ctypes.c_size_t),
                    ("MaximumWorkingSetSize", ctypes.c_size_t),
                    ("ActiveProcessLimit", wintypes.DWORD), ("Affinity", ctypes.c_size_t),
                    ("PriorityClass", wintypes.DWORD), ("SchedulingClass", wintypes.DWORD)]

    class ExtendedLimits(ctypes.Structure):
        _fields_ = [("BasicLimitInformation", BasicLimits),
                    ("IoInfo", ctypes.c_ulonglong * 6),
                    ("ProcessMemoryLimit", ctypes.c_size_t), ("JobMemoryLimit", ctypes.c_size_t),
                    ("PeakProcessMemoryUsed", ctypes.c_size_t),
                    ("PeakJobMemoryUsed", ctypes.c_size_t)]

    class Accounting(ctypes.Structure):
        _fields_ = [("times", ctypes.c_longlong * 4), ("TotalPageFaultCount", wintypes.DWORD),
                    ("TotalProcesses", wintypes.DWORD), ("ActiveProcesses", wintypes.DWORD),
                    ("TotalTerminatedProcesses", wintypes.DWORD)]

    signatures = {
        "CreateJobObjectW": ([ctypes.c_void_p, wintypes.LPCWSTR], wintypes.HANDLE),
        "SetInformationJobObject": ([wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD], wintypes.BOOL),
        "QueryInformationJobObject": ([wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD, ctypes.c_void_p], wintypes.BOOL),
        "InitializeProcThreadAttributeList": ([ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD, ctypes.POINTER(ctypes.c_size_t)], wintypes.BOOL),
        "UpdateProcThreadAttribute": ([ctypes.c_void_p, wintypes.DWORD, ctypes.c_size_t, ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p, ctypes.c_void_p], wintypes.BOOL),
        "DeleteProcThreadAttributeList": ([ctypes.c_void_p], None),
        "CreateProcessW": ([wintypes.LPCWSTR, wintypes.LPWSTR, ctypes.c_void_p, ctypes.c_void_p, wintypes.BOOL, wintypes.DWORD, ctypes.c_void_p, wintypes.LPCWSTR, ctypes.POINTER(StartupInfoEx), ctypes.POINTER(ProcessInfo)], wintypes.BOOL),
        "WaitForSingleObject": ([wintypes.HANDLE, wintypes.DWORD], wintypes.DWORD),
        "GetExitCodeProcess": ([wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)], wintypes.BOOL),
        "TerminateJobObject": ([wintypes.HANDLE, wintypes.UINT], wintypes.BOOL),
        "CloseHandle": ([wintypes.HANDLE], wintypes.BOOL),
        "OpenProcess": ([wintypes.DWORD, wintypes.BOOL, wintypes.DWORD], wintypes.HANDLE),
        "IsProcessInJob": ([wintypes.HANDLE, wintypes.HANDLE, ctypes.POINTER(wintypes.BOOL)], wintypes.BOOL),
    }
    for name, (arguments, result) in signatures.items():
        function = getattr(kernel, name)
        function.argtypes, function.restype = arguments, result

    def check(value):
        if not value:
            raise ctypes.WinError(ctypes.get_last_error())
        return value

    job = check(kernel.CreateJobObjectW(None, None))
    process = ProcessInfo()
    attributes = None
    initialized = False
    succeeded = False
    member_handles = []
    try:
        limits = ExtendedLimits()
        limits.BasicLimitInformation.LimitFlags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        check(kernel.SetInformationJobObject(job, 9, ctypes.byref(limits), ctypes.sizeof(limits)))
        size = ctypes.c_size_t()
        kernel.InitializeProcThreadAttributeList(None, 1, 0, ctypes.byref(size))
        if not size.value:
            raise ctypes.WinError(ctypes.get_last_error())
        attributes = ctypes.create_string_buffer(size.value)
        check(kernel.InitializeProcThreadAttributeList(attributes, 1, 0, ctypes.byref(size)))
        initialized = True
        jobs = (wintypes.HANDLE * 1)(job)
        check(kernel.UpdateProcThreadAttribute(attributes, 0, 0x2000D, jobs,
                                              ctypes.sizeof(jobs), None, None))
        startup = StartupInfoEx()
        startup.StartupInfo.cb = ctypes.sizeof(startup)
        startup.StartupInfo.dwFlags = 1  # STARTF_USESHOWWINDOW
        startup.StartupInfo.wShowWindow = 0  # SW_HIDE
        startup.lpAttributeList = ctypes.cast(attributes, ctypes.c_void_p)
        command_line = ctypes.create_unicode_buffer(subprocess.list2cmdline(command))
        check(kernel.CreateProcessW(command[0], command_line, None, None, False,
                                    0x80000 | 0x08000000, None, None,
                                    ctypes.byref(startup), ctypes.byref(process)))
        wait_result = kernel.WaitForSingleObject(process.hProcess, max(1, int(timeout * 1000)))
        if wait_result == 0:
            exit_code = wintypes.DWORD()
            check(kernel.GetExitCodeProcess(process.hProcess, ctypes.byref(exit_code)))
            succeeded = exit_code.value == 0
        elif wait_result != 258:  # WAIT_TIMEOUT
            raise ctypes.WinError(ctypes.get_last_error())
    finally:
        deadline = time.monotonic() + 5
        try:
            try:
                capacity = 16
                while True:
                    if capacity > 4096 or time.monotonic() >= deadline:
                        raise OSError("Cannot inspect owned conversion processes within cleanup deadline")
                    members = ctypes.create_string_buffer(8 + capacity * ctypes.sizeof(ctypes.c_size_t))
                    result = kernel.QueryInformationJobObject(job, 3, members, len(members), None)
                    if result:
                        break
                    if ctypes.get_last_error() != 234:  # ERROR_MORE_DATA
                        check(result)
                    capacity = max(capacity * 2, wintypes.DWORD.from_buffer(members).value)
                count = wintypes.DWORD.from_buffer(members, 4).value
                ids = (ctypes.c_size_t * count).from_buffer(members, 8)
                for pid in ids:
                    if time.monotonic() >= deadline:
                        raise OSError("Owned conversion process inspection exceeded cleanup deadline")
                    if pid == process.dwProcessId:
                        continue
                    handle = kernel.OpenProcess(0x100000 | 0x400, False, pid)
                    if not handle:
                        if ctypes.get_last_error() == 87:  # Process already exited
                            continue
                        check(handle)
                    belongs = wintypes.BOOL()
                    try:
                        check(kernel.IsProcessInJob(handle, job, ctypes.byref(belongs)))
                    except Exception:
                        kernel.CloseHandle(handle)
                        raise
                    if belongs.value:
                        member_handles.append(handle)
                    else:
                        kernel.CloseHandle(handle)
            finally:
                # Includes Word and descendants even when the helper exited first.
                check(kernel.TerminateJobObject(job, 1))
            for handle in [process.hProcess, *member_handles]:
                if not handle:
                    continue
                wait_result = kernel.WaitForSingleObject(handle, max(0, int((deadline - time.monotonic()) * 1000)))
                if wait_result != 0:
                    raise OSError("Owned Word conversion process did not exit")
            while True:
                accounting = Accounting()
                check(kernel.QueryInformationJobObject(job, 1, ctypes.byref(accounting),
                                                       ctypes.sizeof(accounting), None))
                if not accounting.ActiveProcesses:
                    break
                if time.monotonic() >= deadline:
                    raise OSError("Owned Word conversion processes did not exit")
                time.sleep(0.01)
        finally:
            for handle in (process.hThread, process.hProcess, *member_handles, job):
                if handle:
                    kernel.CloseHandle(handle)
            if initialized:
                kernel.DeleteProcThreadAttributeList(attributes)
    return succeeded


def helper_command(source, output):
    executable = [sys.executable]
    if not getattr(sys, "frozen", False):
        executable.append(str(Path(__file__).with_name("DokuReader.py")))
    return executable + ["--word-conversion-helper", str(source), str(output)]


def convert_word_to_pdf(source, directory):
    if not _is_windows():
        return None
    try:
        with tempfile.TemporaryDirectory(prefix=".dokureader-word-", dir=directory) as temporary:
            output = Path(temporary) / "converted.pdf"
            if not run_windows_job(helper_command(Path(source).resolve(), output), WORD_TIMEOUT_SECONDS):
                return None
            if not valid_pdf(output):
                return None
            destination = Path(directory) / (Path(source).stem + ".pdf")
            os.replace(output, destination)
            return str(destination)
    except (OSError, ValueError, ImportError):
        return None


def valid_pdf(path):
    """Accept only a newly written PDF with at least one readable page."""
    try:
        try:
            from pypdf import PdfReader
        except ImportError:
            from PyPDF2 import PdfReader
        with open(path, "rb") as stream:
            return bool(PdfReader(stream, strict=True).pages)
    except Exception:
        return False


def _word_executable():
    import winreg
    for hive in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
        for view in (winreg.KEY_WOW64_64KEY, winreg.KEY_WOW64_32KEY):
            try:
                with winreg.OpenKey(hive, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\WINWORD.EXE",
                                    0, winreg.KEY_READ | view) as key:
                    path, _ = winreg.QueryValueEx(key, None)
                if Path(path).is_file():
                    return path
            except OSError:
                pass
    return shutil.which("WINWORD.EXE")


def _owned_word_application(process):
    import pythoncom
    import win32com.client
    import win32gui
    import win32process
    windows = []

    def collect(hwnd, _):
        if win32process.GetWindowThreadProcessId(hwnd)[1] == process.pid:
            def collect_child(child, _):
                if win32gui.GetClassName(child) == "_WwG":
                    windows.append(child)
            win32gui.EnumChildWindows(hwnd, collect_child, None)

    win32gui.EnumWindows(collect, None)
    for hwnd in windows:
        if process.poll() is not None:
            return None
        if win32process.GetWindowThreadProcessId(hwnd)[1] != process.pid:
            continue
        result = win32gui.SendMessage(hwnd, 0x003D, 0, -16)  # WM_GETOBJECT / OBJID_NATIVEOM
        if not result:
            continue
        native = pythoncom.ObjectFromLresult(result, pythoncom.IID_IDispatch, 0)
        window = win32com.client.Dispatch(native)
        application = window.Application
        if (process.poll() is None
                and win32process.GetWindowThreadProcessId(window.Hwnd)[1] == process.pid
                and win32process.GetWindowThreadProcessId(application.ActiveWindow.Hwnd)[1] == process.pid):
            return application
    return None


def word_helper_main(arguments):
    """All COM calls run here; the parent bounds and owns the whole process job."""
    if not _is_windows() or len(arguments) != 2:
        return 2
    source, output = map(Path, arguments)
    word = document = process = None
    initialized = False
    try:
        import pythoncom
        executable = _word_executable()
        if not executable:
            return 1
        pythoncom.CoInitializeEx(pythoncom.COINIT_APARTMENTTHREADED)
        initialized = True
        startup = subprocess.STARTUPINFO()
        startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startup.wShowWindow = 0
        # /w is Word's documented separate instance with a blank document.
        process = subprocess.Popen([executable, "/w"], startupinfo=startup,
                                   stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                   stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW)
        while process.poll() is None:
            word = _owned_word_application(process)
            if word is not None:
                break
            time.sleep(0.05)
        if word is None:
            return 1
        word.Visible = False
        word.DisplayAlerts = 0
        word.AutomationSecurity = 3  # msoAutomationSecurityForceDisable
        document = word.Documents.Open(str(source), ReadOnly=True, AddToRecentFiles=False)
        document.ExportAsFixedFormat(str(output), 17)  # wdExportFormatPDF
        return 0 if output.is_file() and output.stat().st_size else 1
    except Exception:
        return 1
    finally:
        # These may block too; the parent deadline covers the entire helper.
        try:
            if document is not None:
                document.Close(False)
        finally:
            try:
                if word is not None:
                    word.Quit(False)
            finally:
                if initialized:
                    pythoncom.CoUninitialize()
