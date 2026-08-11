"""
E.V.I.E. - Repository Graph Store

Phase 12C
"""

from __future__ import annotations

import json

from pathlib import Path

from .models import (
    RepositoryEdge,
    RepositoryGraph,
    RepositoryNode,
    graph_to_dict,
)


PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[3]
)

REPOSITORY_RUNTIME = (
    PROJECT_ROOT
    / "runtime"
    / "workspace"
    / "repositories"
)


def _safe(
    value: str,
):
    return (
        str(
            value
            or ""
        )
        .replace(
            "/",
            "_",
        )
        .replace(
            "\\",
            "_",
        )
        .replace(
            ":",
            "_",
        )
    )


def graph_path(
    repository: str,
):
    return (
        REPOSITORY_RUNTIME
        / (
            _safe(
                repository
            )
            + ".json"
        )
    )


def save_repository_graph(
    graph: RepositoryGraph,
):
    REPOSITORY_RUNTIME.mkdir(
        parents=True,
        exist_ok=True,
    )

    path = graph_path(
        graph.repository
    )

    temp = path.with_suffix(
        ".json.tmp"
    )

    temp.write_text(
        json.dumps(
            graph_to_dict(
                graph
            ),
            indent=2,
            ensure_ascii=False,
            default=str,
        ),
        encoding="utf-8",
    )

    temp.replace(
        path
    )

    return graph


def load_repository_graph(
    repository: str,
):
    path = graph_path(
        repository
    )

    if not path.exists():
        return None

    data = json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )

    nodes = [
        RepositoryNode(
            **item
        )
        for item
        in (
            data.get(
                "nodes",
                []
            )
            or []
        )
    ]

    edges = [
        RepositoryEdge(
            **item
        )
        for item
        in (
            data.get(
                "edges",
                []
            )
            or []
        )
    ]

    return RepositoryGraph(
        repository=data.get(
            "repository",
            repository,
        ),
        root_path=data.get(
            "root_path",
            "",
        ),
        nodes=nodes,
        edges=edges,
        metadata=data.get(
            "metadata",
            {},
        ),
    )
