"""
E.V.I.E. - Knowledge Retriever

Created: August 8, 2026
Last Edited: August 8, 2026
Author: Max Maehara

Purpose:
    Searches indexed project source code and documents.

How It Works:
    Stage 1:
        Semantic similarity.

    Stage 2:
        Lexical + path + symbol matching.

    Stage 3:
        CrossEncoder reranking.

    Stage 4:
        Neighbor expansion around strong matches.

    This allows E.V.I.E. to retrieve the exact relevant code while
    also receiving enough surrounding implementation to understand
    execution flow across large functions.

Most Recent Change:
    Added neighboring-chunk context expansion, deduplication,
    and context-size control for final Phase 4 grounding.
"""

import re
from pathlib import Path

import numpy as np

from .database import (
    get_neighbor_chunks,
    get_workspace_chunks,
)

from .embeddings import (
    embedding_from_json,
    similarity,
)

from .indexer import (
    index_workspace,
)

from .scanner import (
    get_active_workspace_path,
)


from ..memory.embeddings import (
    create_embedding,
)

from ..memory.retriever import (
    get_reranker,
    sigmoid,
)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SEMANTIC_WEIGHT = 0.40
LEXICAL_WEIGHT = 0.15
PATH_WEIGHT = 0.15
RERANK_WEIGHT = 0.30


CANDIDATE_LIMIT = 30


# Number of direct semantic search results.
DEFAULT_RESULT_LIMIT = 6


# Neighbor expansion.
NEIGHBOR_BEFORE = 1
NEIGHBOR_AFTER = 1


# Final amount of source text allowed into brain context.
MAX_CONTEXT_CHARACTERS = 30_000


STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "can",
    "do",
    "does",
    "for",
    "from",
    "how",
    "i",
    "in",
    "is",
    "it",
    "my",
    "of",
    "on",
    "or",
    "the",
    "this",
    "to",
    "what",
    "where",
    "which",
    "with",
}


# ---------------------------------------------------------------------------
# Lexical Processing
# ---------------------------------------------------------------------------

def words(
    value: str,
):

    tokens = re.findall(
        r"[A-Za-z0-9_+.]+",
        value.lower(),
    )

    return {
        token
        for token in tokens

        if (
            token not in STOP_WORDS
            and len(token) > 1
        )
    }


def lexical_score(
    query: str,
    content: str,
):

    query_words = words(
        query
    )

    if not query_words:
        return 0.0

    content_words = words(
        content
    )

    overlap = (
        query_words
        & content_words
    )

    return (
        len(overlap)
        / len(query_words)
    )


def path_score(
    query: str,
    relative_path: str,
    symbol: str | None,
):

    query_words = words(
        query
    )

    if not query_words:
        return 0.0

    target = (
        relative_path
        + " "
        + (
            symbol
            or ""
        )
    )

    target_words = words(
        target
    )

    overlap = (
        query_words
        & target_words
    )

    return (
        len(overlap)
        / len(query_words)
    )


# ---------------------------------------------------------------------------
# First-Stage Retrieval
# ---------------------------------------------------------------------------

def retrieve_direct_knowledge(
    query: str,
    limit: int = DEFAULT_RESULT_LIMIT,
    workspace_path=None,
    ensure_index: bool = True,
):
    """
    Finds the strongest direct source-code/document chunks.
    """

    query = query.strip()

    if not query:
        return []

    # -----------------------------------------------------------------------
    # Workspace
    # -----------------------------------------------------------------------

    if workspace_path is None:

        workspace = (
            get_active_workspace_path()
        )

    else:

        workspace = Path(
            workspace_path
        ).resolve()

    if workspace is None:
        return []


    # -----------------------------------------------------------------------
    # Ensure Current Index
    # -----------------------------------------------------------------------

    if ensure_index:

        index_workspace(
            workspace
        )


    # -----------------------------------------------------------------------
    # Load Indexed Chunks
    # -----------------------------------------------------------------------

    chunks = get_workspace_chunks(
        str(workspace)
    )

    if not chunks:
        return []


    # -----------------------------------------------------------------------
    # Query Embedding
    # -----------------------------------------------------------------------

    query_embedding = (
        create_embedding(
            query
        )
    )


    candidates = []


    # -----------------------------------------------------------------------
    # Candidate Scoring
    # -----------------------------------------------------------------------

    for chunk in chunks:

        vector = embedding_from_json(
            chunk.get(
                "embedding"
            )
        )

        if vector is None:
            continue


        semantic = max(
            0.0,

            similarity(
                query_embedding,
                vector,
            ),
        )


        lexical = lexical_score(
            query,
            chunk[
                "content"
            ],
        )


        path = path_score(
            query,
            chunk[
                "relative_path"
            ],
            chunk.get(
                "symbol"
            ),
        )


        pre_score = (
            semantic * 0.65
            + lexical * 0.20
            + path * 0.15
        )


        item = dict(
            chunk
        )


        item[
            "_semantic_score"
        ] = semantic


        item[
            "_lexical_score"
        ] = lexical


        item[
            "_path_score"
        ] = path


        item[
            "_pre_score"
        ] = pre_score


        item[
            "_retrieval_type"
        ] = "direct"


        candidates.append(
            item
        )


    # -----------------------------------------------------------------------
    # Initial Ranking
    # -----------------------------------------------------------------------

    candidates.sort(
        key=lambda item:
            item[
                "_pre_score"
            ],
        reverse=True,
    )


    candidates = candidates[
        :CANDIDATE_LIMIT
    ]


    if not candidates:
        return []


    # -----------------------------------------------------------------------
    # CrossEncoder Reranking
    # -----------------------------------------------------------------------

    reranker = get_reranker()


    pairs = []


    for candidate in candidates:

        candidate_text = (
            f"File: "
            f"{candidate['relative_path']}\n"

            f"Symbol: "
            f"{candidate.get('symbol') or ''}\n"

            f"Lines: "
            f"{candidate['start_line']}-"
            f"{candidate['end_line']}\n\n"

            f"{candidate['content']}"
        )


        pairs.append(
            [
                query,
                candidate_text,
            ]
        )


    raw_scores = reranker.predict(
        pairs,
        show_progress_bar=False,
    )


    raw_scores = np.asarray(
        raw_scores
    ).reshape(-1)


    # -----------------------------------------------------------------------
    # Final Direct Score
    # -----------------------------------------------------------------------

    for candidate, raw in zip(
        candidates,
        raw_scores,
    ):

        rerank = sigmoid(
            raw
        )


        candidate[
            "_rerank_score"
        ] = rerank


        candidate[
            "_final_score"
        ] = (
            SEMANTIC_WEIGHT
            * candidate[
                "_semantic_score"
            ]

            + LEXICAL_WEIGHT
            * candidate[
                "_lexical_score"
            ]

            + PATH_WEIGHT
            * candidate[
                "_path_score"
            ]

            + RERANK_WEIGHT
            * rerank
        )


    candidates.sort(
        key=lambda item:
            item[
                "_final_score"
            ],
        reverse=True,
    )


    return candidates[
        :limit
    ]


# ---------------------------------------------------------------------------
# Neighbor Expansion
# ---------------------------------------------------------------------------

def expand_neighbors(
    direct_results,
    workspace_path: str,
    before: int = NEIGHBOR_BEFORE,
    after: int = NEIGHBOR_AFTER,
):
    """
    Expands each strong direct result with nearby chunks from
    the same file.

    Neighboring chunks are context only. They are not treated as
    independent semantic search hits.
    """

    expanded = []


    # Deduplicate using file + chunk index.
    seen = set()


    for direct in direct_results:

        relative_path = direct[
            "relative_path"
        ]

        chunk_index = direct[
            "chunk_index"
        ]


        neighbors = get_neighbor_chunks(
            workspace_path=workspace_path,
            relative_path=relative_path,
            chunk_index=chunk_index,
            before=before,
            after=after,
        )


        for neighbor in neighbors:

            key = (
                neighbor[
                    "relative_path"
                ],

                neighbor[
                    "chunk_index"
                ],
            )


            if key in seen:
                continue


            seen.add(
                key
            )


            # ---------------------------------------------------------------
            # Was this itself a direct result?
            # ---------------------------------------------------------------

            matching_direct = next(
                (
                    item

                    for item in direct_results

                    if (
                        item[
                            "relative_path"
                        ]
                        == neighbor[
                            "relative_path"
                        ]

                        and item[
                            "chunk_index"
                        ]
                        == neighbor[
                            "chunk_index"
                        ]
                    )
                ),
                None,
            )


            if matching_direct:

                item = dict(
                    matching_direct
                )

                item[
                    "_retrieval_type"
                ] = "direct"

            else:

                item = dict(
                    neighbor
                )

                item[
                    "_retrieval_type"
                ] = "neighbor"

                item[
                    "_semantic_score"
                ] = None

                item[
                    "_lexical_score"
                ] = None

                item[
                    "_path_score"
                ] = None

                item[
                    "_rerank_score"
                ] = None

                # Neighbor score inherits some relevance from
                # the result that caused its inclusion.
                item[
                    "_final_score"
                ] = (
                    direct[
                        "_final_score"
                    ]
                    * 0.75
                )


            expanded.append(
                item
            )


    # -----------------------------------------------------------------------
    # Keep source order within files
    # -----------------------------------------------------------------------

    expanded.sort(
        key=lambda item: (
            item[
                "relative_path"
            ],

            item[
                "chunk_index"
            ],
        )
    )


    return expanded


# ---------------------------------------------------------------------------
# Context Budget
# ---------------------------------------------------------------------------

def apply_context_budget(
    results,
    maximum_characters:
        int = MAX_CONTEXT_CHARACTERS,
):
    """
    Prevents project knowledge from growing without bound.

    Direct matches receive priority over neighbor-only context.
    """

    if not results:
        return []


    direct = [
        item
        for item in results

        if (
            item.get(
                "_retrieval_type"
            )
            == "direct"
        )
    ]


    neighbors = [
        item
        for item in results

        if (
            item.get(
                "_retrieval_type"
            )
            != "direct"
        )
    ]


    direct.sort(
        key=lambda item:
            item.get(
                "_final_score",
                0,
            ),
        reverse=True,
    )


    neighbors.sort(
        key=lambda item:
            item.get(
                "_final_score",
                0,
            ),
        reverse=True,
    )


    selected = []

    used = 0


    for item in (
        direct
        + neighbors
    ):

        size = len(
            item[
                "content"
            ]
        )


        if (
            used + size
            > maximum_characters
        ):

            continue


        selected.append(
            item
        )


        used += size


    # Restore logical source ordering.
    selected.sort(
        key=lambda item: (
            item[
                "relative_path"
            ],

            item[
                "chunk_index"
            ],
        )
    )


    return selected


# ---------------------------------------------------------------------------
# Complete Knowledge Retrieval
# ---------------------------------------------------------------------------

def retrieve_knowledge(
    query: str,
    limit: int = DEFAULT_RESULT_LIMIT,
    workspace_path=None,
    ensure_index: bool = True,
    expand_context: bool = True,
):
    """
    Main Phase 4 retrieval entry point.
    """

    if workspace_path is None:

        workspace = (
            get_active_workspace_path()
        )

    else:

        workspace = Path(
            workspace_path
        ).resolve()


    if workspace is None:
        return []


    direct_results = (
        retrieve_direct_knowledge(
            query=query,
            limit=limit,
            workspace_path=workspace,
            ensure_index=ensure_index,
        )
    )


    if not direct_results:
        return []


    if not expand_context:

        return direct_results


    expanded = expand_neighbors(
        direct_results=direct_results,
        workspace_path=str(
            workspace
        ),
    )


    return apply_context_budget(
        expanded
    )


# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------

def format_knowledge_results(
    results,
):

    blocks = []


    for result in results:

        symbol = (
            result.get(
                "symbol"
            )
            or "none"
        )


        retrieval_type = (
            result.get(
                "_retrieval_type"
            )
            or "unknown"
        )


        blocks.append(
            f"""
SOURCE TYPE:
{retrieval_type}

FILE:
{result['relative_path']}

SYMBOL:
{symbol}

CHUNK:
{result['chunk_index']}

LINES:
{result['start_line']}-{result['end_line']}

CONTENT:
{result['content']}
""".strip()
        )


    return (
        "\n\n---\n\n"
        .join(
            blocks
        )
    )


# ---------------------------------------------------------------------------
# Standalone Test
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    print(
        "E.V.I.E. Knowledge Retriever"
    )

    print(
        "-----------------------------"
    )


    while True:

        query = input(
            "Search: "
        ).strip()


        if query.lower() in {
            "quit",
            "exit",
        }:

            break


        results = retrieve_knowledge(
            query=query,
            limit=5,
            expand_context=True,
        )


        print()


        if not results:

            print(
                "No knowledge found."
            )

            continue


        for result in results:

            score = result.get(
                "_final_score"
            )


            if score is None:

                score_text = "context"

            else:

                score_text = (
                    f"{score:.3f}"
                )


            print(
                f"[{result.get('_retrieval_type')}] "
                f"{result['relative_path']} "
                f"| "
                f"{result.get('symbol') or '-'} "
                f"| chunk "
                f"{result['chunk_index']} "
                f"| lines "
                f"{result['start_line']}-"
                f"{result['end_line']} "
                f"| score "
                f"{score_text}"
            )