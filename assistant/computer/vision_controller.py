from __future__ import annotations
from .screen_capture import (
    capture_monitor,
    capture_virtual_desktop,
    capture_window,
)
from .vision_actions import (
    click_visual_target,
    move_pointer_to_target,
)
from .vision_fallback import (
    choose_visual_target,
    normalize_visual_target,
)

def capture_local_monitor(path: str, *, monitor_index: int = 1):
    return capture_monitor(path, monitor_index=monitor_index).to_dict()

def capture_local_virtual_desktop(path: str):
    return capture_virtual_desktop(path).to_dict()

def capture_local_window_image(path: str, handle: int):
    return capture_window(path, handle).to_dict()

def choose_local_visual_target(candidates: list[dict], *, min_confidence: float = 0.70):
    normalized = [normalize_visual_target(item) for item in candidates]
    return choose_visual_target(
        normalized,
        min_confidence=min_confidence,
    ).to_dict()

def move_local_pointer_to_visual_target(
    payload: dict,
    *,
    screen_width: int,
    screen_height: int,
    min_confidence: float = 0.70,
):
    target = normalize_visual_target(payload)
    return move_pointer_to_target(
        target,
        screen_width=screen_width,
        screen_height=screen_height,
        min_confidence=min_confidence,
    )

def click_local_visual_target(
    payload: dict,
    *,
    screen_width: int,
    screen_height: int,
    approved: bool = False,
    min_confidence: float = 0.80,
):
    target = normalize_visual_target(payload)
    return click_visual_target(
        target,
        screen_width=screen_width,
        screen_height=screen_height,
        approved=approved,
        min_confidence=min_confidence,
    )
