"""
E.V.I.E. - Application Control Tools

Created: August 9, 2026
Last Edited: August 9, 2026
Author: Max Maehara

Purpose:
    Opens and focuses approved desktop applications.

Security:
    Only applications explicitly defined in APPROVED_APPLICATIONS
    may be launched.

Current Tools:
    - open_application
    - focus_application
"""

import ctypes
import os
import subprocess
from pathlib import Path

from .registry import (
    register_tool,
)


# ---------------------------------------------------------------------------
# Approved Applications
# ---------------------------------------------------------------------------

LOCAL_APPDATA = os.environ.get(
    "LOCALAPPDATA",
    ""
)


APPROVED_APPLICATIONS = {

    "vscode": {
        "display_name":
            "Visual Studio Code",

        "executables": [
            "code",
            str(
                Path(
                    LOCAL_APPDATA
                )
                / "Programs"
                / "Microsoft VS Code"
                / "Code.exe"
            ),
        ],

        "window_keywords": [
            "visual studio code",
        ],
    },

    "chrome": {
        "display_name":
            "Google Chrome",

        "executables": [
            "chrome",
            str(
                Path(
                    os.environ.get(
                        "PROGRAMFILES",
                        ""
                    )
                )
                / "Google"
                / "Chrome"
                / "Application"
                / "chrome.exe"
            ),
            str(
                Path(
                    os.environ.get(
                        "PROGRAMFILES(X86)",
                        ""
                    )
                )
                / "Google"
                / "Chrome"
                / "Application"
                / "chrome.exe"
            ),
        ],

        "window_keywords": [
            "google chrome",
        ],
    },

    "notepad": {
        "display_name":
            "Notepad",

        "executables": [
            "notepad.exe",
        ],

        "window_keywords": [
            "notepad",
        ],
    },

    "explorer": {
        "display_name":
            "File Explorer",

        "executables": [
            "explorer.exe",
        ],

        "window_keywords": [
            "file explorer",
        ],
    },

    "powershell": {
        "display_name":
            "PowerShell",

        "executables": [
            "powershell.exe",
        ],

        "window_keywords": [
            "powershell",
        ],
    },
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def normalize_application_name(
    name: str,
):
    aliases = {
        "vs code":
            "vscode",

        "visual studio code":
            "vscode",

        "code":
            "vscode",

        "google chrome":
            "chrome",

        "file explorer":
            "explorer",

        "windows explorer":
            "explorer",
    }

    normalized = (
        name
        .strip()
        .lower()
    )

    return aliases.get(
        normalized,
        normalized,
    )


def get_application(
    name: str,
):
    normalized = (
        normalize_application_name(
            name
        )
    )

    application = (
        APPROVED_APPLICATIONS.get(
            normalized
        )
    )

    if application is None:

        raise PermissionError(
            (
                "Application is not on "
                "E.V.I.E.'s approved list: "
                f"{name}"
            )
        )

    return (
        normalized,
        application,
    )


def find_executable(
    candidates,
):
    for candidate in candidates:

        if not candidate:
            continue

        candidate_path = (
            Path(
                candidate
            )
        )

        if candidate_path.is_absolute():

            if candidate_path.exists():

                return str(
                    candidate_path
                )

        else:

            return candidate

    return None


# ---------------------------------------------------------------------------
# Open Application
# ---------------------------------------------------------------------------

def open_application(
    name: str,
):
    normalized, application = (
        get_application(
            name
        )
    )

    executable = find_executable(
        application[
            "executables"
        ]
    )

    if executable is None:

        raise FileNotFoundError(
            (
                "Could not locate approved "
                f"application: {name}"
            )
        )

    subprocess.Popen(
        [
            executable,
        ],
        shell=False,
    )

    return {
        "application":
            normalized,

        "display_name":
            application[
                "display_name"
            ],

        "launched":
            True,
    }


# ---------------------------------------------------------------------------
# Windows Window Enumeration
# ---------------------------------------------------------------------------

def get_visible_windows():
    user32 = ctypes.windll.user32

    windows = []

    EnumWindowsProc = (
        ctypes.WINFUNCTYPE(
            ctypes.c_bool,
            ctypes.c_void_p,
            ctypes.c_void_p,
        )
    )

    def callback(
        hwnd,
        lparam,
    ):
        if not user32.IsWindowVisible(
            hwnd
        ):
            return True

        length = (
            user32.GetWindowTextLengthW(
                hwnd
            )
        )

        if length <= 0:
            return True

        buffer = ctypes.create_unicode_buffer(
            length + 1
        )

        user32.GetWindowTextW(
            hwnd,
            buffer,
            length + 1,
        )

        title = (
            buffer.value.strip()
        )

        if title:

            windows.append(
                {
                    "hwnd":
                        hwnd,

                    "title":
                        title,
                }
            )

        return True

    user32.EnumWindows(
        EnumWindowsProc(
            callback
        ),
        0,
    )

    return windows


# ---------------------------------------------------------------------------
# Focus Application
# ---------------------------------------------------------------------------

def focus_application(
    name: str,
):
    normalized, application = (
        get_application(
            name
        )
    )

    keywords = [
        keyword.lower()

        for keyword
        in application[
            "window_keywords"
        ]
    ]

    windows = (
        get_visible_windows()
    )

    for window in windows:

        title = (
            window[
                "title"
            ].lower()
        )

        if any(
            keyword in title
            for keyword
            in keywords
        ):

            hwnd = (
                window[
                    "hwnd"
                ]
            )

            user32 = (
                ctypes.windll.user32
            )

            SW_RESTORE = 9

            user32.ShowWindow(
                hwnd,
                SW_RESTORE,
            )

            success = bool(
                user32.SetForegroundWindow(
                    hwnd
                )
            )

            return {
                "application":
                    normalized,

                "window_title":
                    window[
                        "title"
                    ],

                "focused":
                    success,
            }

    return {
        "application":
            normalized,

        "focused":
            False,

        "reason":
            "No matching visible window found.",
    }


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

register_tool(
    name="open_application",
    description=(
        "Launches an approved desktop application."
    ),
    category="applications",
    risk="low",
    function=open_application,
)


register_tool(
    name="focus_application",
    description=(
        "Brings an approved application's "
        "existing window to the foreground."
    ),
    category="applications",
    risk="low",
    function=focus_application,
)


# ---------------------------------------------------------------------------
# Standalone Test
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    print(
        "E.V.I.E. Application Tools"
    )

    print(
        "---------------------------"
    )

    print()

    print(
        "Approved applications:"
    )

    for key, value in (
        APPROVED_APPLICATIONS.items()
    ):

        print(
            (
                f"- {key}: "
                f"{value['display_name']}"
            )
        )