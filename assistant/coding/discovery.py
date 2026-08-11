"""
E.V.I.E. - Self-Engineering Candidate Discovery

Phase 12N v3

Corpus-aware read-only candidate discovery.

Why v3 exists:
The first two live tests showed that generic engineering words and generic
modules could still outrank the actual subsystem. v3 uses a small BM25/IDF-
style scorer over repository file paths + contents so rare domain concepts
such as "timezone" and "schedule" naturally matter more than common words
such as "validation", "workflow", or "plan".

No edits or tool execution occur here.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
import math
import re

from assistant.workspace.query_expansion import significant_tokens
from assistant.workspace.repository.controller import get_repository_graph
from assistant.workspace.repository.models import NODE_FILE, NODE_TEST


GENERIC_WORDS = {
    "a", "an", "and", "approach", "approve", "approved", "before",
    "change", "changes", "code", "codebase", "create", "diagnose",
    "display-only", "do", "engineering", "evie", "e.v.i.e.", "execute",
    "execution", "executable", "fix", "full", "generated", "improve",
    "improvement", "in", "include", "keep", "make", "minimal", "minimum",
    "modify", "necessary", "not", "only", "own", "plan", "prepare",
    "regression", "repository", "run", "safe", "self", "self-engineering",
    "semantics", "source", "stop", "suite", "test", "tests", "the",
    "until", "validation", "targeted", "commit", "your",
}

TOKEN_RE = re.compile(r"[a-zA-Z_][a-zA-Z0-9_./-]*")


def _normalize(value: str) -> str:
    return str(value or "").lower().replace("\\", "/")


def _query_tokens(goal: str) -> list[str]:
    result = []

    for token in significant_tokens(goal):
        token = re.sub(
            r"[^a-z0-9_.-]+",
            "",
            str(token or "").lower(),
        )

        if (
            not token
            or token in GENERIC_WORDS
            or len(token) < 3
        ):
            continue

        if token not in result:
            result.append(token)

    return result[:24]


def _safe_read(root: Path, relative_path: str) -> str:
    target = (root / relative_path).resolve()

    try:
        target.relative_to(root)
    except ValueError:
        return ""

    if not target.exists() or not target.is_file():
        return ""

    try:
        return target.read_text(
            encoding="utf-8",
            errors="ignore",
        )
    except OSError:
        return ""


def _document_text(node, content: str) -> str:
    return _normalize(
        " ".join(
            [
                node.path or "",
                node.name or "",
                node.module or "",
                node.package or "",
                content,
            ]
        )
    )


def _term_count(text: str, token: str) -> int:
    """
    Count both literal appearances and identifier-style appearances.
    Literal counting intentionally recognizes names such as next_run_at.
    """
    literal = text.count(token)

    if "_" in token or "." in token or "/" in token or "-" in token:
        return literal

    identifier_hits = 0

    for word in TOKEN_RE.findall(text):
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


def discover_candidate_paths(
    repository: str,
    goal: str,
    *,
    max_candidates: int = 8,
):
    graph = get_repository_graph(repository)

    if graph is None:
        raise RuntimeError(
            f"Repository graph does not exist: {repository}"
        )

    tokens = _query_tokens(goal)

    if not tokens:
        return []

    root = Path(graph.root_path).resolve()

    # One module-level entry per path.
    documents = {}

    for node in graph.nodes:
        if node.node_type not in {NODE_FILE, NODE_TEST}:
            continue

        if not node.path:
            continue

        existing = documents.get(node.path)

        # Prefer module source node over duplicate test/function-style nodes.
        if existing is not None:
            if (
                existing["node"].node_type == NODE_FILE
                and node.node_type != NODE_FILE
            ):
                continue

        content = _safe_read(
            root,
            node.path,
        )

        documents[node.path] = {
            "node": node,
            "content": content,
            "text": _document_text(
                node,
                content,
            ),
        }

    if not documents:
        return []

    # ------------------------------------------------------------------
    # Corpus document frequency / IDF
    # ------------------------------------------------------------------

    document_frequency = Counter()

    for token in tokens:
        for item in documents.values():
            if _term_count(
                item["text"],
                token,
            ) > 0:
                document_frequency[token] += 1

    total_docs = len(documents)

    idf = {}

    for token in tokens:
        df = document_frequency.get(
            token,
            0,
        )

        # Standard smooth BM25-style IDF.
        idf[token] = math.log(
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

    scores = defaultdict(float)
    matched_terms = defaultdict(set)

    # ------------------------------------------------------------------
    # Score path/module and content separately.
    # ------------------------------------------------------------------

    for path, item in documents.items():
        node = item["node"]
        text = item["text"]

        path_text = _normalize(
            " ".join(
                [
                    node.path or "",
                    node.name or "",
                    node.module or "",
                    node.package or "",
                ]
            )
        )

        for token in tokens:
            term_idf = idf[token]

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

            matched_terms[path].add(
                token
            )

            # Path/module matches are strongest.
            if path_count:
                scores[path] += (
                    5.0
                    * term_idf
                    * min(
                        path_count,
                        3,
                    )
                )

            # Saturating content-frequency score.
            if content_count:
                tf = (
                    content_count
                    / (
                        content_count
                        + 2.0
                    )
                )

                scores[path] += (
                    7.0
                    * term_idf
                    * tf
                )

        distinct = len(
            matched_terms[path]
        )

        # Files connecting multiple request concepts are especially useful
        # for repository-level engineering.
        if distinct >= 2:
            scores[path] += (
                distinct
                * 2.5
            )

        if distinct >= 3:
            scores[path] += 6.0

        # Source code should lead candidate planning. Relevant tests are
        # still retained later through a separate quota.
        if node.node_type == NODE_FILE:
            scores[path] += 3.0

    # ------------------------------------------------------------------
    # Coherence boost around strongest relevant source packages.
    # ------------------------------------------------------------------

    source_rank = sorted(
        [
            (
                path,
                score,
            )
            for path, score
            in scores.items()
            if (
                documents[path]["node"].node_type
                == NODE_FILE
            )
        ],
        key=lambda pair:
            pair[1],
        reverse=True,
    )

    anchor_packages = {
        str(
            Path(path).parent
        ).replace(
            "\\",
            "/",
        )
        for path, score
        in source_rank[:3]
        if score > 0
    }

    for path in scores:
        parent = str(
            Path(path).parent
        ).replace(
            "\\",
            "/",
        )

        if parent in anchor_packages:
            scores[path] += 2.0

    # ------------------------------------------------------------------
    # Final selection:
    #   mostly implementation modules + up to two highly relevant tests.
    # ------------------------------------------------------------------

    ranked_sources = sorted(
        [
            path
            for path in scores
            if (
                documents[path]["node"].node_type
                == NODE_FILE
                and scores[path] > 0
            )
        ],
        key=lambda path:
            (
                scores[path],
                len(
                    matched_terms[path]
                ),
                path,
            ),
        reverse=True,
    )

    ranked_tests = sorted(
        [
            path
            for path in scores
            if (
                documents[path]["node"].node_type
                == NODE_TEST
                and scores[path] > 0
            )
        ],
        key=lambda path:
            (
                scores[path],
                len(
                    matched_terms[path]
                ),
                path,
            ),
        reverse=True,
    )

    limit = max(
        1,
        int(
            max_candidates
            or 1
        ),
    )

    test_quota = min(
        2,
        max(
            0,
            limit // 4,
        ),
    )

    source_quota = max(
        1,
        limit
        - test_quota,
    )

    selected = ranked_sources[
        :source_quota
    ]

    selected.extend(
        ranked_tests[
            :test_quota
        ]
    )

    # Fill remaining slots from whichever relevant entries are left.
    if len(selected) < limit:
        remaining = [
            path
            for path in (
                ranked_sources[
                    source_quota:
                ]
                + ranked_tests[
                    test_quota:
                ]
            )
            if path not in selected
        ]

        selected.extend(
            remaining[
                :(
                    limit
                    - len(
                        selected
                    )
                )
            ]
        )

    return selected[
        :limit
    ]
