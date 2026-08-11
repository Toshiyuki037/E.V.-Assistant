"""
E.V.I.E. - Self-Engineering Commit Approval

Phase 12M

Explicitly completes an already-reviewed self-engineering transaction.
No push or merge occurs.
"""

from __future__ import annotations

from .completion import completion_gate
from .git_review import (
    approve_transaction_commit,
    commit_transaction,
    stage_transaction_changes,
)


def approve_and_commit_engineering_transaction(
    transaction_id: str,
    *,
    commit_message: str,
):
    gate = completion_gate(
        transaction_id
    )

    if not gate[
        "ready"
    ]:
        raise RuntimeError(
            (
                "Coding transaction is not ready for commit: "
                + "; ".join(
                    gate[
                        "reasons"
                    ]
                )
            )
        )

    stage_transaction_changes(
        transaction_id
    )

    approve_transaction_commit(
        transaction_id,
        commit_message=commit_message,
    )

    return commit_transaction(
        transaction_id
    )
