"""
E.V.I.E. - Local Media Device Models

Phase 13F
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class AudioDeviceInfo:
    index: int
    name: str
    host_api: str
    max_input_channels: int
    max_output_channels: int
    default_sample_rate: float
    is_default_input: bool = False
    is_default_output: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "name": self.name,
            "host_api": self.host_api,
            "max_input_channels": self.max_input_channels,
            "max_output_channels": self.max_output_channels,
            "default_sample_rate": self.default_sample_rate,
            "is_default_input": self.is_default_input,
            "is_default_output": self.is_default_output,
        }


@dataclass
class CameraDeviceInfo:
    index: int
    available: bool
    width: int = 0
    height: int = 0
    fps: float = 0.0
    backend: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "available": self.available,
            "width": self.width,
            "height": self.height,
            "fps": self.fps,
            "backend": self.backend,
        }


@dataclass
class CaptureResult:
    kind: str
    path: str
    success: bool
    detail: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "path": self.path,
            "success": self.success,
            "detail": self.detail,
        }
