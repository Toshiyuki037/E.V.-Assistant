from __future__ import annotations

import ctypes
from ctypes import wintypes
import os
from pathlib import Path
import time

if os.name != "nt":
    raise RuntimeError("desktop_layout is Windows-only.")

user32 = ctypes.WinDLL("user32", use_last_error=True)
SW_RESTORE = 9
SW_MAXIMIZE = 3
WM_CLOSE = 0x0010


class RECT(ctypes.Structure):
    _fields_ = [
        ("left", wintypes.LONG),
        ("top", wintypes.LONG),
        ("right", wintypes.LONG),
        ("bottom", wintypes.LONG),
    ]


class MONITORINFOEXW(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("rcMonitor", RECT),
        ("rcWork", RECT),
        ("dwFlags", wintypes.DWORD),
        ("szDevice", wintypes.WCHAR * 32),
    ]


def _enum_windows() -> list[dict]:
    windows = []
    callback_type = ctypes.WINFUNCTYPE(
        wintypes.BOOL,
        wintypes.HWND,
        wintypes.LPARAM,
    )

    def callback(hwnd, lparam):
        if not user32.IsWindowVisible(hwnd):
            return True
        length = user32.GetWindowTextLengthW(hwnd)
        if length <= 0:
            return True
        buffer = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buffer, length + 1)
        title = buffer.value.strip()
        if not title:
            return True
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        rect = RECT()
        if not user32.GetWindowRect(hwnd, ctypes.byref(rect)):
            return True
        windows.append({
            "handle": int(hwnd),
            "title": title,
            "process_id": int(pid.value),
            "x": int(rect.left),
            "y": int(rect.top),
            "width": int(rect.right - rect.left),
            "height": int(rect.bottom - rect.top),
        })
        return True

    user32.EnumWindows(callback_type(callback), 0)
    return windows


def list_physical_monitors() -> list[dict]:
    monitors = []
    monitor_enum_proc = ctypes.WINFUNCTYPE(
        wintypes.BOOL,
        wintypes.HMONITOR,
        wintypes.HDC,
        ctypes.POINTER(RECT),
        wintypes.LPARAM,
    )

    def callback(hmonitor, hdc, lprect, lparam):
        info = MONITORINFOEXW()
        info.cbSize = ctypes.sizeof(MONITORINFOEXW)
        if not user32.GetMonitorInfoW(hmonitor, ctypes.byref(info)):
            return True
        monitors.append({
            "monitor_index": len(monitors) + 1,
            "handle": int(hmonitor),
            "device": str(info.szDevice),
            "primary": bool(info.dwFlags & 1),
            "x": int(info.rcMonitor.left),
            "y": int(info.rcMonitor.top),
            "width": int(info.rcMonitor.right - info.rcMonitor.left),
            "height": int(info.rcMonitor.bottom - info.rcMonitor.top),
            "work_x": int(info.rcWork.left),
            "work_y": int(info.rcWork.top),
            "work_width": int(info.rcWork.right - info.rcWork.left),
            "work_height": int(info.rcWork.bottom - info.rcWork.top),
        })
        return True

    user32.EnumDisplayMonitors(0, None, monitor_enum_proc(callback), 0)
    return monitors


def get_monitor(monitor_index: int) -> dict:
    monitors = list_physical_monitors()
    index = int(monitor_index)
    if index < 1 or index > len(monitors):
        raise IndexError(
            f"Monitor {index} does not exist. Detected {len(monitors)} monitor(s)."
        )
    return monitors[index - 1]


def resolve_window(target: str = "", *, handle: int | None = None) -> dict:
    if handle is not None:
        wanted = int(handle)
        for window in _enum_windows():
            if window["handle"] == wanted:
                return window
        raise LookupError(f"No visible window matched handle {wanted}.")

    text = str(target or "").strip().lower()
    if not text:
        raise ValueError("Window target cannot be empty.")
    matches = [w for w in _enum_windows() if text in w["title"].lower()]
    if not matches:
        raise LookupError(f"No visible window matched: {target}")
    exact = [w for w in matches if w["title"].lower() == text]
    if len(exact) == 1:
        return exact[0]
    matches.sort(key=lambda w: w["width"] * w["height"], reverse=True)
    return matches[0]


def close_window(target: str = "", *, handle: int | None = None) -> dict:
    window = resolve_window(target, handle=handle)
    hwnd = wintypes.HWND(window["handle"])
    if not user32.PostMessageW(hwnd, WM_CLOSE, 0, 0):
        raise RuntimeError("WM_CLOSE could not be posted.")
    deadline = time.time() + 5.0
    while time.time() < deadline:
        if not user32.IsWindow(hwnd):
            return {
                "action": "window.close",
                "success": True,
                "verified": True,
                "closed_handle": window["handle"],
                "title": window["title"],
            }
        time.sleep(0.1)
    return {
        "action": "window.close",
        "success": True,
        "verified": False,
        "closed_handle": window["handle"],
        "title": window["title"],
        "detail": "WM_CLOSE was sent, but the window still exists; a save/confirmation dialog may be open.",
    }


def place_window_on_monitor(
    target: str = "",
    *,
    monitor_index: int,
    handle: int | None = None,
    maximized: bool = True,
    use_work_area: bool = True,
) -> dict:
    window = resolve_window(target, handle=handle)
    monitor = get_monitor(monitor_index)
    hwnd = wintypes.HWND(window["handle"])
    user32.ShowWindow(hwnd, SW_RESTORE)
    if use_work_area:
        x = monitor["work_x"]
        y = monitor["work_y"]
        width = monitor["work_width"]
        height = monitor["work_height"]
    else:
        x = monitor["x"]
        y = monitor["y"]
        width = monitor["width"]
        height = monitor["height"]
    if not user32.MoveWindow(hwnd, x, y, width, height, True):
        raise RuntimeError("MoveWindow failed.")
    if maximized:
        user32.ShowWindow(hwnd, SW_MAXIMIZE)
    time.sleep(0.15)
    updated = resolve_window(handle=window["handle"])
    return {
        "action": "window.place",
        "success": True,
        "verified": True,
        "monitor": monitor,
        "window": updated,
        "maximized": bool(maximized),
    }


KNOWN_FOLDER_ALIASES = {
    "desktop": Path.home() / "Desktop",
    "documents": Path.home() / "Documents",
    "downloads": Path.home() / "Downloads",
    "pictures": Path.home() / "Pictures",
    "music": Path.home() / "Music",
    "videos": Path.home() / "Videos",
    "home": Path.home(),
}


def resolve_user_path(value: str) -> str:
    raw = os.path.expandvars(os.path.expanduser(str(value or "").strip()))
    if not raw:
        raise ValueError("Path cannot be empty.")
    normalized = raw.replace("/", "\\")
    first, _, rest = normalized.partition("\\")
    alias = first.strip().lower()
    if alias in KNOWN_FOLDER_ALIASES:
        path = KNOWN_FOLDER_ALIASES[alias]
        if rest:
            path = path / rest
        return str(path.resolve(strict=False))
    return str(Path(raw).resolve(strict=False))
