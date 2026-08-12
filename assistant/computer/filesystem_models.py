"""
E.V.I.E. - Filesystem Models

Phase 13D
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class PathRisk(str, Enum):
    NORMAL = "normal"
    SENSITIVE = "sensitive"
    PROTECTED = "protected"


@dataclass
class PathInfo:
    path: str
    exists: bool
    is_file: bool
    is_directory: bool
    size: int = 0
    modified_at: float = 0.0
    risk: PathRisk = PathRisk.NORMAL

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "exists": self.exists,
            "is_file": self.is_file,
            "is_directory": self.is_directory,
            "size": self.size,
            "modified_at": self.modified_at,
            "risk": self.risk.value,
        }


@dataclass
class FilesystemActionResult:
    action: str
    source: str = ""
    destination: str = ""
    success: bool = False
    verified: bool = False
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "source": self.source,
            "destination": self.destination,
            "success": self.success,
            "verified": self.verified,
            "message": self.message,
        }
