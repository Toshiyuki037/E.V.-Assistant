"""
E.V.I.E. - Self-Engineering Request Models

Phase 12N
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class CodingRequest:
    handled: bool
    action: str = ""
    goal: str = ""
    confidence: int = 0
    summary: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
