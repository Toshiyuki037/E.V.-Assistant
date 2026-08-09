"""
E.V.I.E. - Screen Capture

Created: August 9, 2026
Last Edited: August 9, 2026
Author: Max Maehara

Purpose:
    Captures temporary screenshots for E.V.I.E.'s visual intelligence.

Capabilities:
    - full virtual desktop capture
    - individual monitor capture
    - active-window capture on Windows
    - safe fallback to desktop capture
    - temporary screenshot files

Most Recent Change:
    Added active-window capture, capture metadata, DPI awareness,
    and integration with temporary screenshot lifecycle management.
"""

import ctypes
import os

from datetime import datetime
from pathlib import Path

import mss
from PIL import Image

from .lifecycle import (
    VISION_CACHE,
    cleanup_stale_visual_artifacts,
)


ROOT = (
    Path(__file__)
    .resolve()
    .parent
    .parent
    .parent
)


def _timestamp() -> str:
    return (
        datetime.now()
        .strftime(
            "%Y%m%d_%H%M%S_%f"
        )
    )


def _enable_windows_dpi_awareness():
    """
    Improves window-coordinate accuracy on high-DPI Windows displays.
    """

    if os.name != "nt":
        return

    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(
            2
        )

    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()

        except Exception:
            pass


def _get_foreground_window_rect():
    """
    Returns the physical foreground-window rectangle on Windows.

    Returns:
        dict | None
    """

    if os.name != "nt":
        return None

    _enable_windows_dpi_awareness()

    user32 = ctypes.windll.user32

    hwnd = user32.GetForegroundWindow()

    if not hwnd:
        return None

    class RECT(
        ctypes.Structure
    ):
        _fields_ = [
            (
                "left",
                ctypes.c_long,
            ),
            (
                "top",
                ctypes.c_long,
            ),
            (
                "right",
                ctypes.c_long,
            ),
            (
                "bottom",
                ctypes.c_long,
            ),
        ]

    rect = RECT()

    if not user32.GetWindowRect(
        hwnd,
        ctypes.byref(
            rect
        ),
    ):
        return None

    width = (
        rect.right
        - rect.left
    )

    height = (
        rect.bottom
        - rect.top
    )

    if (
        width <= 0
        or height <= 0
    ):
        return None

    return {
        "left":
            int(
                rect.left
            ),

        "top":
            int(
                rect.top
            ),

        "width":
            int(
                width
            ),

        "height":
            int(
                height
            ),
    }


def save_mss_capture(
    capture,
    filename: str,
):
    """
    Saves one MSS capture as a temporary PNG.
    """

    path = (
        VISION_CACHE
        / filename
    )

    image = Image.frombytes(
        "RGB",

        (
            capture.width,
            capture.height,
        ),

        capture.rgb,
    )

    image.save(
        path,
        format="PNG",
    )

    return path


def capture_desktop():
    """
    Captures the complete virtual desktop across all monitors.
    """

    cleanup_stale_visual_artifacts(
        max_age_minutes=60
    )

    with mss.MSS() as screen:

        region = (
            screen.monitors[0]
        )

        capture = screen.grab(
            region
        )

    path = save_mss_capture(
        capture,
        (
            "screen_desktop_"
            f"{_timestamp()}.png"
        ),
    )

    return {
        "screenshot_path":
            str(path),

        "source":
            "desktop",

        "fresh":
            True,

        "temporary":
            True,

        "monitor_index":
            None,

        "region":
            dict(region),
    }


def capture_monitor(
    monitor_index: int = 1,
):
    """
    Captures one physical monitor.
    """

    cleanup_stale_visual_artifacts(
        max_age_minutes=60
    )

    with mss.MSS() as screen:

        if (
            monitor_index < 1
            or monitor_index
            >= len(
                screen.monitors
            )
        ):
            raise ValueError(
                (
                    "Invalid monitor index: "
                    f"{monitor_index}"
                )
            )

        region = (
            screen.monitors[
                monitor_index
            ]
        )

        capture = screen.grab(
            region
        )

    path = save_mss_capture(
        capture,
        (
            "screen_monitor"
            f"{monitor_index}_"
            f"{_timestamp()}.png"
        ),
    )

    return {
        "screenshot_path":
            str(path),

        "source":
            "monitor",

        "fresh":
            True,

        "temporary":
            True,

        "monitor_index":
            monitor_index,

        "region":
            dict(region),
    }


def capture_active_window(
    fallback_to_desktop: bool = True,
):
    """
    Captures the foreground window.

    On unsupported systems or invalid foreground-window geometry,
    optionally falls back to a full desktop capture.
    """

    cleanup_stale_visual_artifacts(
        max_age_minutes=60
    )

    region = (
        _get_foreground_window_rect()
    )

    if region is None:

        if fallback_to_desktop:

            result = (
                capture_desktop()
            )

            result[
                "source"
            ] = "desktop_fallback"

            return result

        raise RuntimeError(
            "Active-window capture is unavailable."
        )

    try:

        with mss.MSS() as screen:

            capture = screen.grab(
                region
            )

    except Exception:

        if fallback_to_desktop:

            result = (
                capture_desktop()
            )

            result[
                "source"
            ] = "desktop_fallback"

            return result

        raise

    path = save_mss_capture(
        capture,
        (
            "screen_active_window_"
            f"{_timestamp()}.png"
        ),
    )

    return {
        "screenshot_path":
            str(path),

        "source":
            "active_window",

        "fresh":
            True,

        "temporary":
            True,

        "monitor_index":
            None,

        "region":
            region,
    }


if __name__ == "__main__":

    from .lifecycle import (
        delete_visual_artifact,
    )

    print(
        "E.V.I.E. Screen Capture"
    )

    print(
        "------------------------"
    )

    captures = []

    try:

        desktop = (
            capture_desktop()
        )

        captures.append(
            desktop
        )

        print(
            "Desktop screenshot:"
        )

        print(
            desktop[
                "screenshot_path"
            ]
        )

        active = (
            capture_active_window()
        )

        captures.append(
            active
        )

        print()

        print(
            "Active-window screenshot:"
        )

        print(
            active[
                "screenshot_path"
            ]
        )

        print(
            "Source:",
            active[
                "source"
            ],
        )

        monitor = (
            capture_monitor(
                1
            )
        )

        captures.append(
            monitor
        )

        print()

        print(
            "Monitor 1 screenshot:"
        )

        print(
            monitor[
                "screenshot_path"
            ]
        )

    finally:

        for item in captures:

            delete_visual_artifact(
                item.get(
                    "screenshot_path"
                )
            )

        print()

        print(
            "Temporary test screenshots deleted."
        )
