"""
E.V.I.E. - Notification Models

Phase 13E
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class NotificationResult:
    title: str
    message: str
    success: bool
    backend: str
    detail: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "message": self.message,
            "success": self.success,
            "backend": self.backend,
            "detail": self.detail,
        }
