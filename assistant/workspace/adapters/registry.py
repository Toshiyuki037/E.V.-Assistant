"""
E.V.I.E. - Workspace Adapter Registry

Phase 12E / 12F
"""

from __future__ import annotations

from .connected import ConnectedWorkspaceAdapter
from .documents import ResearchDocumentAdapter
from .github import GitHubWorkspaceAdapter
from .knowledge import KnowledgeWorkspaceAdapter
from .local import LocalWorkspaceAdapter
from .memory import MemoryWorkspaceAdapter
from .notion import NotionWorkspaceAdapter
from .repository import RepositoryGraphAdapter
from .research import ResearchAdapter


_ADAPTERS = {}


def register_adapter(
    adapter,
):
    _ADAPTERS[
        adapter.name
    ] = adapter

    return adapter


def get_adapter(
    name: str,
):
    return _ADAPTERS.get(
        name
    )


def list_adapters():
    return dict(
        _ADAPTERS
    )


def load_default_adapters():
    defaults = [
        LocalWorkspaceAdapter(),
        GitHubWorkspaceAdapter(),
        NotionWorkspaceAdapter(),
        RepositoryGraphAdapter(),
        MemoryWorkspaceAdapter(),
        KnowledgeWorkspaceAdapter(),
        ResearchDocumentAdapter(),
        ConnectedWorkspaceAdapter(),
        ResearchAdapter(),
    ]

    for adapter in defaults:
        if adapter.name not in _ADAPTERS:
            register_adapter(
                adapter
            )

    return list_adapters()