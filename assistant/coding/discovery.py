"""
E.V.I.E. - Self-Engineering Candidate Discovery

Phase 12N

Hybrid read-only candidate discovery using:
1. repository graph search
2. file-path/module-name relevance
3. direct source-content relevance
4. light structural preference for source modules over tests

This module performs no edits.
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from assistant.workspace.query_expansion import (
    significant_tokens,
)
from assistant.workspace.repository.controller import (
    get_repository_graph,
    search_repository_graph,
)
from assistant.workspace.repository.models import (
    NODE_FILE,
    NODE_TEST,
)


GENERIC_ENGINEERING_WORDS = {
    "fix",
    "repair",
    "debug",
    "diagnose",
    "investigate",
    "change",
    "modify",
    "update",
    "improve",
    "implement",
    "code",
    "source",
    "repository",
    "repo",
    "your",
    "own",
    "evie",
    "e.v.i.e.",
    "assistant",
}


def _useful_tokens(
    goal: str,
):
    return [
        token
        for token in significant_tokens(
            goal
        )
        if token.lower()
        not in GENERIC_ENGINEERING_WORDS
    ]


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

    root = Path(
        graph.root_path
    ).resolve()

    tokens = _useful_tokens(
        goal
    )

    scores = defaultdict(
        float
    )

    # ------------------------------------------------------------------
    # 1. Repository graph search
    # ------------------------------------------------------------------

    search_terms = []

    if goal.strip():
        search_terms.append(
            goal.strip()
        )

    search_terms.extend(
        tokens[
            :16
        ]
    )

    seen_terms = set()

    for term in search_terms:
        lowered = term.lower()

        if lowered in seen_terms:
            continue

        seen_terms.add(
            lowered
        )

        try:
            nodes = search_repository_graph(
                repository,
                term,
            )
        except Exception:
            nodes = []

        for rank, node in enumerate(
            nodes[
                :60
            ],
            start=1,
        ):
            if node.node_type not in {
                NODE_FILE,
                NODE_TEST,
            }:
                continue

            if not node.path:
                continue

            source_bonus = (
                4.0
                if node.node_type
                == NODE_FILE
                else 0.5
            )

            scores[
                node.path
            ] += (
                source_bonus
                + max(
                    0.0,
                    6.0
                    - (
                        rank
                        * 0.1
                    ),
                )
            )

    # ------------------------------------------------------------------
    # 2. Direct file/module/content scoring
    # ------------------------------------------------------------------

    for node in graph.nodes:
        if node.node_type not in {
            NODE_FILE,
            NODE_TEST,
        }:
            continue

        if not node.path:
            continue

        content = _safe_read(
            root,
            node.path,
        )

        path_text = (
            f"{node.path} "
            f"{node.name} "
            f"{node.module} "
            f"{node.package}"
        ).lower()

        content_lower = (
            content.lower()
        )

        path_overlap = 0
        content_overlap = 0
        content_hits = 0

        for token in tokens:
            token = token.lower()

            if token in path_text:
                path_overlap += 1

            count = content_lower.count(
                token
            )

            if count:
                content_overlap += 1
                content_hits += min(
                    count,
                    5,
                )

        if (
            path_overlap == 0
            and content_overlap == 0
        ):
            continue

        source_bonus = (
            5.0
            if node.node_type
            == NODE_FILE
            else 0.25
        )

        # Path/module matches are strongest.
        scores[
            node.path
        ] += (
            source_bonus
            + (
                path_overlap
                * 7.0
            )
            + (
                content_overlap
                * 3.0
            )
            + min(
                8.0,
                content_hits
                * 0.4,
            )
        )

        # A file matching multiple distinct request concepts is often
        # a much better engineering candidate than a file matching one.
        if content_overlap >= 2:
            scores[
                node.path
            ] += (
                content_overlap
                * 2.5
            )

    # ------------------------------------------------------------------
    # 3. Prefer source modules to tests for edit candidates
    # ------------------------------------------------------------------

    node_types = {
        node.path:
            node.node_type
        for node in graph.nodes
        if node.path
        and node.node_type
        in {
            NODE_FILE,
            NODE_TEST,
        }
    }

    ordered = sorted(
        scores.items(),
        key=lambda pair: (
            pair[
                1
            ],
            (
                1
                if node_types.get(
                    pair[
                        0
                    ]
                )
                == NODE_FILE
                else 0
            ),
            pair[
                0
            ],
        ),
        reverse=True,
    )

    return [
        path
        for path, _
        in ordered[
            :max(
                1,
                int(
                    max_candidates
                    or 1
                ),
            )
        ]
    ]
