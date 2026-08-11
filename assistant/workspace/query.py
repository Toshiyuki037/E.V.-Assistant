"""
E.V.I.E. - Cross-Source Workspace Query Engine

Phase 12D - Source Diversity Fix

Queries multiple workspace adapters, deduplicates evidence, ranks it,
and preserves cross-source diversity so local source code cannot crowd
GitHub/Notion/repository evidence out of the synthesis window.
"""

from __future__ import annotations

from collections import defaultdict

from assistant.workspace.models import (
    WorkspaceQuery,
    WorkspaceResult,
)
from assistant.workspace.ranking import (
    rank_evidence,
)

from .adapters.base import (
    AdapterContext,
)
from .adapters.registry import (
    get_adapter,
    load_default_adapters,
)


DEFAULT_SOURCES = (
    "repository",
    "local",
    "github",
    "notion",
)


def _dedupe(
    evidence,
):
    seen = set()
    results = []

    for item in evidence:
        key = (
            item.source_type,
            item.source_id,
            item.path,
            item.content,
        )

        if key in seen:
            continue

        seen.add(
            key
        )

        results.append(
            item
        )

    return results


def _balanced_select(
    evidence,
    *,
    limit: int,
    minimum_per_source: int = 2,
):
    """
    Preserve at least a small amount of evidence from each source type
    when that source returned useful results, then fill remaining slots
    by global relevance.
    """

    if not evidence:
        return []

    limit = max(
        1,
        int(
            limit
            or 1
        ),
    )

    grouped = defaultdict(
        list
    )

    for item in evidence:
        grouped[
            item.source_type
        ].append(
            item
        )

    for source_type in grouped:
        grouped[
            source_type
        ].sort(
            key=lambda item: (
                item.relevance,
                item.confidence,
            ),
            reverse=True,
        )

    selected = []
    selected_ids = set()

    # First preserve source diversity.
    for source_type in sorted(
        grouped.keys()
    ):
        for item in grouped[
            source_type
        ][
            :minimum_per_source
        ]:
            if len(
                selected
            ) >= limit:
                break

            if item.evidence_id in selected_ids:
                continue

            selected.append(
                item
            )
            selected_ids.add(
                item.evidence_id
            )

    # Then fill by overall rank.
    for item in evidence:
        if len(
            selected
        ) >= limit:
            break

        if item.evidence_id in selected_ids:
            continue

        selected.append(
            item
        )
        selected_ids.add(
            item.evidence_id
        )

    selected.sort(
        key=lambda item: (
            item.relevance,
            item.confidence,
        ),
        reverse=True,
    )

    return selected[
        :limit
    ]


def search_workspace(
    workspace_query: WorkspaceQuery,
    *,
    workspace_path: str = ".",
    adapter_names: list[str] | None = None,
    adapter_arguments: dict | None = None,
):
    load_default_adapters()

    adapter_names = (
        adapter_names
        or list(
            DEFAULT_SOURCES
        )
    )

    adapter_arguments = (
        adapter_arguments
        or {}
    )

    evidence = []
    errors = []
    source_counts = {}

    for name in adapter_names:
        adapter = get_adapter(
            name
        )

        if adapter is None:
            errors.append(
                {
                    "source": name,
                    "error": "adapter_not_found",
                }
            )
            continue

        context = AdapterContext(
            project=workspace_query.project,
            repository=workspace_query.repository,
            workspace_path=workspace_path,
            arguments=(
                adapter_arguments.get(
                    name,
                    {}
                )
                if isinstance(
                    adapter_arguments.get(
                        name,
                        {}
                    ),
                    dict,
                )
                else {}
            ),
        )

        try:
            results = adapter.search(
                workspace_query.query,
                context,
            )

            source_counts[
                name
            ] = len(
                results
            )

            evidence.extend(
                results
            )

        except Exception as error:
            source_counts[
                name
            ] = 0

            errors.append(
                {
                    "source": name,
                    "error": str(
                        error
                    ),
                }
            )

    evidence = _dedupe(
        evidence
    )

    evidence = rank_evidence(
        workspace_query.query,
        evidence,
    )

    evidence = _balanced_select(
        evidence,
        limit=workspace_query.limit,
        minimum_per_source=int(
            workspace_query.metadata.get(
                "minimum_per_source",
                2,
            )
            or 2
        ),
    )

    selected_counts = defaultdict(
        int
    )

    for item in evidence:
        selected_counts[
            item.source_type
        ] += 1

    return WorkspaceResult(
        query=workspace_query.query,
        evidence=evidence,
        metadata={
            "sources_requested":
                adapter_names,
            "source_errors":
                errors,
            "source_counts":
                source_counts,
            "selected_source_counts":
                dict(
                    selected_counts
                ),
            "evidence_count":
                len(
                    evidence
                ),
        },
    )
