"""
E.V.I.E. - Coding Transaction Verification

Phase 12J
"""

from __future__ import annotations

from .state import (
    load_transaction,
)


def transaction_ready_for_review(
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

    return (
        bool(
            transaction.changed_paths
        )
        and (
            transaction.targeted_tests_passed
            is not False
        )
        and (
            transaction.regression_passed
            is not False
        )
        and not transaction.rollback_performed
    )
