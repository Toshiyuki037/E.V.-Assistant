"""
E.V.I.E. - Windows Accessibility Backend

Phase 13G

Uses Microsoft UI Automation through pywinauto's UIA backend.

Control hierarchy:
    Native API
        ↓
    Application integration
        ↓
    Accessibility / UI Automation  <-- this module
        ↓
    Browser DOM
        ↓
    Vision fallback

No coordinate clicking is used here.
"""

from __future__ import annotations

import sys

from .accessibility_models import UIElementInfo


IS_WINDOWS = sys.platform == "win32"


class AccessibilityBackendUnavailable(RuntimeError):
    pass


def _load_pywinauto():
    if not IS_WINDOWS:
        raise AccessibilityBackendUnavailable(
            "Windows UI Automation is only available on Windows."
        )

    try:
        from pywinauto import Desktop
    except ImportError as error:
        raise AccessibilityBackendUnavailable(
            "Phase 13G requires pywinauto. "
            "Install it with: python -m pip install pywinauto"
        ) from error

    return Desktop


def _safe(callable_, default):
    try:
        value = callable_()
        return default if value is None else value
    except Exception:
        return default


def _rectangle(wrapper):
    rect = _safe(
        lambda: wrapper.rectangle(),
        None,
    )

    if rect is None:
        return 0, 0, 0, 0

    left = int(
        getattr(rect, "left", 0)
    )
    top = int(
        getattr(rect, "top", 0)
    )
    right = int(
        getattr(rect, "right", left)
    )
    bottom = int(
        getattr(rect, "bottom", top)
    )

    return (
        left,
        top,
        max(0, right - left),
        max(0, bottom - top),
    )


def _available_patterns(wrapper) -> list[str]:
    patterns = []

    element_info = getattr(
        wrapper,
        "element_info",
        None,
    )

    if element_info is None:
        return patterns

    names = [
        "invoke",
        "value",
        "toggle",
        "selection",
        "selection_item",
        "expand_collapse",
        "scroll",
        "range_value",
    ]

    for name in names:
        attr_name = (
            name
            + "_pattern"
        )

        pattern = _safe(
            lambda attr_name=attr_name: getattr(
                element_info,
                attr_name,
            ),
            None,
        )

        if pattern is not None:
            patterns.append(name)

    return patterns


def _value_text(wrapper) -> str:
    candidates = [
        lambda: wrapper.get_value(),
        lambda: wrapper.window_text(),
        lambda: wrapper.texts()[0],
    ]

    for candidate in candidates:
        try:
            value = candidate()

            if value is not None:
                return str(value)
        except Exception:
            continue

    return ""


def _toggle_state(wrapper) -> str:
    value = _safe(
        lambda: wrapper.get_toggle_state(),
        None,
    )

    if value is None:
        return ""

    mapping = {
        0: "off",
        1: "on",
        2: "indeterminate",
    }

    return mapping.get(
        int(value),
        str(value),
    )


def _selection_state(wrapper) -> str:
    value = _safe(
        lambda: wrapper.is_selected(),
        None,
    )

    if value is None:
        return ""

    return (
        "selected"
        if bool(value)
        else "not_selected"
    )


def wrapper_to_info(
    wrapper,
    *,
    depth: int = 0,
    path: list[int] | None = None,
) -> UIElementInfo:
    element = getattr(
        wrapper,
        "element_info",
        None,
    )

    x, y, width, height = _rectangle(
        wrapper
    )

    return UIElementInfo(
        name=str(
            _safe(
                lambda: wrapper.window_text(),
                "",
            )
            or ""
        ),
        control_type=str(
            getattr(
                element,
                "control_type",
                "",
            )
            or ""
        ),
        automation_id=str(
            getattr(
                element,
                "automation_id",
                "",
            )
            or ""
        ),
        class_name=str(
            getattr(
                element,
                "class_name",
                "",
            )
            or ""
        ),
        framework_id=str(
            getattr(
                element,
                "framework_id",
                "",
            )
            or ""
        ),
        process_id=int(
            getattr(
                element,
                "process_id",
                0,
            )
            or 0
        ),
        handle=int(
            getattr(
                element,
                "handle",
                0,
            )
            or 0
        ),
        x=x,
        y=y,
        width=width,
        height=height,
        enabled=bool(
            _safe(
                lambda: wrapper.is_enabled(),
                False,
            )
        ),
        visible=bool(
            _safe(
                lambda: wrapper.is_visible(),
                False,
            )
        ),
        focused=bool(
            _safe(
                lambda: wrapper.has_keyboard_focus(),
                False,
            )
        ),
        value=_value_text(
            wrapper
        ),
        toggle_state=_toggle_state(
            wrapper
        ),
        selection_state=_selection_state(
            wrapper
        ),
        patterns=_available_patterns(
            wrapper
        ),
        depth=int(depth),
        path=list(
            path
            or []
        ),
    )


def desktop():
    Desktop = _load_pywinauto()

    return Desktop(
        backend="uia"
    )
