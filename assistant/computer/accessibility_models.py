"""
E.V.I.E. - Accessibility / UI Automation Models

Phase 13G
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class UIElementInfo:
    name: str
    control_type: str
    automation_id: str = ""
    class_name: str = ""
    framework_id: str = ""
    process_id: int = 0
    handle: int = 0
    x: int = 0
    y: int = 0
    width: int = 0
    height: int = 0
    enabled: bool = False
    visible: bool = False
    focused: bool = False
    value: str = ""
    toggle_state: str = ""
    selection_state: str = ""
    patterns: list[str] = field(default_factory=list)
    depth: int = 0
    path: list[int] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "control_type": self.control_type,
            "automation_id": self.automation_id,
            "class_name": self.class_name,
            "framework_id": self.framework_id,
            "process_id": self.process_id,
            "handle": self.handle,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "enabled": self.enabled,
            "visible": self.visible,
            "focused": self.focused,
            "value": self.value,
            "toggle_state": self.toggle_state,
            "selection_state": self.selection_state,
            "patterns": list(self.patterns),
            "depth": self.depth,
            "path": list(self.path),
        }


@dataclass
class UIActionResult:
    action: str
    target: dict[str, Any]
    success: bool
    verified: bool = False
    detail: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "target": dict(self.target),
            "success": self.success,
            "verified": self.verified,
            "detail": self.detail,
        }
