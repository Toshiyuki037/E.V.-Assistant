
"""
E.V.I.E. - Unified Computer Control Models

Phase 13J
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ControlMethod(str, Enum):
    NATIVE = "native"
    INTEGRATION = "integration"
    ACCESSIBILITY = "accessibility"
    DOM = "dom"
    VISION = "vision"


class AttemptStatus(str, Enum):
    SUCCESS = "success"
    UNSUPPORTED = "unsupported"
    NOT_FOUND = "not_found"
    AMBIGUOUS = "ambiguous"
    BLOCKED = "blocked"
    FAILED = "failed"


@dataclass
class ControlAttempt:
    method: ControlMethod
    status: AttemptStatus
    detail: str = ""
    confidence: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "method": self.method.value,
            "status": self.status.value,
            "detail": self.detail,
            "confidence": self.confidence,
        }


@dataclass
class ComputerControlRequest:
    action: str
    target: str = ""
    arguments: dict[str, Any] = field(default_factory=dict)
    preferred_method: str = ""
    allow_vision: bool = True
    approved: bool = False
    device_id: str = "local-windows"

    def to_dict(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "target": self.target,
            "arguments": dict(self.arguments),
            "preferred_method": self.preferred_method,
            "allow_vision": self.allow_vision,
            "approved": self.approved,
            "device_id": self.device_id,
        }


@dataclass
class ComputerControlResult:
    action: str
    target: str
    success: bool
    method: str = ""
    verified: bool = False
    confidence: float = 0.0
    result: Any = None
    attempts: list[ControlAttempt] = field(default_factory=list)
    detail: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "target": self.target,
            "success": self.success,
            "method": self.method,
            "verified": self.verified,
            "confidence": self.confidence,
            "result": self.result,
            "attempts": [
                attempt.to_dict()
                for attempt in self.attempts
            ],
            "detail": self.detail,
        }
