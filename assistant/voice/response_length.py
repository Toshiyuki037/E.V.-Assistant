"""
E.V.I.E. - Voice Response Length Discipline

Final Phase 14/15 polish.

Purpose:
    Keep voice answers concise by default without losing information that
    changes the user's decision, action, safety, approval, diagnosis, or result.

Important:
    This policy changes GENERATION behavior, not merely TTS truncation.
    The model is asked to produce the right amount of information up front.

Modes:
    concise
        Normal voice conversation. Fast and complete.

    important
        Errors, diagnostics, health, security, approvals, failures, or other
        information where omission could materially mislead the user.

    detailed
        The user explicitly requests a deep/full/exhaustive explanation.

"Exactly" by itself is NOT treated as a request for an exhaustive answer.
"""

from __future__ import annotations

from dataclasses import (
    dataclass,
)

import re


@dataclass(
    frozen=True
)
class ResponseLengthPolicy:
    mode: str
    target_words: int
    maximum_words: int
    instruction: str


# ---------------------------------------------------------------------------
# Intent Signals
# ---------------------------------------------------------------------------

_DETAILED_PHRASES = (
    "in detail",
    "in-depth",
    "in depth",
    "deep dive",
    "deep-dive",
    "extreme detail",
    "exhaustive",
    "exhaustively",
    "full explanation",
    "fully explain",
    "explain everything",
    "tell me everything",
    "all the details",
    "every detail",
    "step by step",
    "step-by-step",
    "walk me through everything",
    "comprehensive explanation",
)

_IMPORTANT_PHRASES = (
    "error",
    "fail",
    "failed",
    "failure",
    "broken",
    "diagnostic",
    "health",
    "healthy",
    "degraded",
    "unavailable",
    "warning",
    "security",
    "permission",
    "approval",
    "approve",
    "authentication",
    "credential",
    "dangerous",
    "risk",
    "portfolio",
    "financial",
    "transaction",
    "order",
    "delete",
    "remove",
    "overwrite",
    "commit",
    "push",
    "fix",
    "repair",
)


def _normalize(
    text: str,
):
    return (
        " ".join(
            str(
                text
                or ""
            )
            .strip()
            .lower()
            .split()
        )
    )


def explicitly_requests_detail(
    user_text: str,
):
    text = (
        _normalize(
            user_text
        )
    )

    return any(
        phrase in text
        for phrase
        in _DETAILED_PHRASES
    )


def contains_important_information_signal(
    user_text: str,
):
    text = (
        _normalize(
            user_text
        )
    )

    return any(
        phrase in text
        for phrase
        in _IMPORTANT_PHRASES
    )


# ---------------------------------------------------------------------------
# Policy Selection
# ---------------------------------------------------------------------------

def choose_response_length_policy(
    user_text: str,
    *,
    voice_mode: bool,
):
    """
    Select the amount of response detail BEFORE reasoning begins.
    """

    if not voice_mode:

        return ResponseLengthPolicy(
            mode=
                "standard",

            target_words=
                250,

            maximum_words=
                700,

            instruction=(
                "Use a proportionate response length. "
                "Be concise when the question is simple and expand only "
                "when the task genuinely requires detail."
            ),
        )


    if explicitly_requests_detail(
        user_text
    ):

        return ResponseLengthPolicy(
            mode=
                "detailed",

            target_words=
                300,

            maximum_words=
                500,

            instruction=(
                "The user explicitly requested detail. Give a thorough answer, "
                "but remain organized and avoid repetitive restatement. Preserve "
                "all facts necessary to understand the subject. Prefer roughly "
                "300 words and normally stay under 500 words unless correctness "
                "absolutely requires more."
            ),
        )


    if contains_important_information_signal(
        user_text
    ):

        return ResponseLengthPolicy(
            mode=
                "important",

            target_words=
                120,

            maximum_words=
                190,

            instruction=(
                "This request may contain operationally important information. "
                "Answer concisely, normally around 120 words and under 190 words, "
                "but NEVER omit a real error, failed component, degraded state, "
                "security/safety warning, approval requirement, exact requested "
                "result, important numeric value, or the user's next required "
                "action. Summarize healthy/background details instead of listing "
                "every low-priority item."
            ),
        )


    return ResponseLengthPolicy(
        mode=
            "concise",

        target_words=
            80,

        maximum_words=
            130,

        instruction=(
            "This is a normal voice interaction. Give the complete useful answer "
            "in conversational form, preferably about 60-100 words and normally "
            "under 130 words. Lead with the answer. Include only the most relevant "
            "supporting details. Do not enumerate every piece of available context, "
            "repeat the question, or give an exhaustive architecture dump unless "
            "the user explicitly asks for a detailed/deep/full explanation. "
            "Do not omit information that materially changes the answer or the "
            "user's next action. Offer to expand if additional detail would help."
        ),
    )


# ---------------------------------------------------------------------------
# Reasoning Prompt
# ---------------------------------------------------------------------------

def apply_response_length_policy(
    user_text: str,
    *,
    voice_mode: bool,
):
    """
    Return a reasoning-only prompt.

    The original user_text should still be used for:
        - routing
        - tools
        - memory
        - conversation persistence
        - display

    Only the final conversational reasoning call should receive this augmented
    prompt.
    """

    original = (
        str(
            user_text
            or ""
        )
        .strip()
    )

    if not original:

        return original


    policy = (
        choose_response_length_policy(
            original,
            voice_mode=
                voice_mode,
        )
    )


    return (
        original
        + "\n\n"
        + "[E.V.I.E. RESPONSE-LENGTH POLICY — INTERNAL RUNTIME INSTRUCTION]\n"
        + policy.instruction
        + "\n"
        + (
            "Important: preserve critical facts over brevity. "
            "Do not mention this response-length policy to the user."
        )
    )
