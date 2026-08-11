"""
E.V.I.E. - Workspace Query Expansion

Phase 12D Retrieval Fix

Purpose:
Turn natural-language workspace questions into compact retrieval terms
that different sources can match reliably.

Example:
    "What changed in E.V.I.E. around Phase 11?"
becomes roughly:
    ["what changed in e.v.i.e. around phase 11",
     "phase 11",
     "e.v.i.e.",
     "changed",
     "phase",
     "11"]
"""

from __future__ import annotations

import re


STOPWORDS = {
    "a", "an", "and", "are", "around", "as", "at", "be", "by",
    "did", "do", "does", "for", "from", "how", "i", "in", "is",
    "it", "me", "my", "of", "on", "or", "the", "this", "to",
    "was", "were", "what", "when", "where", "which", "who", "why",
    "with", "you", "your",
}


def significant_tokens(
    query: str,
):
    tokens = re.findall(
        r"[A-Za-z0-9_.-]+",
        str(query or ""),
    )

    results = []

    for token in tokens:
        lowered = token.lower()

        if lowered in STOPWORDS:
            continue

        if len(lowered) <= 1 and not lowered.isdigit():
            continue

        if lowered not in results:
            results.append(lowered)

    return results


def expand_query(
    query: str,
):
    original = (
        str(query or "")
        .strip()
    )

    variants = []

    if original:
        variants.append(
            original
        )

    # Preserve useful explicit phase references.
    for match in re.findall(
        r"\bphase\s+\d+\b",
        original,
        flags=re.IGNORECASE,
    ):
        if match.lower() not in {
            value.lower()
            for value in variants
        }:
            variants.append(
                match
            )

    # Preserve dotted/acronym-like project names.
    for match in re.findall(
        r"\b(?:[A-Za-z]\.){2,}[A-Za-z]?\.?\b",
        original,
    ):
        if match.lower() not in {
            value.lower()
            for value in variants
        }:
            variants.append(
                match
            )

    for token in significant_tokens(
        original
    ):
        if token not in {
            value.lower()
            for value in variants
        }:
            variants.append(
                token
            )

    return variants


def text_matches_query(
    text: str,
    query: str,
    *,
    minimum_overlap: int = 1,
):
    haystack = (
        str(text or "")
        .lower()
    )

    if not query:
        return True

    if query.lower() in haystack:
        return True

    tokens = significant_tokens(
        query
    )

    overlap = sum(
        1
        for token in tokens
        if token in haystack
    )

    return overlap >= max(
        1,
        minimum_overlap,
    )
