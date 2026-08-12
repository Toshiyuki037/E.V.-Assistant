"""
E.V.I.E. - Native Windows Clipboard

Phase 13D

Uses Win32 clipboard APIs for Unicode text.
No UI automation is used.
"""

from __future__ import annotations

import ctypes
from ctypes import wintypes
import sys


IS_WINDOWS = (
    sys.platform == "win32"
)


class ClipboardUnavailable(RuntimeError):
    pass


if IS_WINDOWS:
    user32 = ctypes.WinDLL(
        "user32",
        use_last_error=True,
    )

    kernel32 = ctypes.WinDLL(
        "kernel32",
        use_last_error=True,
    )

    CF_UNICODETEXT = 13
    GMEM_MOVEABLE = 0x0002

    user32.OpenClipboard.argtypes = [
        wintypes.HWND,
    ]
    user32.OpenClipboard.restype = wintypes.BOOL

    user32.CloseClipboard.argtypes = []
    user32.CloseClipboard.restype = wintypes.BOOL

    user32.EmptyClipboard.argtypes = []
    user32.EmptyClipboard.restype = wintypes.BOOL

    user32.GetClipboardData.argtypes = [
        wintypes.UINT,
    ]
    user32.GetClipboardData.restype = wintypes.HANDLE

    user32.SetClipboardData.argtypes = [
        wintypes.UINT,
        wintypes.HANDLE,
    ]
    user32.SetClipboardData.restype = wintypes.HANDLE

    user32.IsClipboardFormatAvailable.argtypes = [
        wintypes.UINT,
    ]
    user32.IsClipboardFormatAvailable.restype = wintypes.BOOL

    kernel32.GlobalAlloc.argtypes = [
        wintypes.UINT,
        ctypes.c_size_t,
    ]
    kernel32.GlobalAlloc.restype = wintypes.HGLOBAL

    kernel32.GlobalLock.argtypes = [
        wintypes.HGLOBAL,
    ]
    kernel32.GlobalLock.restype = wintypes.LPVOID

    kernel32.GlobalUnlock.argtypes = [
        wintypes.HGLOBAL,
    ]
    kernel32.GlobalUnlock.restype = wintypes.BOOL

    kernel32.GlobalFree.argtypes = [
        wintypes.HGLOBAL,
    ]
    kernel32.GlobalFree.restype = wintypes.HGLOBAL


def _require_windows():
    if not IS_WINDOWS:
        raise ClipboardUnavailable(
            "Native clipboard control is only available on Windows."
        )


def _open_clipboard():
    _require_windows()

    if not user32.OpenClipboard(
        None
    ):
        raise RuntimeError(
            "Could not open Windows clipboard."
        )


def read_clipboard_text() -> str:
    _open_clipboard()

    try:
        if not user32.IsClipboardFormatAvailable(
            CF_UNICODETEXT
        ):
            return ""

        handle = user32.GetClipboardData(
            CF_UNICODETEXT
        )

        if not handle:
            return ""

        pointer = kernel32.GlobalLock(
            handle
        )

        if not pointer:
            return ""

        try:
            return ctypes.wstring_at(
                pointer
            )

        finally:
            kernel32.GlobalUnlock(
                handle
            )

    finally:
        user32.CloseClipboard()


def write_clipboard_text(
    text: str,
) -> str:
    _open_clipboard()

    value = str(
        text
        or ""
    )

    data = (
        value
        + "\0"
    ).encode(
        "utf-16-le"
    )

    handle = None

    try:
        if not user32.EmptyClipboard():
            raise RuntimeError(
                "Could not clear Windows clipboard."
            )

        handle = kernel32.GlobalAlloc(
            GMEM_MOVEABLE,
            len(data),
        )

        if not handle:
            raise MemoryError(
                "GlobalAlloc failed for clipboard data."
            )

        pointer = kernel32.GlobalLock(
            handle
        )

        if not pointer:
            raise MemoryError(
                "GlobalLock failed for clipboard data."
            )

        try:
            ctypes.memmove(
                pointer,
                data,
                len(data),
            )
        finally:
            kernel32.GlobalUnlock(
                handle
            )

        result = user32.SetClipboardData(
            CF_UNICODETEXT,
            handle,
        )

        if not result:
            raise RuntimeError(
                "SetClipboardData failed."
            )

        # Clipboard now owns the handle.
        handle = None

    finally:
        user32.CloseClipboard()

        if handle:
            kernel32.GlobalFree(
                handle
            )

    return value


def clear_clipboard() -> bool:
    _open_clipboard()

    try:
        if not user32.EmptyClipboard():
            raise RuntimeError(
                "Could not clear Windows clipboard."
            )

        return True

    finally:
        user32.CloseClipboard()
