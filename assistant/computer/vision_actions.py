from __future__ import annotations
import ctypes
from ctypes import wintypes
import sys

from .vision_models import VisualTarget
from .vision_fallback import validate_visual_target

class VisionActionUnavailable(RuntimeError):
    pass

def _require_windows():
    if sys.platform != "win32":
        raise VisionActionUnavailable(
            "Vision mouse actions are only available on Windows."
        )

def move_pointer_to_target(
    target: VisualTarget,
    *,
    screen_width: int,
    screen_height: int,
    min_confidence: float = 0.70,
) -> dict:
    _require_windows()

    validate_visual_target(
        target,
        screen_width=screen_width,
        screen_height=screen_height,
        min_confidence=min_confidence,
    )

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    user32.SetCursorPos.argtypes = [ctypes.c_int, ctypes.c_int]
    user32.SetCursorPos.restype = wintypes.BOOL

    x, y = target.center

    if not user32.SetCursorPos(x, y):
        raise RuntimeError("SetCursorPos failed.")

    return {
        "action": "move_pointer",
        "target": target.to_dict(),
        "success": True,
        "verified": True,
    }

def click_visual_target(
    target: VisualTarget,
    *,
    screen_width: int,
    screen_height: int,
    approved: bool = False,
    min_confidence: float = 0.80,
) -> dict:
    _require_windows()

    if not approved:
        raise PermissionError(
            "Vision-based clicking requires explicit approval."
        )

    validate_visual_target(
        target,
        screen_width=screen_width,
        screen_height=screen_height,
        min_confidence=min_confidence,
    )

    user32 = ctypes.WinDLL("user32", use_last_error=True)

    INPUT_MOUSE = 0
    MOUSEEVENTF_LEFTDOWN = 0x0002
    MOUSEEVENTF_LEFTUP = 0x0004

    class MOUSEINPUT(ctypes.Structure):
        _fields_ = [
            ("dx", wintypes.LONG),
            ("dy", wintypes.LONG),
            ("mouseData", wintypes.DWORD),
            ("dwFlags", wintypes.DWORD),
            ("time", wintypes.DWORD),
            ("dwExtraInfo", ctypes.c_void_p),
        ]

    class INPUT_UNION(ctypes.Union):
        _fields_ = [("mi", MOUSEINPUT)]

    class INPUT(ctypes.Structure):
        _anonymous_ = ("u",)
        _fields_ = [
            ("type", wintypes.DWORD),
            ("u", INPUT_UNION),
        ]

    user32.SetCursorPos.argtypes = [ctypes.c_int, ctypes.c_int]
    user32.SetCursorPos.restype = wintypes.BOOL
    user32.SendInput.argtypes = [
        wintypes.UINT,
        ctypes.POINTER(INPUT),
        ctypes.c_int,
    ]
    user32.SendInput.restype = wintypes.UINT

    x, y = target.center

    if not user32.SetCursorPos(x, y):
        raise RuntimeError("SetCursorPos failed.")

    inputs = (INPUT * 2)(
        INPUT(
            type=INPUT_MOUSE,
            mi=MOUSEINPUT(
                0, 0, 0, MOUSEEVENTF_LEFTDOWN, 0, None
            ),
        ),
        INPUT(
            type=INPUT_MOUSE,
            mi=MOUSEINPUT(
                0, 0, 0, MOUSEEVENTF_LEFTUP, 0, None
            ),
        ),
    )

    sent = user32.SendInput(
        2,
        inputs,
        ctypes.sizeof(INPUT),
    )

    if sent != 2:
        raise RuntimeError(
            f"SendInput sent {sent}/2 mouse events."
        )

    return {
        "action": "vision_click",
        "target": target.to_dict(),
        "success": True,
        "verified": False,
        "detail": (
            "Vision click executed. Higher-level control flow must "
            "verify the resulting UI state."
        ),
    }
