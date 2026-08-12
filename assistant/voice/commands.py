"""
E.V.I.E. - Contextual Live Voice Commands

Phase 14J

Purpose:
    Classifies short conversational control utterances separately from
    application/session commands and normal prompts.

Important:
    "Actually ..." is treated as a revision/new authoritative turn.
    "Go back" is handled by the voice session using safe conversational
    history semantics; it does not blindly re-execute an old action.
"""

from __future__ import annotations


STOP_COMMANDS = {
    "stop",
    "stop talking",
    "that's enough",
    "thats enough",
}

WAIT_COMMANDS = {
    "wait",
    "hold on",
    "one moment",
}

NEVER_MIND_COMMANDS = {
    "never mind",
    "nevermind",
    "forget it",
}

CONTINUE_COMMANDS = {
    "continue",
    "keep going",
    "go on",
}

GO_BACK_COMMANDS = {
    "go back",
    "back up",
}


def normalize_live_command(
    text: str,
) -> str:

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
        .rstrip(
            ".!?"
        )
    )


def classify_live_voice_command(
    text: str,
):

    normalized = (
        normalize_live_command(
            text
        )
    )


    if normalized in STOP_COMMANDS:

        return "stop"


    if normalized in WAIT_COMMANDS:

        return "wait"


    if normalized in NEVER_MIND_COMMANDS:

        return "never_mind"


    if normalized in CONTINUE_COMMANDS:

        return "continue"


    if normalized in GO_BACK_COMMANDS:

        return "go_back"


    if (
        normalized == "actually"
        or normalized.startswith(
            "actually "
        )
    ):

        return "revision"


    return None
