"""
E.V.I.E. - Workspace Evidence Ranking

Phase 12D

Simple deterministic V1 ranking.
Later this can be upgraded with local embeddings/reranking.
"""

from __future__ import annotations

import re


def _tokens(
    text: str,
):
    return {
        token
        for token
        in re.findall(
            r"[a-zA-Z0-9_.-]+",
            str(
                text
                or ""
            ).lower(),
        )
        if len(
            token
        ) > 1
    }


def rank_evidence(
    query: str,
    evidence,
):
    query_tokens = _tokens(
        query
    )

    ranked = []

    for item in evidence:
        haystack = " ".join(
            [
                item.title,
                item.content,
                item.path,
                item.repository,
                item.project,
                " ".join(
                    item.tags
                ),
            ]
        )

        item_tokens = _tokens(
            haystack
        )

        overlap = len(
            query_tokens
            & item_tokens
        )

        relevance = (
            float(
                item.relevance
                or 0.0
            )
            + overlap
        )

        item.relevance = relevance

        ranked.append(
            item
        )

    ranked.sort(
        key=lambda item: (
            item.relevance,
            item.confidence,
        ),
        reverse=True,
    )

    return ranked
