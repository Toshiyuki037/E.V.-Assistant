"""
E.V.I.E. - Repository Graph Query

Phase 12C
"""

from __future__ import annotations

from .models import (
    EDGE_IMPORTS,
    EDGE_TESTS,
)


def node_map(
    graph,
):
    return {
        node.node_id:
            node
        for node
        in graph.nodes
    }


def find_nodes(
    graph,
    query: str,
    *,
    limit: int = 50,
):
    lowered = (
        str(
            query
            or ""
        )
        .strip()
        .lower()
    )

    if not lowered:
        return graph.nodes[
            :limit
        ]

    matches = []

    for node in graph.nodes:
        haystack = (
            " ".join(
                [
                    node.name,
                    node.path,
                    node.module,
                    node.package,
                    node.node_type,
                ]
            )
            .lower()
        )

        if lowered in haystack:
            matches.append(
                node
            )

        if len(matches) >= limit:
            break

    return matches


def imports_of(
    graph,
    node_id: str,
):
    mapping = node_map(
        graph
    )

    return [
        mapping[
            edge.target_node_id
        ]
        for edge
        in graph.edges
        if (
            edge.edge_type
            == EDGE_IMPORTS
            and edge.source_node_id
            == node_id
            and edge.target_node_id
            in mapping
        )
    ]


def imported_by(
    graph,
    node_id: str,
):
    mapping = node_map(
        graph
    )

    return [
        mapping[
            edge.source_node_id
        ]
        for edge
        in graph.edges
        if (
            edge.edge_type
            == EDGE_IMPORTS
            and edge.target_node_id
            == node_id
            and edge.source_node_id
            in mapping
        )
    ]


def tests_for(
    graph,
    node_id: str,
):
    mapping = node_map(
        graph
    )

    return [
        mapping[
            edge.source_node_id
        ]
        for edge
        in graph.edges
        if (
            edge.edge_type
            == EDGE_TESTS
            and edge.target_node_id
            == node_id
            and edge.source_node_id
            in mapping
        )
    ]


def explain_node(
    graph,
    node_id: str,
):
    mapping = node_map(
        graph
    )

    node = mapping.get(
        node_id
    )

    if node is None:
        return None

    return {
        "node":
            node,
        "imports":
            imports_of(
                graph,
                node_id,
            ),
        "imported_by":
            imported_by(
                graph,
                node_id,
            ),
        "tests":
            tests_for(
                graph,
                node_id,
            ),
    }
