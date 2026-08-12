from __future__ import annotations
from dataclasses import dataclass
from typing import Any

@dataclass
class ScreenCaptureInfo:
    path: str
    width: int
    height: int
    monitor_index: int | None = None
    window_handle: int | None = None
    success: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "width": self.width,
            "height": self.height,
            "monitor_index": self.monitor_index,
            "window_handle": self.window_handle,
            "success": self.success,
        }

@dataclass
class VisualTarget:
    label: str
    x: int
    y: int
    width: int
    height: int
    confidence: float = 0.0
    source: str = "vision"

    @property
    def center(self) -> tuple[int, int]:
        return (
            int(self.x + self.width / 2),
            int(self.y + self.height / 2),
        )

    def to_dict(self) -> dict[str, Any]:
        cx, cy = self.center
        return {
            "label": self.label,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "center_x": cx,
            "center_y": cy,
            "confidence": self.confidence,
            "source": self.source,
        }
