"""
E.V.I.E. - Coding Repair Models

Phase 12K
"""

from __future__ import annotations

from dataclasses import (
    dataclass,
    field,
)

from typing import Any


@dataclass
class RepairEdit:
    path: str
    content: str
    reason: str = ""


@dataclass
class RepairPlan:
    action: str
    diagnosis: str = ""
    edits: list[RepairEdit] = field(
        default_factory=list
    )
    validation_commands: list[list[str]] = field(
        default_factory=list
    )
    confidence: int = 0
    rationale: str = ""
    metadata: dict[str, Any] = field(
        default_factory=dict
    )
