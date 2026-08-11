"""
E.V.I.E. - Self-Engineering Request Planner

Phase 12N

Purpose:
Detect explicit repository/self-engineering requests without hijacking
ordinary conversation.

This is deliberately conservative. Merely mentioning a bug or file does
not trigger repository modification. The user must clearly ask E.V.I.E.
to inspect/diagnose/fix/implement/refactor/test its code or repository.
"""

from __future__ import annotations

import re

from .request_models import CodingRequest


ENGINEERING_VERBS = {
    "fix",
    "repair",
    "debug",
    "diagnose",
    "implement",
    "change",
    "modify",
    "refactor",
    "update",
    "improve",
    "test",
    "investigate",
}

REPOSITORY_TERMS = {
    "repository",
    "repo",
    "codebase",
    "source",
    "source code",
    "your code",
    "yourself",
    "evie",
    "e.v.i.e.",
    "assistant",
}

PLAN_TERMS = {
    "plan",
    "analyze",
    "analyse",
    "inspect",
    "diagnose",
    "investigate",
}

COMMIT_APPROVAL_PATTERNS = (
    r"\bapprove (?:the )?commit\b",
    r"\bcommit (?:it|the change|the changes)\b",
    r"\byes[, ]+commit\b",
)

REJECT_COMMIT_PATTERNS = (
    r"\breject (?:the )?commit\b",
    r"\bdon'?t commit\b",
    r"\bdo not commit\b",
    r"\bdiscard (?:the )?change",
)

STATUS_PATTERNS = (
    r"\bengineering status\b",
    r"\bcoding status\b",
    r"\bwhat(?:'s| is) the (?:engineering|coding) status\b",
)


def _normalized(
    text: str,
):
    return (
        str(text or "")
        .strip()
        .lower()
    )


def _contains_any(
    text: str,
    values,
):
    return any(
        value in text
        for value in values
    )


def plan_coding_request(
    user_message: str,
):
    text = _normalized(
        user_message
    )

    if not text:
        return CodingRequest(
            handled=False
        )

    for pattern in COMMIT_APPROVAL_PATTERNS:
        if re.search(
            pattern,
            text,
        ):
            return CodingRequest(
                handled=True,
                action="approve_commit",
                confidence=100,
                summary="Approve the pending self-engineering commit.",
            )

    for pattern in REJECT_COMMIT_PATTERNS:
        if re.search(
            pattern,
            text,
        ):
            return CodingRequest(
                handled=True,
                action="reject_commit",
                confidence=100,
                summary="Reject the pending self-engineering commit.",
            )

    for pattern in STATUS_PATTERNS:
        if re.search(
            pattern,
            text,
        ):
            return CodingRequest(
                handled=True,
                action="status",
                confidence=100,
                summary="Show self-engineering state.",
            )

    has_engineering_verb = _contains_any(
        text,
        ENGINEERING_VERBS,
    )

    has_repository_term = _contains_any(
        text,
        REPOSITORY_TERMS,
    )

    # Strong explicit forms such as:
    # "Fix your protocol time display."
    # "Diagnose the bug in your own code."
    explicit_self_reference = any(
        phrase in text
        for phrase in (
            "fix your",
            "repair your",
            "debug your",
            "diagnose your",
            "improve your",
            "change your",
            "modify your",
            "refactor your",
            "your own code",
            "your repository",
            "your codebase",
        )
    )

    if (
        has_engineering_verb
        and (
            has_repository_term
            or explicit_self_reference
        )
    ):
        return CodingRequest(
            handled=True,
            action="plan_change",
            goal=user_message.strip(),
            confidence=100 if explicit_self_reference else 92,
            summary="Plan a bounded repository-level engineering change.",
        )

    return CodingRequest(
        handled=False
    )
