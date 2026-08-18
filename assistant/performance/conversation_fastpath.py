from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class FastConversationResult:
    handled: bool
    response: str = ""
    reason: str = ""


def _normalize(
    text: str,
):
    value = str(
        text
        or ""
    ).strip().lower()

    value = re.sub(
        r"[^\w\s']",
        " ",
        value,
    )

    value = re.sub(
        r"\s+",
        " ",
        value,
    ).strip()

    for prefix in (
        "evie ",
        "eve ",
        "ev ",
    ):
        if value.startswith(
            prefix
        ):
            value = value[
                len(
                    prefix
                ):
            ].strip()

    return value


_EXACT_RESPONSES = {
    "thank you":
        "You're welcome, Max.",

    "thanks":
        "You're welcome, Max.",

    "good morning":
        "Good morning, Max.",

    "good afternoon":
        "Good afternoon, Max.",

    "good evening":
        "Good evening, Max.",

    "hello":
        "Hey, Max.",

    "hi":
        "Hey, Max.",

    "hey":
        "Hey, Max.",
}


def handle_fast_conversation(
    user_text: str,
):
    response = _EXACT_RESPONSES.get(
        _normalize(
            user_text
        )
    )

    if response is None:
        return FastConversationResult(
            handled=
                False,
        )

    return FastConversationResult(
        handled=
            True,

        response=
            response,

        reason=
            "deterministic_social_turn",
    )
