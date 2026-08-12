
"""
E.V.I.E. - Phase 13L Computer Integration Models

Final Phase 13 integration layer.

This module intentionally keeps natural-language planning separate from the
low-level control backends built in Phase 13A-13K.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ComputerToolPlan:
    handled: bool
    action: str = ""
    target: str = ""
    arguments: dict[str, Any] = field(default_factory=dict)
    approved: bool = False
    allow_vision: bool = True
    confidence: int = 0
    rationale: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "handled": self.handled,
            "action": self.action,
            "target": self.target,
            "arguments": dict(self.arguments),
            "approved": self.approved,
            "allow_vision": self.allow_vision,
            "confidence": self.confidence,
            "rationale": self.rationale,
        }
