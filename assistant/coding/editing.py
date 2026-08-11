"""
E.V.I.E. - Controlled File Editing

Phase 12J

Purpose:
Apply explicit file replacements inside the planned transaction scope.

This module does not decide what code to write. It only enforces:
- repository-root confinement
- transaction path allowlist
- baseline transaction existence
- controlled UTF-8 writes
"""

from __future__ import annotations

from pathlib import Path

from .state import (
    load_transaction,
    save_transaction,
)

from .transaction import (
    detect_changed_paths,
    refresh_transaction_diff,
)


def _safe_target(
    root_path: str,
    relative_path: str,
):
    root = Path(
        root_path
    ).resolve()

    target = (
        root
        / relative_path
    ).resolve()

    try:
        target.relative_to(
            root
        )
    except ValueError:
        raise ValueError(
            (
                "Path escapes repository root: "
                f"{relative_path}"
            )
        )

    return target


def write_transaction_file(
    transaction_id: str,
    relative_path: str,
    content: str,
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

    if relative_path not in transaction.planned_paths:
        raise RuntimeError(
            (
                "File is outside transaction plan: "
                f"{relative_path}"
            )
        )

    if transaction.status not in {
        "branch_created",
        "editing",
        "edited",
        "validation_failed",
    }:
        raise RuntimeError(
            (
                "Transaction is not ready for editing. "
                f"Current status: {transaction.status}"
            )
        )

    target = _safe_target(
        transaction.root_path,
        relative_path,
    )

    target.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    target.write_text(
        str(
            content
        ),
        encoding="utf-8",
    )

    transaction.status = "editing"

    save_transaction(
        transaction
    )

    changed = detect_changed_paths(
        transaction_id
    )

    transaction = load_transaction(
        transaction_id
    )

    transaction.status = "edited"

    save_transaction(
        transaction
    )

    refresh_transaction_diff(
        transaction_id
    )

    return changed
