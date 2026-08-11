"""
E.V.I.E. - Coding Completion Gate

Phase 12L

Determines whether a transaction is safe to present for commit approval.
"""

from __future__ import annotations

from .state import (
    load_transaction,
)


def completion_gate(
    transaction_id: str,
):
    transaction = load_transaction(
        transaction_id
    )

    if transaction is None:
        raise ValueError(
            f"Coding transaction does not exist: {transaction_id}"
        )

    reasons = []

    if not transaction.changed_paths:
        reasons.append(
            "No changed files detected."
        )

    if transaction.targeted_tests_passed is not True:
        reasons.append(
            "Targeted validation has not passed."
        )

    if transaction.regression_passed is not True:
        reasons.append(
            "Full regression has not passed."
        )

    if transaction.rollback_performed:
        reasons.append(
            "Transaction was rolled back."
        )

    unexpected = [
        path
        for path in transaction.changed_paths
        if path not in transaction.planned_paths
    ]

    if unexpected:
        reasons.append(
            (
                "Unexpected changed files: "
                + ", ".join(
                    unexpected
                )
            )
        )

    return {
        "ready":
            not reasons,

        "reasons":
            reasons,
    }
