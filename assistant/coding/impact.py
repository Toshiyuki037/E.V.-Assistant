"""
E.V.I.E. - Repository Impact Analysis

Phase 12H

Purpose:
Use the Phase 12C repository graph to determine what a proposed code
change may affect before E.V.I.E. edits anything.

This module is read-only.

Important:
Repository graphs contain file, function, class, and test nodes that can
share the same path. Impact analysis must resolve a requested path to
the FILE/TEST module node because import edges are attached to module
nodes, not function/class nodes.
"""

from __future__ import annotations

from collections import deque

from assistant.workspace.repository.controller import (
    get_repository_graph,
)

from assistant.workspace.repository.models import (
    EDGE_IMPORTS,
    EDGE_TESTS,
    NODE_FILE,
    NODE_TEST,
)


# ---------------------------------------------------------------------------
# Graph Maps
# ---------------------------------------------------------------------------

def _node_maps(
    graph,
):
    by_id = {
        node.node_id:
            node
        for node
        in graph.nodes
    }

    # Critical: only module-level file/test nodes belong in path lookup.
    # Function/class nodes also carry .path and would otherwise overwrite
    # the actual file node in this dictionary.
    by_path = {
        node.path:
            node
        for node
        in graph.nodes
        if (
            node.path
            and node.node_type
            in {
                NODE_FILE,
                NODE_TEST,
            }
        )
    }

    return (
        by_id,
        by_path,
    )


def _reverse_import_map(
    graph,
):
    reverse = {}

    for edge in graph.edges:
        if edge.edge_type != EDGE_IMPORTS:
            continue

        reverse.setdefault(
            edge.target_node_id,
            set(),
        ).add(
            edge.source_node_id
        )

    return reverse


def _forward_import_map(
    graph,
):
    forward = {}

    for edge in graph.edges:
        if edge.edge_type != EDGE_IMPORTS:
            continue

        forward.setdefault(
            edge.source_node_id,
            set(),
        ).add(
            edge.target_node_id
        )

    return forward


def _test_map(
    graph,
):
    tests = {}

    for edge in graph.edges:
        if edge.edge_type != EDGE_TESTS:
            continue

        tests.setdefault(
            edge.target_node_id,
            set(),
        ).add(
            edge.source_node_id
        )

    return tests


# ---------------------------------------------------------------------------
# Traversal
# ---------------------------------------------------------------------------

def _walk_dependents(
    start_id: str,
    reverse_imports: dict,
    *,
    max_depth: int = 4,
):
    visited = {
        start_id
    }

    queue = deque(
        [
            (
                start_id,
                0,
            )
        ]
    )

    results = {}

    while queue:
        node_id, depth = (
            queue.popleft()
        )

        if depth >= max_depth:
            continue

        for dependent_id in (
            reverse_imports.get(
                node_id,
                set(),
            )
        ):
            if dependent_id in visited:
                continue

            visited.add(
                dependent_id
            )

            next_depth = (
                depth
                + 1
            )

            results[
                dependent_id
            ] = next_depth

            queue.append(
                (
                    dependent_id,
                    next_depth,
                )
            )

    return results


# ---------------------------------------------------------------------------
# Single File
# ---------------------------------------------------------------------------

def analyze_file_impact(
    repository: str,
    path: str,
    *,
    max_depth: int = 4,
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

    by_id, by_path = (
        _node_maps(
            graph
        )
    )

    target = by_path.get(
        path
    )

    if target is None:
        raise ValueError(
            (
                "Repository file path not found "
                f"in graph: {path}"
            )
        )

    reverse_imports = (
        _reverse_import_map(
            graph
        )
    )

    forward_imports = (
        _forward_import_map(
            graph
        )
    )

    test_map = _test_map(
        graph
    )

    direct_import_ids = (
        forward_imports.get(
            target.node_id,
            set(),
        )
    )

    direct_importer_ids = (
        reverse_imports.get(
            target.node_id,
            set(),
        )
    )

    dependent_depths = (
        _walk_dependents(
            target.node_id,
            reverse_imports,
            max_depth=max_depth,
        )
    )

    test_ids = (
        test_map.get(
            target.node_id,
            set(),
        )
    )

    direct_imports = sorted(
        [
            by_id[
                node_id
            ]
            for node_id
            in direct_import_ids
            if node_id
            in by_id
        ],
        key=lambda node:
            node.path,
    )

    direct_importers = sorted(
        [
            by_id[
                node_id
            ]
            for node_id
            in direct_importer_ids
            if node_id
            in by_id
        ],
        key=lambda node:
            node.path,
    )

    transitive_importers = [
        {
            "node":
                by_id[
                    node_id
                ],

            "depth":
                depth,
        }
        for node_id, depth
        in sorted(
            dependent_depths.items(),
            key=lambda pair:
                (
                    pair[
                        1
                    ],
                    (
                        by_id[
                            pair[
                                0
                            ]
                        ].path
                        if pair[
                            0
                        ]
                        in by_id
                        else ""
                    ),
                ),
        )
        if node_id
        in by_id
    ]

    tests = sorted(
        [
            by_id[
                node_id
            ]
            for node_id
            in test_ids
            if node_id
            in by_id
        ],
        key=lambda node:
            node.path,
    )

    importer_count = len(
        dependent_depths
    )

    if importer_count >= 10:
        risk = "high"

    elif importer_count >= 3:
        risk = "medium"

    else:
        risk = "low"

    return {
        "repository":
            repository,

        "path":
            path,

        "target":
            target,

        "direct_imports":
            direct_imports,

        "direct_importers":
            direct_importers,

        "transitive_importers":
            transitive_importers,

        "tests":
            tests,

        "impact_count":
            importer_count,

        "risk":
            risk,
    }


# ---------------------------------------------------------------------------
# Multi-File Scope
# ---------------------------------------------------------------------------

def analyze_change_scope(
    repository: str,
    paths: list[str],
    *,
    max_depth: int = 4,
):
    analyses = [
        analyze_file_impact(
            repository,
            path,
            max_depth=max_depth,
        )
        for path
        in paths
    ]

    impacted = {}
    tests = {}

    highest_risk = "low"

    risk_rank = {
        "low": 1,
        "medium": 2,
        "high": 3,
    }

    for analysis in analyses:
        if (
            risk_rank[
                analysis[
                    "risk"
                ]
            ]
            > risk_rank[
                highest_risk
            ]
        ):
            highest_risk = (
                analysis[
                    "risk"
                ]
            )

        for item in (
            analysis[
                "transitive_importers"
            ]
        ):
            node = item[
                "node"
            ]

            existing = (
                impacted.get(
                    node.node_id
                )
            )

            if (
                existing is None
                or item[
                    "depth"
                ]
                < existing[
                    "depth"
                ]
            ):
                impacted[
                    node.node_id
                ] = item

        for node in (
            analysis[
                "tests"
            ]
        ):
            tests[
                node.node_id
            ] = node

    return {
        "repository":
            repository,

        "paths":
            list(
                paths
            ),

        "analyses":
            analyses,

        "impacted_nodes":
            sorted(
                impacted.values(),
                key=lambda item:
                    (
                        item[
                            "depth"
                        ],
                        item[
                            "node"
                        ].path,
                    ),
            ),

        "tests":
            sorted(
                tests.values(),
                key=lambda node:
                    node.path,
            ),

        "risk":
            highest_risk,
    }
