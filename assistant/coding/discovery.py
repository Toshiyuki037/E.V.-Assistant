"""
E.V.I.E. - Self-Engineering Candidate Discovery

Phase 12N Final

Purpose:
Find the smallest coherent repository context for a self-engineering task.

Pipeline:
    user engineering goal
        ->
    corpus-aware source ranking
        ->
    strongest implementation files
        ->
    repository import graph
        ->
    relevant regression tests
        ->
    bounded candidate_paths

This module is read-only.
"""

from __future__ import annotations

from collections import (
    Counter,
    defaultdict,
)

from pathlib import Path

import math
import re

from assistant.workspace.query_expansion import (
    significant_tokens,
)

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
# Generic Engineering Vocabulary
# ---------------------------------------------------------------------------

GENERIC_WORDS = {
    "a",
    "an",
    "and",
    "approach",
    "approve",
    "approved",
    "before",
    "change",
    "changes",
    "code",
    "codebase",
    "commit",
    "create",
    "diagnose",
    "display-only",
    "do",
    "engineering",
    "evie",
    "e.v.i.e.",
    "execute",
    "execution",
    "executable",
    "fix",
    "full",
    "generated",
    "improve",
    "improvement",
    "in",
    "include",
    "keep",
    "make",
    "minimal",
    "minimum",
    "modify",
    "necessary",
    "not",
    "only",
    "own",
    "plan",
    "prepare",
    "regression",
    "repository",
    "run",
    "safe",
    "self",
    "self-engineering",
    "semantics",
    "source",
    "stop",
    "suite",
    "targeted",
    "test",
    "tests",
    "the",
    "until",
    "validation",
    "your",
}


TOKEN_RE = re.compile(
    r"[a-zA-Z_][a-zA-Z0-9_./-]*"
)


# ---------------------------------------------------------------------------
# Query Helpers
# ---------------------------------------------------------------------------

def _normalize(
    value: str,
):
    return (
        str(
            value
            or ""
        )
        .lower()
        .replace(
            "\\",
            "/",
        )
    )


def _query_tokens(
    goal: str,
):
    result = []

    for token in significant_tokens(
        goal
    ):
        token = re.sub(
            r"[^a-z0-9_.-]+",
            "",
            str(
                token
                or ""
            ).lower(),
        )

        if not token:
            continue

        if token in GENERIC_WORDS:
            continue

        if len(
            token
        ) < 3:
            continue

        if token not in result:
            result.append(
                token
            )

    return result[
        :24
    ]


# ---------------------------------------------------------------------------
# File Reading
# ---------------------------------------------------------------------------

def _safe_read(
    root: Path,
    relative_path: str,
):
    target = (
        root
        / relative_path
    ).resolve()

    try:
        target.relative_to(
            root
        )

    except ValueError:
        return ""

    if (
        not target.exists()
        or not target.is_file()
    ):
        return ""

    try:
        return target.read_text(
            encoding="utf-8",
            errors="ignore",
        )

    except OSError:
        return ""


def _document_text(
    node,
    content: str,
):
    return _normalize(
        " ".join(
            [
                node.path
                or "",

                node.name
                or "",

                node.module
                or "",

                node.package
                or "",

                content,
            ]
        )
    )


# ---------------------------------------------------------------------------
# Term Matching
# ---------------------------------------------------------------------------

def _term_count(
    text: str,
    token: str,
):
    literal = text.count(
        token
    )

    if (
        "_"
        in token
        or "."
        in token
        or "/"
        in token
        or "-"
        in token
    ):
        return literal

    identifier_hits = 0

    for word in TOKEN_RE.findall(
        text
    ):
        parts = re.split(
            r"[_./-]+",
            word.lower(),
        )

        if token in parts:
            identifier_hits += 1

    return max(
        literal,
        identifier_hits,
    )


# ---------------------------------------------------------------------------
# Graph Helpers
# ---------------------------------------------------------------------------

def _module_nodes_by_path(
    graph,
):
    result = {}

    for node in graph.nodes:

        if not node.path:
            continue

        if node.node_type not in {
            NODE_FILE,
            NODE_TEST,
        }:
            continue

        existing = result.get(
            node.path
        )

        # Prefer normal FILE module nodes when duplicate path nodes exist.
        if (
            existing is None
            or node.node_type
            == NODE_FILE
        ):
            result[
                node.path
            ] = node

    return result


def _node_map(
    graph,
):
    return {
        node.node_id:
            node
        for node
        in graph.nodes
    }


def _direct_test_paths_for_sources(
    graph,
    source_paths,
):
    """
    Find regression tests structurally connected to selected source modules.

    Supports:
    - explicit EDGE_TESTS relationships
    - test modules importing source modules through EDGE_IMPORTS
    """

    modules = _module_nodes_by_path(
        graph
    )

    by_id = _node_map(
        graph
    )

    source_ids = {
        modules[
            path
        ].node_id
        for path
        in source_paths
        if path
        in modules
    }

    discovered = set()

    for edge in graph.edges:

        # ---------------------------------------------------------------
        # Explicit test relationship
        # ---------------------------------------------------------------

        if edge.edge_type == EDGE_TESTS:

            if (
                edge.target_node_id
                in source_ids
            ):
                test_node = by_id.get(
                    edge.source_node_id
                )

                if (
                    test_node is not None
                    and test_node.path
                ):
                    discovered.add(
                        test_node.path
                    )

            continue


        # ---------------------------------------------------------------
        # Test imports implementation module
        # ---------------------------------------------------------------

        if edge.edge_type != EDGE_IMPORTS:
            continue

        if (
            edge.target_node_id
            not in source_ids
        ):
            continue

        importer = by_id.get(
            edge.source_node_id
        )

        if importer is None:
            continue

        if not importer.path:
            continue

        if (
            importer.node_type
            == NODE_TEST
            or importer.path.startswith(
                "tests/"
            )
        ):
            discovered.add(
                importer.path
            )

    return sorted(
        discovered
    )


# ---------------------------------------------------------------------------
# Main Discovery
# ---------------------------------------------------------------------------

def discover_candidate_paths(
    repository: str,
    goal: str,
    *,
    max_candidates: int = 8,
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

    tokens = _query_tokens(
        goal
    )

    if not tokens:
        return []

    root = Path(
        graph.root_path
    ).resolve()

    # -----------------------------------------------------------------------
    # Build one repository document per module-level path
    # -----------------------------------------------------------------------

    documents = {}

    for node in graph.nodes:

        if node.node_type not in {
            NODE_FILE,
            NODE_TEST,
        }:
            continue

        if not node.path:
            continue

        existing = documents.get(
            node.path
        )

        if existing is not None:

            if (
                existing[
                    "node"
                ].node_type
                == NODE_FILE
                and node.node_type
                != NODE_FILE
            ):
                continue

        content = _safe_read(
            root,
            node.path,
        )

        documents[
            node.path
        ] = {
            "node":
                node,

            "content":
                content,

            "text":
                _document_text(
                    node,
                    content,
                ),
        }

    if not documents:
        return []


    # -----------------------------------------------------------------------
    # Corpus-aware IDF
    # -----------------------------------------------------------------------

    document_frequency = Counter()

    for token in tokens:

        for item in documents.values():

            if (
                _term_count(
                    item[
                        "text"
                    ],
                    token,
                )
                > 0
            ):
                document_frequency[
                    token
                ] += 1

    total_docs = len(
        documents
    )

    idf = {}

    for token in tokens:

        df = document_frequency.get(
            token,
            0,
        )

        idf[
            token
        ] = math.log(
            1.0
            + (
                (
                    total_docs
                    - df
                    + 0.5
                )
                / (
                    df
                    + 0.5
                )
            )
        )


    # -----------------------------------------------------------------------
    # Score source files and tests
    # -----------------------------------------------------------------------

    scores = defaultdict(
        float
    )

    matched_terms = defaultdict(
        set
    )

    for path, item in (
        documents.items()
    ):
        node = item[
            "node"
        ]

        text = item[
            "text"
        ]

        path_text = _normalize(
            " ".join(
                [
                    node.path
                    or "",

                    node.name
                    or "",

                    node.module
                    or "",

                    node.package
                    or "",
                ]
            )
        )

        for token in tokens:

            term_idf = idf[
                token
            ]

            path_count = _term_count(
                path_text,
                token,
            )

            content_count = _term_count(
                text,
                token,
            )

            if (
                path_count == 0
                and content_count == 0
            ):
                continue

            matched_terms[
                path
            ].add(
                token
            )

            # Path/module names are highly meaningful.
            if path_count:

                scores[
                    path
                ] += (
                    5.0
                    * term_idf
                    * min(
                        path_count,
                        3,
                    )
                )

            # Saturating source-content score.
            if content_count:

                tf = (
                    content_count
                    / (
                        content_count
                        + 2.0
                    )
                )

                scores[
                    path
                ] += (
                    7.0
                    * term_idf
                    * tf
                )


        distinct = len(
            matched_terms[
                path
            ]
        )


        # -------------------------------------------------------------------
        # Multi-concept bonus
        # -------------------------------------------------------------------

        if distinct >= 2:

            scores[
                path
            ] += (
                distinct
                * 2.5
            )


        if distinct >= 3:

            scores[
                path
            ] += 6.0


        # -------------------------------------------------------------------
        # Prefer implementation modules during initial source selection
        # -------------------------------------------------------------------

        if (
            node.node_type
            == NODE_FILE
        ):
            scores[
                path
            ] += 3.0


    # -----------------------------------------------------------------------
    # Rank implementation files first
    # -----------------------------------------------------------------------

    ranked_sources = sorted(
        [
            path
            for path in scores
            if (
                documents[
                    path
                ][
                    "node"
                ].node_type
                == NODE_FILE
                and scores[
                    path
                ]
                > 0
            )
        ],
        key=lambda path:
            (
                scores[
                    path
                ],

                len(
                    matched_terms[
                        path
                    ]
                ),

                path,
            ),
        reverse=True,
    )


    # -----------------------------------------------------------------------
    # Choose strongest source candidates
    # -----------------------------------------------------------------------

    limit = max(
        1,
        int(
            max_candidates
            or 1
        ),
    )

    # Reserve up to two slots for structurally relevant tests.
    structural_test_quota = min(
        2,
        max(
            1,
            limit
            // 4
        ),
    )

    source_limit = max(
        1,
        limit
        - structural_test_quota
    )

    selected_sources = ranked_sources[
        :source_limit
    ]


    # -----------------------------------------------------------------------
    # STRUCTURAL TEST EXPANSION
    # -----------------------------------------------------------------------
    #
    # This is the important final Phase 12N improvement.
    #
    # Once implementation candidates are known, ask the repository graph:
    #
    #     Which tests directly exercise/import these modules?
    #
    # instead of hoping test filenames happen to match the user prompt.
    # -----------------------------------------------------------------------

    structural_tests = (
        _direct_test_paths_for_sources(
            graph,
            selected_sources,
        )
    )


    # Rank discovered tests by their lexical score when available.
    structural_tests = sorted(
        structural_tests,
        key=lambda path:
            (
                scores.get(
                    path,
                    0.0,
                ),

                len(
                    matched_terms.get(
                        path,
                        set(),
                    )
                ),

                path,
            ),
        reverse=True,
    )


    selected_tests = structural_tests[
        :structural_test_quota
    ]


    # -----------------------------------------------------------------------
    # Fallback lexical tests
    # -----------------------------------------------------------------------

    if (
        len(
            selected_tests
        )
        < structural_test_quota
    ):

        ranked_tests = sorted(
            [
                path
                for path in scores
                if (
                    documents[
                        path
                    ][
                        "node"
                    ].node_type
                    == NODE_TEST
                    and scores[
                        path
                    ]
                    > 0
                    and path
                    not in selected_tests
                )
            ],
            key=lambda path:
                (
                    scores[
                        path
                    ],

                    len(
                        matched_terms[
                            path
                        ]
                    ),

                    path,
                ),
            reverse=True,
        )

        missing = (
            structural_test_quota
            - len(
                selected_tests
            )
        )

        selected_tests.extend(
            ranked_tests[
                :missing
            ]
        )


    # -----------------------------------------------------------------------
    # Combine bounded context
    # -----------------------------------------------------------------------

    selected = []

    for path in (
        selected_sources
        + selected_tests
    ):

        if path not in selected:
            selected.append(
                path
            )


    # -----------------------------------------------------------------------
    # Fill unused candidate slots
    # -----------------------------------------------------------------------

    if len(
        selected
    ) < limit:

        remaining_sources = [
            path
            for path in ranked_sources
            if path not in selected
        ]

        for path in remaining_sources:

            if len(
                selected
            ) >= limit:
                break

            selected.append(
                path
            )


    return selected[
        :limit
    ]