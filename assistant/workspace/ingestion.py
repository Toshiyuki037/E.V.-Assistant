"""
E.V.I.E. - Workspace Source Ingestion

Phase 12B

Purpose:
Run one or more source adapters and persist normalized evidence into the
Phase 12 workspace store.
"""

from __future__ import annotations

from .adapters.base import AdapterContext
from .adapters.registry import (
    get_adapter,
    load_default_adapters,
)
from .evidence import save_evidence


def ingest_from_adapter(
    adapter_name: str,
    query: str,
    *,
    project: str = "",
    repository: str = "",
    workspace_path: str = "",
    arguments: dict | None = None,
):
    load_default_adapters()

    adapter = get_adapter(
        adapter_name
    )

    if adapter is None:
        raise RuntimeError(
            (
                "Workspace adapter "
                f"does not exist: {adapter_name}"
            )
        )

    context = AdapterContext(
        project=project,
        repository=repository,
        workspace_path=workspace_path,
        arguments=arguments or {},
    )

    evidence = adapter.search(
        query,
        context,
    )

    for item in evidence:
        save_evidence(
            item
        )

    return evidence


def ingest_many(
    adapter_names: list[str],
    query: str,
    **kwargs,
):
    results = []

    for adapter_name in adapter_names:
        results.extend(
            ingest_from_adapter(
                adapter_name,
                query,
                **kwargs,
            )
        )

    return results
