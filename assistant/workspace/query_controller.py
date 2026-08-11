"""
E.V.I.E. - Unified Workspace Query Controller

Phase 12D - Source Diversity
"""

from __future__ import annotations

from assistant.workspace.models import (
    WorkspaceQuery,
)

from .query import (
    search_workspace,
)
from .synthesis import (
    synthesize_workspace_result,
)


def query_workspace(
    query: str,
    *,
    project: str = "",
    repository: str = "",
    workspace_path: str = ".",
    sources: list[str] | None = None,
    limit: int = 30,
    synthesize: bool = True,
    adapter_arguments: dict | None = None,
    minimum_per_source: int = 2,
):
    request = WorkspaceQuery(
        query=query,
        project=project,
        repository=repository,
        limit=limit,
        metadata={
            "minimum_per_source":
                minimum_per_source,
        },
    )

    result = search_workspace(
        request,
        workspace_path=workspace_path,
        adapter_names=sources,
        adapter_arguments=adapter_arguments,
    )

    if synthesize:
        result = synthesize_workspace_result(
            result
        )

    return result


def format_workspace_sources(
    result,
):
    lines = []

    for index, item in enumerate(
        result.evidence,
        start=1,
    ):
        location = (
            item.path
            or item.uri
            or item.source_id
        )

        lines.append(
            (
                f"[{index}] {item.source_type}: "
                f"{item.title or location}"
                + (
                    f" — {location}"
                    if location
                    and location
                    != item.title
                    else ""
                )
            )
        )

    return "\n".join(
        lines
    )
