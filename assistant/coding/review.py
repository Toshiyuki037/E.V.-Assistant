"""
E.V.I.E. - Coding Transaction Review

Phase 12I
"""

from __future__ import annotations

from .state import (
    load_transaction,
)


def transaction_summary(
    transaction_id: str,
):
    transaction = load_transaction(
        transaction_id
    )

    if transaction is None:
        raise ValueError(
            (
                "Coding transaction does not exist: "
                f"{transaction_id}"
            )
        )

    return {
        "transaction_id":
            transaction.transaction_id,

        "repository":
            transaction.repository,

        "goal":
            transaction.goal,

        "status":
            transaction.status,

        "baseline_branch":
            transaction.baseline_branch,

        "baseline_commit":
            transaction.baseline_commit,

        "planned_paths":
            transaction.planned_paths,

        "changed_paths":
            transaction.changed_paths,

        "targeted_tests_passed":
            transaction.targeted_tests_passed,

        "regression_passed":
            transaction.regression_passed,

        "rollback_performed":
            transaction.rollback_performed,

        "approval_required":
            transaction.approval_required,

        "approved_for_commit":
            transaction.approved_for_commit,

        "error":
            transaction.error,
    }


def format_transaction_summary(
    transaction_id: str,
):
    summary = transaction_summary(
        transaction_id
    )

    lines = [
        (
            "Coding transaction: "
            f"{summary['transaction_id']}"
        ),
        (
            "Repository: "
            f"{summary['repository']}"
        ),
        (
            "Status: "
            f"{summary['status']}"
        ),
        (
            "Goal: "
            f"{summary['goal']}"
        ),
        (
            "Baseline branch: "
            f"{summary['baseline_branch']}"
        ),
        (
            "Baseline commit: "
            f"{summary['baseline_commit']}"
        ),
        "Planned files:",
    ]

    for path in summary[
        "planned_paths"
    ]:
        lines.append(
            f"- {path}"
        )

    if summary[
        "changed_paths"
    ]:
        lines.append(
            "Changed files:"
        )

        for path in summary[
            "changed_paths"
        ]:
            lines.append(
                f"- {path}"
            )

    return "\n".join(
        lines
    )
