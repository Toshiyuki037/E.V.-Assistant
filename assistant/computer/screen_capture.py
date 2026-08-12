from __future__ import annotations
from pathlib import Path
import sys

from .vision_models import ScreenCaptureInfo

try:
    import mss
except ImportError:
    mss = None

try:
    from PIL import Image
except ImportError:
    Image = None

class ScreenCaptureUnavailable(RuntimeError):
    pass

def _require_backend():
    if mss is None or Image is None:
        raise ScreenCaptureUnavailable(
            "Phase 13I requires mss and Pillow. "
            "Install with: python -m pip install mss pillow"
        )

def capture_monitor(path: str, *, monitor_index: int = 1) -> ScreenCaptureInfo:
    _require_backend()
    target = Path(path).resolve(strict=False)
    target.parent.mkdir(parents=True, exist_ok=True)

    with mss.mss() as sct:
        monitors = sct.monitors
        index = int(monitor_index)
        if index <= 0 or index >= len(monitors):
            raise IndexError(f"Monitor index out of range: {index}")
        mon = monitors[index]
        shot = sct.grab(mon)
        image = Image.frombytes("RGB", shot.size, shot.rgb)
        image.save(target)
        return ScreenCaptureInfo(
            path=str(target),
            width=int(shot.width),
            height=int(shot.height),
            monitor_index=index,
            success=target.exists(),
        )

def capture_virtual_desktop(path: str) -> ScreenCaptureInfo:
    _require_backend()
    target = Path(path).resolve(strict=False)
    target.parent.mkdir(parents=True, exist_ok=True)

    with mss.mss() as sct:
        mon = sct.monitors[0]
        shot = sct.grab(mon)
        image = Image.frombytes("RGB", shot.size, shot.rgb)
        image.save(target)
        return ScreenCaptureInfo(
            path=str(target),
            width=int(shot.width),
            height=int(shot.height),
            monitor_index=0,
            success=target.exists(),
        )

def capture_window(path: str, handle: int) -> ScreenCaptureInfo:
    if sys.platform != "win32":
        raise ScreenCaptureUnavailable(
            "Window capture is only available on Windows."
        )

    from .windows_backend import get_window_info

    info = get_window_info(int(handle))
    _require_backend()

    target = Path(path).resolve(strict=False)
    target.parent.mkdir(parents=True, exist_ok=True)

    region = {
        "left": int(info.x),
        "top": int(info.y),
        "width": int(info.width),
        "height": int(info.height),
    }

    if region["width"] <= 0 or region["height"] <= 0:
        raise ValueError("Window bounds are not capturable.")

    with mss.mss() as sct:
        shot = sct.grab(region)
        image = Image.frombytes("RGB", shot.size, shot.rgb)
        image.save(target)

    return ScreenCaptureInfo(
        path=str(target),
        width=region["width"],
        height=region["height"],
        window_handle=int(handle),
        success=target.exists(),
    )
