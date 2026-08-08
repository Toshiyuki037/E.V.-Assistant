"""
E.V.I.E. - Memory Consolidation Module

Created: August 8, 2026
Last Edited: August 8, 2026
Author: Max Maehara

Purpose:
    Performs maintenance on E.V.I.E.'s long-term memory.

How It Works:
    Finds semantically similar memories and asks the Memory Manager
    whether they are duplicates, superseded facts, contradictions,
    or merely related.

    Duplicate memories are consolidated conservatively.

Most Recent Change:
    Added LLM-assisted semantic consolidation instead of relying
    on cosine similarity alone.
"""

from .database import (
    archive_memory,
    get_active_memories,
)

from .manager import (
    resolve_new_memory,
)

from .retriever import (
    retrieve_memories,
)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

MIN_SEMANTIC_SIMILARITY = 0.72
MIN_RELATION_CONFIDENCE = 88

MAX_PAIRS_PER_RUN = 50


# ---------------------------------------------------------------------------
# Quality Score
# ---------------------------------------------------------------------------

def memory_quality(
    memory,
):
    return (
        memory["importance"]
        + memory["permanence"]
        + memory["confidence"]
    )


# ---------------------------------------------------------------------------
# Consolidation
# ---------------------------------------------------------------------------

def consolidate_memories():
    memories = get_active_memories()

    reviewed_pairs = set()

    actions = []

    pair_count = 0

    for memory in memories:
        if pair_count >= MAX_PAIRS_PER_RUN:
            break

        candidates = retrieve_memories(
            query=memory["content"],
            limit=6,
            exclude_ids={
                memory["id"]
            },
            use_reranker=False,
        )

        for candidate in candidates:
            if pair_count >= MAX_PAIRS_PER_RUN:
                break

            pair = tuple(
                sorted(
                    (
                        memory["id"],
                        candidate["id"],
                    )
                )
            )

            if pair in reviewed_pairs:
                continue

            reviewed_pairs.add(pair)

            if (
                candidate[
                    "_semantic_score"
                ]
                < MIN_SEMANTIC_SIMILARITY
            ):
                continue

            pair_count += 1

            resolution = (
                resolve_new_memory(
                    memory["content"],
                    [candidate],
                )
            )

            if (
                resolution.confidence
                < MIN_RELATION_CONFIDENCE
            ):
                continue

            # ---------------------------------------------------------------
            # Duplicate
            # ---------------------------------------------------------------

            if (
                resolution.relation
                == "duplicate"
            ):
                if (
                    memory_quality(memory)
                    >= memory_quality(candidate)
                ):
                    keep = memory
                    archive = candidate
                else:
                    keep = candidate
                    archive = memory

                archive_memory(
                    memory_id=archive["id"],
                    superseded_by=keep["id"],
                    reason="duplicate",
                )

                actions.append(
                    {
                        "action": "duplicate",
                        "kept": keep["id"],
                        "archived": archive["id"],
                    }
                )

                continue

            # ---------------------------------------------------------------
            # Superseded / Contradictory
            # ---------------------------------------------------------------

            if resolution.relation in {
                "supersedes",
                "contradicts",
            }:
                # Conservative rule:
                # newer database entry wins only when the resolver is
                # highly confident these describe the same subject.

                if memory["id"] > candidate["id"]:
                    newer = memory
                    older = candidate
                else:
                    newer = candidate
                    older = memory

                archive_memory(
                    memory_id=older["id"],
                    superseded_by=newer["id"],
                    reason=resolution.relation,
                )

                actions.append(
                    {
                        "action":
                            resolution.relation,

                        "kept":
                            newer["id"],

                        "archived":
                            older["id"],
                    }
                )

    return actions


# ---------------------------------------------------------------------------
# Test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print(
        "Running E.V.I.E. memory consolidation..."
    )

    actions = consolidate_memories()

    if not actions:
        print(
            "No consolidation required."
        )

    else:
        print(
            "\nConsolidation actions:"
        )

        for action in actions:
            print(action)