"""
E.V.I.E. - Engineering Documentation Note

Phase 12M

Produces a deterministic change note from a completed transaction.
Writing that note into Notion remains an integration action and therefore
continues through the existing permission/approval system.
"""

from __future__ import annotations

from .state import load_transaction


def build_engineering_documentation_note(
    transaction_id: str,
):
    transaction = load_transaction(
        transaction_id
    )

    if transaction is None:
        raise ValueError(
            f"Coding transaction does not exist: {transaction_id}"
        )

    plan = transaction.metadata.get(
        "engineering_plan",
        {}
    )

    lines = [
        f"Engineering transaction: {transaction.transaction_id}",
        f"Goal: {transaction.goal}",
        f"Status: {transaction.status}",
        f"Branch: {transaction.working_branch}",
        f"Baseline commit: {transaction.baseline_commit}",
    ]

    commit_sha = transaction.metadata.get(
        "commit_sha",
        "",
    )

    if commit_sha:
        lines.append(
            f"Commit: {commit_sha}"
        )

    if transaction.changed_paths:
        lines.append(
            "Changed files:"
        )

        for path in transaction.changed_paths:
            lines.append(
                f"- {path}"
            )

    lines.extend(
        [
            (
                "Targeted validation passed: "
                f"{transaction.targeted_tests_passed}"
            ),
            (
                "Full regression passed: "
                f"{transaction.regression_passed}"
            ),
        ]
    )

    note = plan.get(
        "documentation_note",
        ""
    )

    if note:
        lines.append(
            "Engineering note:"
        )
        lines.append(
            note
        )

    return "\n".join(
        lines
    )
