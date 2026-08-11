"""
E.V.I.E. - Coding Diff Review

Phase 12L

Creates a bounded review summary for a coding transaction.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from .state import (
    load_transaction,
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


def transaction_diff(
    transaction_id: str,
):
    transaction = load_transaction(
        transaction_id
    )

    if transaction is None:
        raise ValueError(
            f"Coding transaction does not exist: {transaction_id}"
        )

    result = _run_git(
        transaction.root_path,
        [
            "diff",
            "--",
            *transaction.planned_paths,
        ],
    )

    if result.returncode != 0:
        return ""

    return result.stdout


def review_transaction(
    transaction_id: str,
):
    transaction = load_transaction(
        transaction_id
    )

    if transaction is None:
        raise ValueError(
            f"Coding transaction does not exist: {transaction_id}"
        )

    diff = transaction_diff(
        transaction_id
    )

    return {
        "transaction_id":
            transaction.transaction_id,

        "goal":
            transaction.goal,

        "status":
            transaction.status,

        "working_branch":
            transaction.working_branch,

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

        "diff":
            diff,
    }


def format_review(
    transaction_id: str,
):
    review = review_transaction(
        transaction_id
    )

    lines = [
        f"Transaction: {review['transaction_id']}",
        f"Goal: {review['goal']}",
        f"Status: {review['status']}",
        f"Branch: {review['working_branch']}",
        f"Baseline: {review['baseline_commit']}",
        (
            "Targeted tests: "
            f"{review['targeted_tests_passed']}"
        ),
        (
            "Regression: "
            f"{review['regression_passed']}"
        ),
        "Changed files:",
    ]

    for path in review[
        "changed_paths"
    ]:
        lines.append(
            f"- {path}"
        )

    lines.append(
        "Diff:"
    )

    lines.append(
        review[
            "diff"
        ]
        or "(no diff)"
    )

    return "\n".join(
        lines
    )
