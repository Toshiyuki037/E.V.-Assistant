
"""
E.V.I.E. - Unified Computer Control Router

Phase 13J

Routes actions through the strongest available structured method.

Native
  ↓
Application integration
  ↓
Accessibility / UIA
  ↓
Browser DOM
  ↓
Vision fallback
"""

from __future__ import annotations

from .control_models import (
    AttemptStatus,
    ControlAttempt,
    ControlMethod,
    ComputerControlRequest,
)
from .control_policy import (
    ordered_methods,
)


_NATIVE_ACTIONS = {
    "monitor.list",
    "window.focus",
    "window.move",
    "window.minimize",
    "window.maximize",
    "window.close",
    "window.place",
    "application.launch",
    "filesystem.create_directory",
    "filesystem.write",
    "filesystem.copy",
    "filesystem.move",
    "filesystem.rename",
    "filesystem.delete",
    "filesystem.exists",
    "filesystem.inspect",
    "clipboard.read",
    "clipboard.write",
    "notification.send",
    "settings.open",
    "process.terminate",
    "system.lock_workstation",
}

_ACCESSIBILITY_ACTIONS = {
    "accessibility.focus",
    "accessibility.invoke",
    "accessibility.set_value",
    "accessibility.toggle",
    "accessibility.select",
}

_DOM_ACTIONS = {
    "browser.navigate",
    "browser.dom.click",
    "browser.dom.fill",
    "browser.dom.check",
    "browser.dom.select",
    "browser.dom.press",
}

_VISION_ACTIONS = {
    "vision.pointer_move",
    "vision.click",
}


def method_supports_request(
    method: ControlMethod,
    request: ComputerControlRequest,
) -> bool:
    action = request.action

    if method == ControlMethod.NATIVE:
        return action in _NATIVE_ACTIONS

    if method == ControlMethod.INTEGRATION:
        # Phase 13J preserves this layer even though app-specific
        # computer integrations are added progressively.
        return False

    if method == ControlMethod.ACCESSIBILITY:
        return action in _ACCESSIBILITY_ACTIONS

    if method == ControlMethod.DOM:
        return action in _DOM_ACTIONS

    if method == ControlMethod.VISION:
        return action in _VISION_ACTIONS

    return False


def route_methods(
    request: ComputerControlRequest,
) -> list[ControlMethod]:
    return [
        method
        for method in ordered_methods(
            request
        )
        if method_supports_request(
            method,
            request,
        )
    ]


def unsupported_attempt(
    method: ControlMethod,
    action: str,
) -> ControlAttempt:
    return ControlAttempt(
        method=method,
        status=AttemptStatus.UNSUPPORTED,
        detail=(
            f"{method.value} does not support action {action!r}."
        ),
        confidence=1.0,
    )
