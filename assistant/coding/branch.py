"""
E.V.I.E. - Coding Branch Management

Phase 12J

Purpose:
Create and inspect safe Git branches for coding transactions.

Branch creation is explicit and transaction-bound.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

from .state import (
    load_transaction,
    save_transaction,
)


def _run_git(
    root_path: str,
    arguments: list[str],
):
    return subprocess.run(
        [
            "git",
            *arguments,
        ],
        cwd=str(
            Path(
                root_path
            ).resolve()
        ),
        capture_output=True,
        text=True,
        check=False,
    )


def _safe_branch_name(
    value: str,
):
    value = re.sub(
        r"[^A-Za-z0-9._/-]+",
        "-",
        str(
            value
            or ""
        ).strip(),
    )

    value = re.sub(
        r"-+",
        "-",
        value,
    )

    return value.strip(
        "-/"
    )


def create_transaction_branch(
    transaction_id: str,
    *,
    branch_name: str | None = None,
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

    if transaction.status not in {
        "baselined",
        "branch_created",
    }:
        raise RuntimeError(
            (
                "Transaction is not ready for branch creation. "
                f"Current status: {transaction.status}"
            )
        )

    resolved = (
        _safe_branch_name(
            branch_name
            or (
                "evie/"
                + transaction.transaction_id
            )
        )
    )

    if not resolved:
        raise ValueError(
            "Branch name resolved to empty value."
        )

    result = _run_git(
        transaction.root_path,
        [
            "checkout",
            "-b",
            resolved,
        ],
    )

    if result.returncode != 0:
        raise RuntimeError(
            (
                "Failed to create transaction branch:\n"
                + result.stderr
            )
        )

    transaction.working_branch = resolved
    transaction.status = "branch_created"

    save_transaction(
        transaction
    )

    return transaction
