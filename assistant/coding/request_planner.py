from __future__ import annotations

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
    "prepare",
}

REPOSITORY_TERMS = {
    "repository",
    "repo",
    "codebase",
    "source",
    "source code",
    "your code",
    "yourself",
    "your own",
    "evie",
    "e.v.i.e.",
    "assistant",
}

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


def _normalized(text: str):
    return str(text or "").strip().lower()


def _contains_any(text: str, values):
    return any(value in text for value in values)


def plan_coding_request(user_message: str):
    text = _normalized(user_message)

    if not text:
        return CodingRequest(handled=False)

    if _contains_any(
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

    if _contains_any(
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

    if _contains_any(
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

    if _contains_any(
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

    has_engineering_verb = _contains_any(
        text,
        ENGINEERING_VERBS,
    )

    has_repository_term = _contains_any(
        text,
        REPOSITORY_TERMS,
    )

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
            "your own e.v.i.e. repository",
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
            confidence=(
                100
                if explicit_self_reference
                else 92
            ),
            summary=(
                "Plan a bounded repository-level "
                "engineering change."
            ),
        )

    return CodingRequest(handled=False)
