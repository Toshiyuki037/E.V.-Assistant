"""
E.V.I.E. - Workspace Adapter Base

Phase 12B
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from assistant.workspace.models import EvidenceItem


@dataclass
class AdapterContext:
    project: str = ""
    repository: str = ""
    workspace_path: str = ""
    arguments: dict[str, Any] = field(default_factory=dict)


class WorkspaceAdapter(Protocol):
    name: str

    def search(
        self,
        query: str,
        context: AdapterContext,
    ) -> list[EvidenceItem]:
        ...
