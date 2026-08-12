
"""
E.V.I.E. - Computer Control Context

Phase 13J
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .control_models import ComputerControlRequest


@dataclass
class ControlContext:
    request: ComputerControlRequest
    foreground_window: dict | None = None
    browser_session: Any = None
    screen_capture: dict | None = None

    def to_dict(self):
        return {
            "request": self.request.to_dict(),
            "foreground_window": self.foreground_window,
            "has_browser_session": (
                self.browser_session
                is not None
            ),
            "screen_capture": self.screen_capture,
        }
