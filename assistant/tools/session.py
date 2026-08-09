"""
E.V.I.E. - Tool Approval Session

Created: August 9, 2026
Last Edited: August 9, 2026
Author: Max Maehara

Purpose:
    Stores one exact pending tool action while E.V.I.E. waits for
    explicit approval.

Security:
    Approval executes the exact saved tool name and arguments.

    E.V.I.E. does not re-plan the pending action after the user
    approves it.

Capabilities:
    - exact approval
    - exact rejection
    - compound approval:
        "Yes, then show me Git status."
    - compound rejection:
        "No, open Chrome instead."

Most Recent Change:
    Added approval-prefix parsing and follow-up request extraction.
"""

from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime
from typing import Any


# ---------------------------------------------------------------------------
# Pending Action
# ---------------------------------------------------------------------------

@dataclass
class PendingToolAction:
    tool_name: str
    arguments: dict[str, Any]
    risk: str
    summary: str
    original_request: str
    created_at: str


@dataclass
class ApprovalResponse:
    decision: str
    remainder: str


_PENDING_ACTION: PendingToolAction | None = None


# ---------------------------------------------------------------------------
# Pending State
# ---------------------------------------------------------------------------

def set_pending_action(
    tool_name: str,
    arguments: dict,
    risk: str,
    summary: str,
    original_request: str,
):
    global _PENDING_ACTION

    _PENDING_ACTION = PendingToolAction(
        tool_name=tool_name,
        arguments=deepcopy(
            arguments
        ),
        risk=risk,
        summary=summary,
        original_request=original_request,
        created_at=datetime.now().isoformat(
            timespec="seconds"
        ),
    )

    return get_pending_action()


def get_pending_action():

    if _PENDING_ACTION is None:
        return None

    return PendingToolAction(
        tool_name=_PENDING_ACTION.tool_name,
        arguments=deepcopy(
            _PENDING_ACTION.arguments
        ),
        risk=_PENDING_ACTION.risk,
        summary=_PENDING_ACTION.summary,
        original_request=_PENDING_ACTION.original_request,
        created_at=_PENDING_ACTION.created_at,
    )


def clear_pending_action():

    global _PENDING_ACTION

    previous = (
        get_pending_action()
    )

    _PENDING_ACTION = None

    return previous


def has_pending_action() -> bool:

    return (
        _PENDING_ACTION
        is not None
    )


# ---------------------------------------------------------------------------
# Approval Language
# ---------------------------------------------------------------------------

APPROVE_PHRASES = (
    "go ahead",
    "approved",
    "approve",
    "proceed",
    "continue",
    "confirm",
    "do it",
    "yeah",
    "yep",
    "yes",
    "y",
)


REJECT_PHRASES = (
    "never mind",
    "nevermind",
    "don't",
    "dont",
    "cancel",
    "reject",
    "deny",
    "stop",
    "nope",
    "no",
    "n",
)


# ---------------------------------------------------------------------------
# Normalize Remainder
# ---------------------------------------------------------------------------

def clean_follow_up(
    text: str,
):
    """
    Removes punctuation / connector words that commonly follow
    an approval phrase.
    """

    text = text.strip()

    text = text.lstrip(
        " ,.;:!?-"
    ).strip()

    lower = text.lower()

    connectors = (
        "and then ",
        "then ",
        "and ",
        "also ",
    )

    for connector in connectors:

        if lower.startswith(
            connector
        ):

            text = text[
                len(connector):
            ].strip()

            break

    return text


# ---------------------------------------------------------------------------
# Approval Parsing
# ---------------------------------------------------------------------------

def parse_approval_response(
    user_message: str,
):
    """
    Returns an ApprovalResponse containing:

        decision:
            approve
            reject
            other

        remainder:
            any additional user request following the decision.

    Examples:

        "yes"
            -> approve, ""

        "Yes, then show me Git status."
            -> approve, "show me Git status."

        "No, open Chrome instead."
            -> reject, "open Chrome instead."
    """

    original = (
        user_message.strip()
    )

    lower = (
        original.lower()
    )


    # -----------------------------------------------------------------------
    # Approval
    # -----------------------------------------------------------------------

    for phrase in APPROVE_PHRASES:

        if lower == phrase:

            return ApprovalResponse(
                decision="approve",
                remainder="",
            )

        if lower.startswith(
            phrase
        ):

            boundary = (
                len(phrase)
            )

            if (
                len(lower) > boundary
                and lower[boundary]
                not in " ,.;:!?-"
            ):

                continue

            remainder = (
                original[
                    boundary:
                ]
            )

            return ApprovalResponse(
                decision="approve",
                remainder=clean_follow_up(
                    remainder
                ),
            )


    # -----------------------------------------------------------------------
    # Rejection
    # -----------------------------------------------------------------------

    for phrase in REJECT_PHRASES:

        if lower == phrase:

            return ApprovalResponse(
                decision="reject",
                remainder="",
            )

        if lower.startswith(
            phrase
        ):

            boundary = (
                len(phrase)
            )

            if (
                len(lower) > boundary
                and lower[boundary]
                not in " ,.;:!?-"
            ):

                continue

            remainder = (
                original[
                    boundary:
                ]
            )

            return ApprovalResponse(
                decision="reject",
                remainder=clean_follow_up(
                    remainder
                ),
            )


    return ApprovalResponse(
        decision="other",
        remainder="",
    )


def classify_approval_response(
    user_message: str,
):
    """
    Compatibility helper for older callers.
    """

    return (
        parse_approval_response(
            user_message
        ).decision
    )


# ---------------------------------------------------------------------------
# Standalone Test
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    set_pending_action(
        tool_name="git_add",
        arguments={
            "paths": [
                "assistant/tools/git.py"
            ]
        },
        risk="medium",
        summary=(
            "Stage assistant/tools/git.py."
        ),
        original_request=(
            "Stage assistant/tools/git.py."
        ),
    )

    print(
        "E.V.I.E. Tool Approval Session"
    )

    print(
        "-------------------------------"
    )

    tests = (
        "yes",
        "Yes, then show me my Git status.",
        "go ahead and open Chrome",
        "no",
        "No, open Chrome instead.",
        "What's 2 + 2?",
    )

    for message in tests:

        result = (
            parse_approval_response(
                message
            )
        )

        print()

        print(
            "Input:",
            message,
        )

        print(
            "Decision:",
            result.decision,
        )

        print(
            "Remainder:",
            result.remainder,
        )