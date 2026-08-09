"""
E.V.I.E. - System Awareness Module

Created: August 8, 2026
Last Edited: August 8, 2026
Author: Max Maehara

Purpose:
    Provides read-only awareness of the Windows desktop.

Capabilities:
    - Active application
    - Active window
    - Active process
    - Likely active file
    - Visible applications
    - Terminal detection
    - Recent PowerShell history
    - Python/build process awareness

Most Recent Change:
    Added running-application and terminal context for Phase 3.
"""

import ctypes
import os
from ctypes import wintypes
from pathlib import Path

import psutil


# ---------------------------------------------------------------------------
# Windows API
# ---------------------------------------------------------------------------

user32 = ctypes.windll.user32


# ---------------------------------------------------------------------------
# Active Window
# ---------------------------------------------------------------------------

def get_active_window_handle():
    return user32.GetForegroundWindow()


def get_window_title(hwnd):
    if not hwnd:
        return None

    length = user32.GetWindowTextLengthW(hwnd)

    if length <= 0:
        return None

    buffer = ctypes.create_unicode_buffer(
        length + 1
    )

    user32.GetWindowTextW(
        hwnd,
        buffer,
        length + 1,
    )

    title = buffer.value.strip()

    return title or None


def get_active_window_title():
    return get_window_title(
        get_active_window_handle()
    )


# ---------------------------------------------------------------------------
# Process Resolution
# ---------------------------------------------------------------------------

def get_window_process_id(hwnd):
    if not hwnd:
        return None

    process_id = wintypes.DWORD()

    user32.GetWindowThreadProcessId(
        hwnd,
        ctypes.byref(process_id),
    )

    return (
        process_id.value
        if process_id.value
        else None
    )


def get_active_process_id():
    return get_window_process_id(
        get_active_window_handle()
    )


def process_info_from_pid(pid):
    if not pid:
        return None

    try:
        process = psutil.Process(pid)

        try:
            exe = process.exe()
        except (
            psutil.AccessDenied,
            psutil.NoSuchProcess,
        ):
            exe = None

        try:
            command_line = process.cmdline()
        except (
            psutil.AccessDenied,
            psutil.NoSuchProcess,
        ):
            command_line = []

        return {
            "pid": process.pid,
            "name": process.name(),
            "exe": exe,
            "command_line": command_line,
        }

    except (
        psutil.NoSuchProcess,
        psutil.AccessDenied,
    ):
        return {
            "pid": pid,
            "name": None,
            "exe": None,
            "command_line": [],
        }


def get_active_process():
    return process_info_from_pid(
        get_active_process_id()
    )


# ---------------------------------------------------------------------------
# Active File Inference
# ---------------------------------------------------------------------------

KNOWN_FILE_EXTENSIONS = (
    ".py",
    ".vhd",
    ".vhdl",
    ".sv",
    ".v",
    ".c",
    ".cpp",
    ".h",
    ".hpp",
    ".html",
    ".css",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".json",
    ".toml",
    ".yaml",
    ".yml",
    ".md",
    ".txt",
    ".csv",
)


def infer_active_file(
    window_title: str | None,
):
    if not window_title:
        return None

    parts = [
        part.strip()
        for part in window_title.split(" - ")
    ]

    for part in parts:
        lowered = part.lower()

        if lowered.endswith(
            KNOWN_FILE_EXTENSIONS
        ):
            return part

    return None


# ---------------------------------------------------------------------------
# Visible Applications
# ---------------------------------------------------------------------------

def get_visible_applications():
    """
    Returns top-level visible Windows applications instead of
    every background Windows process.
    """

    applications = {}

    EnumWindowsProc = ctypes.WINFUNCTYPE(
        ctypes.c_bool,
        wintypes.HWND,
        wintypes.LPARAM,
    )

    def callback(
        hwnd,
        lparam,
    ):
        if not user32.IsWindowVisible(hwnd):
            return True

        title = get_window_title(hwnd)

        if not title:
            return True

        pid = get_window_process_id(hwnd)

        if not pid:
            return True

        info = process_info_from_pid(pid)

        if not info:
            return True

        name = info.get("name")

        if not name:
            return True

        key = (
            pid,
            title,
        )

        applications[key] = {
            "pid": pid,
            "process": name,
            "title": title,
        }

        return True

    user32.EnumWindows(
        EnumWindowsProc(callback),
        0,
    )

    return list(
        applications.values()
    )


# ---------------------------------------------------------------------------
# Terminal Detection
# ---------------------------------------------------------------------------

TERMINAL_PROCESSES = {
    "powershell.exe",
    "pwsh.exe",
    "cmd.exe",
    "windowsterminal.exe",
    "bash.exe",
    "wsl.exe",
}


def is_terminal_process(
    process_name: str | None,
):
    if not process_name:
        return False

    return (
        process_name.lower()
        in TERMINAL_PROCESSES
    )


# ---------------------------------------------------------------------------
# PowerShell History
# ---------------------------------------------------------------------------

def get_powershell_history_path():
    appdata = os.environ.get(
        "APPDATA"
    )

    if not appdata:
        return None

    path = (
        Path(appdata)
        / "Microsoft"
        / "Windows"
        / "PowerShell"
        / "PSReadLine"
        / "ConsoleHost_history.txt"
    )

    return path


def get_recent_powershell_history(
    limit: int = 10,
):
    path = (
        get_powershell_history_path()
    )

    if (
        path is None
        or not path.exists()
    ):
        return []

    try:
        lines = path.read_text(
            encoding="utf-8",
            errors="ignore",
        ).splitlines()

        lines = [
            line.strip()
            for line in lines
            if line.strip()
        ]

        return lines[-limit:]

    except OSError:
        return []


# ---------------------------------------------------------------------------
# Development Processes
# ---------------------------------------------------------------------------

def get_development_processes():
    """
    Returns notable processes relevant to active development.
    """

    interesting_names = {
        "python.exe",
        "pythonw.exe",
        "git.exe",
        "node.exe",
        "npm.exe",
        "ghdl.exe",
        "vivado.exe",
        "quartus.exe",
        "make.exe",
        "cmake.exe",
    }

    found = []

    for process in psutil.process_iter(
        [
            "pid",
            "name",
        ]
    ):
        try:
            name = (
                process.info.get(
                    "name"
                )
                or ""
            )

            if (
                name.lower()
                not in interesting_names
            ):
                continue

            found.append(
                {
                    "pid":
                        process.info[
                            "pid"
                        ],

                    "name":
                        name,
                }
            )

        except (
            psutil.NoSuchProcess,
            psutil.AccessDenied,
        ):
            continue

    return found


# ---------------------------------------------------------------------------
# Full System Context
# ---------------------------------------------------------------------------

def get_system_context():
    active_window = (
        get_active_window_title()
    )

    active_process = (
        get_active_process()
    )

    process_name = (
        active_process.get("name")
        if active_process
        else None
    )

    return {
        "active_window":
            active_window,

        "active_process":
            active_process,

        "active_file":
            infer_active_file(
                active_window
            ),

        "active_is_terminal":
            is_terminal_process(
                process_name
            ),

        "visible_applications":
            get_visible_applications(),

        "development_processes":
            get_development_processes(),

        "recent_terminal_history":
            get_recent_powershell_history(
                limit=10
            ),
    }


# ---------------------------------------------------------------------------
# Standalone Test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    context = get_system_context()

    print(
        "E.V.I.E. System Context"
    )

    print(
        "------------------------"
    )

    print(
        "Active window:",
        context["active_window"],
    )

    print(
        "Active process:",
        context["active_process"],
    )

    print(
        "Active file:",
        context["active_file"],
    )

    print(
        "Terminal active:",
        context[
            "active_is_terminal"
        ],
    )

    print(
        "\nVisible applications:"
    )

    for app in context[
        "visible_applications"
    ][:15]:
        print(
            f"- {app['process']}: "
            f"{app['title']}"
        )

    print(
        "\nDevelopment processes:"
    )

    for process in context[
        "development_processes"
    ]:
        print(
            f"- {process}"
        )

    print(
        "\nRecent PowerShell history:"
    )

    for command in context[
        "recent_terminal_history"
    ]:
        print(
            f"- {command}"
        )