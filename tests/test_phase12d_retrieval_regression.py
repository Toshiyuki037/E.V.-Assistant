"""
Phase 12D retrieval regression tests.
"""

from assistant.workspace.query_expansion import (
    expand_query,
    significant_tokens,
    text_matches_query,
)


def test_expands_phase_reference():
    values = expand_query(
        "What changed in E.V.I.E. around Phase 11?"
    )

    lowered = [
        value.lower()
        for value in values
    ]

    assert "phase 11" in lowered


def test_significant_tokens_remove_question_words():
    tokens = significant_tokens(
        "What changed in E.V.I.E. around Phase 11?"
    )

    assert "what" not in tokens
    assert "phase" in tokens
    assert "11" in tokens


def test_token_match_does_not_require_verbatim_question():
    assert text_matches_query(
        "Complete Phase 11 autonomous workflows and protocols",
        "What changed in E.V.I.E. around Phase 11?",
    )
