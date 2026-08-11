"""
E.V.I.E. - Repository Workspace Controller

Phase 12C
"""

from __future__ import annotations

from .graph import (
    build_repository_graph,
)

from .query import (
    explain_node,
    find_nodes,
)

from .store import (
    load_repository_graph,
    save_repository_graph,
)


def index_repository(
    root_path: str,
    *,
    repository: str,
):
    graph = (
        build_repository_graph(
            root_path,
            repository=repository,
        )
    )

    save_repository_graph(
        graph
    )

    return graph


def get_repository_graph(
    repository: str,
):
    return load_repository_graph(
        repository
    )


def search_repository_graph(
    repository: str,
    query: str,
    *,
    limit: int = 50,
):
    graph = get_repository_graph(
        repository
    )

    if graph is None:
        raise RuntimeError(
            (
                "Repository graph does not exist: "
                f"{repository}"
            )
        )

    return find_nodes(
        graph,
        query,
        limit=limit,
    )


def explain_repository_node(
    repository: str,
    node_id: str,
):
    graph = get_repository_graph(
        repository
    )

    if graph is None:
        raise RuntimeError(
            (
                "Repository graph does not exist: "
                f"{repository}"
            )
        )

    return explain_node(
        graph,
        node_id,
    )
