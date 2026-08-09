"""
E.V.I.E. - Tool Approval Session

Created: August 9, 2026
Last Edited: August 9, 2026
Author: Max Maehara

Purpose:
    Stores one exact pending tool action while E.V.I.E. waits for
    explicit approval.

Security:
    Approval executes the saved tool name and arguments.

    E.V.I.E. does not re-plan a different action after the user says
    yes.
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

    previous = get_pending_action()

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

APPROVE_PHRASES = {
    "y",
    "yes",
    "yeah",
    "yep",
    "approve",
    "approved",
    "proceed",
    "go ahead",
    "do it",
    "continue",
    "confirm",
}

REJECT_PHRASES = {
    "n",
    "no",
    "nope",
    "reject",
    "deny",
    "cancel",
    "stop",
    "don't",
    "dont",
    "never mind",
    "nevermind",
}


def classify_approval_response(
    user_message: str,
) -> str:
    """
    Returns:
        approve
        reject
        other
    """

    text = (
        user_message
        .strip()
        .lower()
        .rstrip(".!?")
    )

    if text in APPROVE_PHRASES:
        return "approve"

    if text in REJECT_PHRASES:
        return "reject"

    return "other"


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

    print(
        get_pending_action()
    )

    print(
        "yes ->",
        classify_approval_response(
            "yes"
        ),
    )

    print(
        "no ->",
        classify_approval_response(
            "no"
        ),
    )
