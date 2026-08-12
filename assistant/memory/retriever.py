"""
E.V.I.E. - Hybrid Memory Retriever

Created: August 8, 2026
Last Edited: August 8, 2026
Author: Max Maehara

Purpose:
    Retrieves memories relevant to the user's current request.

How It Works:
    Retrieval occurs in two stages:

    Stage 1:
        Fast local candidate retrieval using:
            - semantic similarity
            - keyword overlap
            - memory metadata

    Stage 2:
        A local CrossEncoder reranks the strongest candidates.

    This produces stronger relevance than semantic similarity alone.

Most Recent Change:
    Added local CrossEncoder reranking and multi-memory retrieval.
"""

import re

import numpy as np
from sentence_transformers import CrossEncoder

from .database import (
    get_active_memories,
    set_memory_embedding,
)

from .embeddings import (
    create_embedding,
    create_memory_embedding,
    embedding_from_json,
    semantic_similarity,
)


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

RERANKER_MODEL = (
    "cross-encoder/"
    "ms-marco-MiniLM-L-6-v2"
)

_reranker = None


def get_reranker():
    global _reranker

    if _reranker is None:
        print(
            "Loading E.V.I.E. memory reranker..."
        )

        _reranker = CrossEncoder(
            RERANKER_MODEL
        )

        print(
            "Memory reranker ready."
        )

    return _reranker

def warm_memory_retriever():
    """
    Explicitly initializes the semantic embedding model and
    CrossEncoder reranker.

    Intended for optional startup warmup so the first real
    memory-dependent conversation does not pay model-load latency.
    """

    print(
        "Warming E.V.I.E. memory retrieval..."
    )

    try:

        # Force the embedding model to initialize.
        create_embedding(
            "E.V.I.E. memory warmup"
        )

        # Force the CrossEncoder to initialize.
        get_reranker()

        print(
            "E.V.I.E. memory retrieval ready."
        )

        return True

    except Exception as error:

        print(
            "\n[Memory Warmup Warning]"
        )

        print(
            error
        )

        return False
        
# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SEMANTIC_WEIGHT = 0.25
LEXICAL_WEIGHT = 0.10
METADATA_WEIGHT = 0.05
RERANK_WEIGHT = 0.60

MIN_FINAL_SCORE = 0.08

CANDIDATE_LIMIT = 20


STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "about",
    "at",
    "be",
    "been",
    "but",
    "by",
    "can",
    "could",
    "did",
    "do",
    "does",
    "for",
    "from",
    "had",
    "has",
    "have",
    "how",
    "i",
    "in",
    "is",
    "it",
    "me",
    "my",
    "of",
    "on",
    "or",
    "our",
    "that",
    "the",
    "this",
    "to",
    "was",
    "were",
    "what",
    "when",
    "where",
    "which",
    "who",
    "why",
    "with",
    "you",
    "your",
}


# ---------------------------------------------------------------------------
# Keywords
# ---------------------------------------------------------------------------

def extract_keywords(
    text: str,
):
    words = re.findall(
        r"[A-Za-z0-9_.+-]+",
        text.lower(),
    )

    return {
        word
        for word in words
        if (
            word not in STOP_WORDS
            and len(word) > 2
        )
    }


def lexical_similarity(
    query: str,
    memory_text: str,
):
    query_words = extract_keywords(
        query
    )

    memory_words = extract_keywords(
        memory_text
    )

    if not query_words:
        return 0.0

    overlap = (
        query_words
        & memory_words
    )

    basic_score = (
        len(overlap)
        / len(query_words)
    )

    # Reward exact technical entities appearing in both.
    entity_bonus = 0.0

    for token in overlap:
        if (
            any(char.isdigit() for char in token)
            or token.isupper()
            or "." in token
            or "+" in token
        ):
            entity_bonus += 0.10

    return min(
        1.0,
        basic_score + entity_bonus,
    )


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def sigmoid(
    value: float,
):
    value = float(
        np.clip(
            value,
            -20,
            20,
        )
    )

    return (
        1.0
        / (
            1.0
            + np.exp(-value)
        )
    )


def ensure_embedding(
    memory,
):
    stored = embedding_from_json(
        memory.get("embedding")
    )

    if stored is not None:
        return stored

    embedding_json = create_memory_embedding(
        memory["content"]
    )

    set_memory_embedding(
        memory["id"],
        embedding_json,
    )

    return embedding_from_json(
        embedding_json
    )


# ---------------------------------------------------------------------------
# Hybrid Retrieval
# ---------------------------------------------------------------------------

def retrieve_memories(
    query: str,
    limit: int = 5,
    candidate_limit: int = CANDIDATE_LIMIT,
    exclude_ids: set[int] | None = None,
    use_reranker: bool = True,
):
    query = query.strip()

    if not query:
        return []

    exclude_ids = (
        exclude_ids
        if exclude_ids is not None
        else set()
    )

    memories = [
        memory
        for memory in get_active_memories()
        if memory["id"] not in exclude_ids
    ]

    if not memories:
        return []

    query_embedding = create_embedding(
        query
    )

    candidates = []

    for memory in memories:
        memory_embedding = ensure_embedding(
            memory
        )

        semantic_score = max(
            0.0,
            semantic_similarity(
                query_embedding,
                memory_embedding,
            ),
        )

        lexical_score = lexical_similarity(
            query,
            memory["content"],
        )

        metadata_score = (
            (
                memory["importance"]
                + memory["confidence"]
            )
            / 200.0
        )

        pre_score = (
            semantic_score * 0.70
            + lexical_score * 0.20
            + metadata_score * 0.10
        )

        item = dict(memory)

        item["_semantic_score"] = (
            semantic_score
        )

        item["_lexical_score"] = (
            lexical_score
        )

        item["_metadata_score"] = (
            metadata_score
        )

        item["_pre_score"] = (
            pre_score
        )

        candidates.append(
            item
        )

    candidates.sort(
        key=lambda item: (
            item["_pre_score"],
            item["importance"],
        ),
        reverse=True,
    )

    candidates = candidates[
        :candidate_limit
    ]

    # -----------------------------------------------------------------------
    # CrossEncoder Reranking
    # -----------------------------------------------------------------------

    if use_reranker and candidates:
        reranker = get_reranker()

        pairs = [
            [
                query,
                memory["content"],
            ]
            for memory in candidates
        ]

        raw_scores = reranker.predict(
            pairs,
            show_progress_bar=False,
        )

        raw_scores = np.asarray(
            raw_scores
        ).reshape(-1)

        for memory, raw_score in zip(
            candidates,
            raw_scores,
        ):
            rerank_score = sigmoid(
                raw_score
            )

            memory["_rerank_score"] = (
                rerank_score
            )

            memory["_final_score"] = (
                RERANK_WEIGHT
                * rerank_score

                + SEMANTIC_WEIGHT
                * memory[
                    "_semantic_score"
                ]

                + LEXICAL_WEIGHT
                * memory[
                    "_lexical_score"
                ]

                + METADATA_WEIGHT
                * memory[
                    "_metadata_score"
                ]
            )

    else:
        for memory in candidates:
            memory["_rerank_score"] = 0.0

            memory["_final_score"] = (
                memory["_pre_score"]
            )

    candidates.sort(
        key=lambda item: (
            item["_final_score"],
            item["importance"],
            item["confidence"],
        ),
        reverse=True,
    )

    useful = [
        memory
        for memory in candidates
        if memory["_final_score"] >= MIN_FINAL_SCORE
    ]

    # If ranking produced candidates but none crossed the threshold,
    # preserve the strongest candidate rather than returning nothing.
    if not useful and candidates:
        useful = [candidates[0]]

    return useful[:limit]


# ---------------------------------------------------------------------------
# One Best Target
# ---------------------------------------------------------------------------

def retrieve_target_memory(
    query: str,
    minimum_score: float = 0.18,
):
    results = retrieve_memories(
        query=query,
        limit=1,
    )

    if not results:
        return None

    best = results[0]

    if (
        best["_final_score"]
        < minimum_score
    ):
        return None

    return best


# ---------------------------------------------------------------------------
# Multiple Matching Targets
# ---------------------------------------------------------------------------

def retrieve_matching_memories(
    query: str,
    limit: int = 12,
):
    """
    Broad candidate retrieval for update/forget operations.

    Unlike normal conversational retrieval, this function intentionally
    does not discard lower-scoring candidates before the Memory Manager
    has a chance to inspect them.
    """

    query = query.strip()

    if not query:
        return []

    # Ask the main retriever for a larger pool.
    results = retrieve_memories(
        query=query,
        limit=limit,
    )

    if results:
        return results

    # Fallback:
    # If the normal threshold filtered everything out, rank all active
    # memories semantically and return the strongest candidates anyway.

    memories = get_active_memories()

    if not memories:
        return []

    query_embedding = create_embedding(
        query
    )

    candidates = []

    for memory in memories:

        memory_embedding = ensure_embedding(
            memory
        )

        semantic_score = max(
            0.0,
            semantic_similarity(
                query_embedding,
                memory_embedding,
            ),
        )

        lexical_score = lexical_similarity(
            query,
            memory["content"],
        )

        item = dict(
            memory
        )

        item["_semantic_score"] = semantic_score
        item["_lexical_score"] = lexical_score

        # Broad candidate score.
        item["_final_score"] = (
            semantic_score * 0.75
            + lexical_score * 0.25
        )

        candidates.append(
            item
        )

    candidates.sort(
        key=lambda item: (
            item["_final_score"],
            item["importance"],
            item["confidence"],
        ),
        reverse=True,
    )

    return candidates[:limit]


# ---------------------------------------------------------------------------
# Test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print(
        "E.V.I.E. Hybrid Memory Retriever"
    )

    print(
        "--------------------------------"
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

        results = retrieve_memories(
            query=query,
            limit=5,
        )

        print()

        if not results:
            print(
                "No relevant memories found."
            )

            continue

        for memory in results:
            print(
                f"ID: {memory['id']}"
            )

            print(
                f"Memory: "
                f"{memory['content']}"
            )

            print(
                "Semantic:",
                round(
                    memory[
                        "_semantic_score"
                    ],
                    3,
                ),
            )

            print(
                "Lexical:",
                round(
                    memory[
                        "_lexical_score"
                    ],
                    3,
                ),
            )

            print(
                "Reranker:",
                round(
                    memory[
                        "_rerank_score"
                    ],
                    3,
                ),
            )

            print(
                "Final:",
                round(
                    memory[
                        "_final_score"
                    ],
                    3,
                ),
            )

            print()