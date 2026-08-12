from __future__ import annotations

import re

from .request_models import CodingRequest


# ---------------------------------------------------------------------------
# Explicit Self-Engineering Language
# ---------------------------------------------------------------------------

SELF_ENGINEERING_ACTIONS = {
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
    "prepare",
}


# These are intentionally STRONG repository anchors.
#
# Generic words such as:
#
#     evie
#     e.v.i.e.
#     assistant
#
# are NOT sufficient.
#
# E.V.I.E. may appear in filenames, document contents, titles,
# application names, notes, etc. That must never automatically mean
# "modify your own repository."
#
REPOSITORY_ANCHORS = {
    "repository",
    "repo",
    "codebase",
    "source code",
    "your code",
    "your repository",
    "your repo",
    "your codebase",
    "your implementation",
    "your own code",
    "your own repository",
    "your own repo",
    "your own codebase",
    "e.v.i.e. repository",
    "evie repository",
    "e.v.-assistant repository",
    "assistant/main.py",
    "assistant/",
    "self-engineering",
}


# ---------------------------------------------------------------------------
# Pending Transaction Commands
# ---------------------------------------------------------------------------

RECOVERY_PHRASES = {
    "continue the pending self-engineering transaction",
    "continue pending self-engineering transaction",
    "resume the pending self-engineering transaction",
    "resume pending self-engineering transaction",
    "continue the self-engineering transaction",
    "resume the self-engineering transaction",
    "continue self-engineering",
    "resume self-engineering",
    "rerun its targeted validation",
    "rerun targeted validation",
    "retry self-engineering validation",
    "recover the coding transaction",
    "recover coding transaction",
}


COMMIT_APPROVAL_PHRASES = {
    "approve commit",
    "approve the commit",
    "commit it",
    "commit the change",
    "commit the changes",
    "yes commit",
}


COMMIT_REJECTION_PHRASES = {
    "reject commit",
    "reject the commit",
    "don't commit",
    "do not commit",
    "discard the change",
    "discard the changes",
}


STATUS_PHRASES = {
    "engineering status",
    "coding status",
    "self-engineering status",
}


# ---------------------------------------------------------------------------
# Normalization
# ---------------------------------------------------------------------------

def _normalized(
    text: str,
):
    return (
        str(
            text
            or ""
        )
        .strip()
        .lower()
    )


# ---------------------------------------------------------------------------
# Exact Phrase Matching
# ---------------------------------------------------------------------------

def _contains_phrase(
    text: str,
    phrase: str,
):
    return (
        phrase
        in text
    )


def _contains_any_phrase(
    text: str,
    phrases,
):
    return any(
        _contains_phrase(
            text,
            phrase,
        )
        for phrase
        in phrases
    )


# ---------------------------------------------------------------------------
# Whole-Word Matching
# ---------------------------------------------------------------------------

def _contains_word(
    text: str,
    word: str,
):
    """
    Match a standalone lexical word.

    Prevents:

        "test"
            from matching
        "EVIE-Phase13-Test.txt"

    unless 'test' is actually present as a normal word in the user's
    instruction.

    This also avoids accidental substring routing such as:

        "repair" inside another token
        "change" inside a filename
    """

    pattern = (
        r"(?<![A-Za-z0-9_])"
        + re.escape(
            word
        )
        + r"(?![A-Za-z0-9_])"
    )

    return (
        re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        )
        is not None
    )


def _contains_any_word(
    text: str,
    words,
):
    return any(
        _contains_word(
            text,
            word,
        )
        for word
        in words
    )


# ---------------------------------------------------------------------------
# Explicit Self Reference
# ---------------------------------------------------------------------------

def _has_explicit_self_engineering_reference(
    text: str,
):
    """
    Strong signals that the user is talking about E.V.I.E.'s own
    implementation rather than asking E.V.I.E. to operate the computer.
    """

    explicit_phrases = (
        "fix your code",
        "fix your repository",
        "fix your repo",
        "fix your implementation",

        "repair your code",
        "repair your repository",

        "debug your code",
        "debug your repository",
        "debug your implementation",

        "diagnose your code",
        "diagnose your repository",
        "diagnose your implementation",

        "improve your code",
        "improve your repository",
        "improve your implementation",

        "change your code",
        "change your repository",
        "change your implementation",

        "modify your code",
        "modify your repository",
        "modify your implementation",

        "refactor your code",
        "refactor your repository",

        "update your code",
        "update your repository",
        "update your implementation",

        "your own code",
        "your own repository",
        "your own repo",
        "your own codebase",

        "self-engineering",
    )

    return _contains_any_phrase(
        text,
        explicit_phrases,
    )


# ---------------------------------------------------------------------------
# Repository Context
# ---------------------------------------------------------------------------

def _has_repository_context(
    text: str,
):
    """
    Require an actual repository/code reference.

    E.V.I.E.'s name alone is intentionally NOT enough.
    """

    return _contains_any_phrase(
        text,
        REPOSITORY_ANCHORS,
    )


# ---------------------------------------------------------------------------
# Coding Request Planner
# ---------------------------------------------------------------------------

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


    # -----------------------------------------------------------------------
    # Pending Commit Approval
    # -----------------------------------------------------------------------

    if _contains_any_phrase(
        text,
        COMMIT_APPROVAL_PHRASES,
    ):
        return CodingRequest(
            handled=True,
            action="approve_commit",
            confidence=100,
            summary=(
                "Approve the pending "
                "self-engineering commit."
            ),
        )


    # -----------------------------------------------------------------------
    # Pending Commit Rejection
    # -----------------------------------------------------------------------

    if _contains_any_phrase(
        text,
        COMMIT_REJECTION_PHRASES,
    ):
        return CodingRequest(
            handled=True,
            action="reject_commit",
            confidence=100,
            summary=(
                "Reject the pending "
                "self-engineering commit."
            ),
        )


    # -----------------------------------------------------------------------
    # Transaction Recovery
    # -----------------------------------------------------------------------

    if _contains_any_phrase(
        text,
        RECOVERY_PHRASES,
    ):
        return CodingRequest(
            handled=True,
            action="resume_transaction",
            confidence=100,
            summary=(
                "Resume the latest recoverable "
                "self-engineering transaction."
            ),
        )


    # -----------------------------------------------------------------------
    # Transaction Status
    # -----------------------------------------------------------------------

    if _contains_any_phrase(
        text,
        STATUS_PHRASES,
    ):
        return CodingRequest(
            handled=True,
            action="status",
            confidence=100,
            summary=(
                "Show self-engineering state."
            ),
        )


    # -----------------------------------------------------------------------
    # Explicit Repository Engineering Request
    # -----------------------------------------------------------------------

    has_engineering_action = (
        _contains_any_word(
            text,
            SELF_ENGINEERING_ACTIONS,
        )
    )

    has_repository_context = (
        _has_repository_context(
            text
        )
    )

    explicit_self_reference = (
        _has_explicit_self_engineering_reference(
            text
        )
    )


    # -----------------------------------------------------------------------
    # Fail Closed
    # -----------------------------------------------------------------------
    #
    # Self-engineering owns the request ONLY if:
    #
    #     strong explicit self-reference
    #
    # OR
    #
    #     actual engineering action
    #         +
    #     actual repository/code context
    #
    # E.V.I.E.'s name in a filename/document is not repository context.
    #
    # A word such as "test" embedded in:
    #
    #     EVIE-Phase13-Test.txt
    #
    # is not an engineering instruction.
    # -----------------------------------------------------------------------

    should_self_engineer = (
        explicit_self_reference
        or (
            has_engineering_action
            and has_repository_context
        )
    )


    if should_self_engineer:
        return CodingRequest(
            handled=True,
            action="plan_change",
            goal=(
                user_message
                .strip()
            ),
            confidence=(
                100
                if explicit_self_reference
                else 95
            ),
            summary=(
                "Plan a bounded repository-level "
                "engineering change."
            ),
        )


    # -----------------------------------------------------------------------
    # Everything Else Falls Through
    # -----------------------------------------------------------------------
    #
    # Examples:
    #
    #   Open Notepad and save EVIE-Test.txt
    #       -> Phase 7 / Phase 13
    #
    #   Verify that EVIE-Test.txt exists
    #       -> Phase 7 / Phase 13
    #
    #   Write "E.V.I.E." in Notepad
    #       -> Phase 7 / Phase 13
    #
    #   Fix your repository's routing logic
    #       -> Phase 12
    #
    # -----------------------------------------------------------------------

    return CodingRequest(
        handled=False
    )