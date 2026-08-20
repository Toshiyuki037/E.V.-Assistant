"""
E.V.I.E. Phase 16F — Conservative Voice Model Router

Purpose:
    Route safe, low-risk, ordinary voice conversation and stable general
    knowledge to the existing low-latency reasoning path.

This preserves the existing architecture. Full authoritative reasoning remains
mandatory for personal/contextual memory, project/code/workspace requests,
vision, live/current data, tools/integrations, diagnostics/debugging,
financial/account requests, and explicit detailed requests.
"""

from __future__ import annotations

import re


_FAST_PREFIXES = (
    "what is ",
    "what are ",
    "what's ",
    "whats ",
    "what's the difference between ",
    "what is the difference between ",
    "how does ",
    "how do ",
    "why does ",
    "why do ",
    "define ",
    "explain ",
    "how are you",
    "how're you",
    "howre you",
    "how is it going",
    "how's it going",
    "hows it going",
    "how are things",
    "are you ready",
    "are you there",
    "good morning",
    "good afternoon",
    "good evening",
    "hello",
    "hi ",
    "hey ",
)

_FAST_EXACT = {
    "hi",
    "hello",
    "hey",
    "good morning",
    "good afternoon",
    "good evening",
    "how are you",
    "how are you doing",
    "how's it going",
    "hows it going",
    "how are things",
    "are you ready",
    "are you there",
    "thank you",
    "thanks",
}

_BLOCK_PHRASES = (
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
    "screen",
    "screenshot",
    "image",
    "photo",
    "camera",
    "see on",
    "look at",
    "visible",
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
    "latency",
    "in detail",
    "deep dive",
    "deep-dive",
    "exhaustive",
    "step by step",
    "step-by-step",
    "full explanation",
    "everything about",
)


def _normalize(text: str):
    return re.sub(
        r"\s+",
        " ",
        str(text or "").strip().lower(),
    ).strip()


def _contains_block_phrase(text: str):
    padded = " " + text + " "

    for phrase in _BLOCK_PHRASES:
        if phrase.startswith(" ") or phrase.endswith(" "):
            if phrase in padded:
                return True
        elif phrase in text:
            return True

    return False


def should_use_fast_voice_reasoning(
    user_text: str,
    cost_profile,
):
    """
    Return True only when the request is a safe fit for E.V.I.E.'s existing
    low-latency reasoning model.

    This does not bypass any Phase 1-15 routing. main.py already calls this
    after workflows, tools, system commands, agents, computer control, memory,
    and other existing routing layers have declined ownership.
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

    if not text:
        return False

    if len(text) > 320:
        return False

    if _contains_block_phrase(
        text
    ):
        return False

    if text.rstrip(" .!?") in _FAST_EXACT:
        return True

    return any(
        text.startswith(prefix)
        for prefix in _FAST_PREFIXES
    )
