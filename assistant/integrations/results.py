"""
E.V.I.E. - Integration Results

Standard result structures returned by Phase 9 integrations.
"""

from __future__ import annotations

from dataclasses import (
    dataclass,
    field,
)

from typing import Any


@dataclass
class IntegrationResult:
    success: bool

    provider: str

    capability: str

    account_id: str = ""

    data: Any = None

    error: str = ""

    metadata: dict[str, Any] = field(
        default_factory=dict
    )