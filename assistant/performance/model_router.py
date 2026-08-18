"""
E.V.I.E. Phase 16F — Conservative Voice Model Router

This router is deliberately narrow.

It can accelerate ONLY stable, generic, text-only explanatory questions after
all existing Phase 1-15 routing has already declined ownership.

It never routes:
    - personal/contextual questions
    - project/code/workspace questions
    - vision/screen/image questions
    - current/live/time-sensitive questions
    - tools/integrations
    - diagnostics/errors/debugging
    - financial/account requests
    - explicit detailed/deep requests

Those continue through the existing authoritative reasoning path.
"""

from __future__ import annotations

import re


_FAST_PREFIXES = (
    "what is ",
    "what are ",
    "what's the difference between ",
    "what is the difference between ",
    "how does ",
    "how do ",
    "why does ",
    "why do ",
    "define ",
    "explain ",
)


_BLOCK_PHRASES = (
    # Personal/contextual
    " my ",
    " our ",
    " we ",
    " i ",
    " me ",
    " remember",
    " earlier",
    " last time",
    " previously",
    " before",
    " tell me more",
    " elaborate",
    " expand on",
    " what exactly",

    # Project/code/runtime
    "project",
    "workspace",
    "repository",
    "repo",
    "codebase",
    "file",
    "function",
    "class",
    "module",
    "implementation",
    "implemented",
    "source code",
    "github",
    "git ",
    ".py",
    ".js",
    ".ts",
    ".cpp",
    ".vhd",
    ".vhdl",
    "fpga",

    # Vision / perception
    "screen",
    "screenshot",
    "image",
    "photo",
    "camera",
    "see on",
    "look at",
    "visible",

    # Live / connected
    "weather",
    "calendar",
    "email",
    "gmail",
    "task",
    "spotify",
    "schwab",
    "portfolio",
    "stock",
    "market",
    "notion",
    "current",
    "currently",
    "today",
    "tomorrow",
    "yesterday",
    "latest",
    "recent",
    "right now",
    "news",
    "price",

    # High-value / diagnostic / engineering
    "error",
    "failed",
    "failure",
    "broken",
    "diagnostic",
    "debug",
    "fix ",
    "repair",
    "architecture",
    "security",
    "permission",
    "approval",
    "health",
    "healthy",

    # Explicit quality-first requests
    "in detail",
    "deep dive",
    "deep-dive",
    "exhaustive",
    "step by step",
    "step-by-step",
    "full explanation",
    "everything about",
)


def _normalize(
    text: str,
):
    value = (
        " "
        + re.sub(
            r"\s+",
            " ",
            str(
                text
                or ""
            )
            .strip()
            .lower(),
        )
        + " "
    )

    return value


def should_use_fast_voice_reasoning(
    user_text: str,
    cost_profile,
):
    """
    Return True only when the request is an excellent fit for a low-latency,
    no-reasoning conversational model.

    Phase 16B's cost profile must already classify the request as fast.
    """

    if str(
        getattr(
            cost_profile,
            "mode",
            "",
        )
        or ""
    ).lower() != "fast":

        return False


    if bool(
        getattr(
            cost_profile,
            "allow_long_term_memory",
            False,
        )
    ):

        return False


    if bool(
        getattr(
            cost_profile,
            "allow_project_knowledge",
            False,
        )
    ):

        return False


    text = _normalize(
        user_text
    )


    if len(
        text
    ) > 320:

        return False


    if any(
        phrase in text
        for phrase
        in _BLOCK_PHRASES
    ):

        return False


    stripped = (
        text.strip()
    )


    return any(
        stripped.startswith(
            prefix
        )
        for prefix
        in _FAST_PREFIXES
    )
