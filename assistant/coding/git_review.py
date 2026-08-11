"""
E.V.I.E. - Git Review and Commit Controls

Phase 12L

Purpose:
Safely review and finalize a validated coding transaction.

Safety:
- commit only after validation
- commit only changed transaction files
- commit bound to current transaction branch
- no push
- no PR creation
- no commit without explicit approval flag
"""

from __future__ import annotations

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


def staged_files(
    root_path: str,
):
    result = _run_git(
        root_path,
        [
            "diff",
            "--cached",
            "--name-only",
        ],
    )

    if result.returncode != 0:
        return []

    return [
        line.strip()
        for line in result.stdout.splitlines()
        if line.strip()
    ]


def current_branch(
    root_path: str,
):
    result = _run_git(
        root_path,
        [
            "branch",
            "--show-current",
        ],
    )

    if result.returncode != 0:
        return ""

    return result.stdout.strip()


def stage_transaction_changes(
    transaction_id: str,
):
    transaction = load_transaction(
        transaction_id
    )

    if transaction is None:
        raise ValueError(
            f"Coding transaction does not exist: {transaction_id}"
        )

    branch = current_branch(
        transaction.root_path
    )

    if branch != transaction.working_branch:
        raise RuntimeError(
            (
                "Current branch does not match transaction branch. "
                f"Expected {transaction.working_branch}, got {branch}."
            )
        )

    if not transaction.changed_paths:
        raise RuntimeError(
            "Transaction has no detected changed files."
        )

    allowed = set(
        transaction.planned_paths
    )

    for path in transaction.changed_paths:
        if path not in allowed:
            raise RuntimeError(
                (
                    "Changed file is outside transaction plan: "
                    f"{path}"
                )
            )

    result = _run_git(
        transaction.root_path,
        [
            "add",
            "--",
            *transaction.changed_paths,
        ],
    )

    if result.returncode != 0:
        raise RuntimeError(
            (
                "Failed to stage transaction changes:\n"
                + result.stderr
            )
        )

    staged = staged_files(
        transaction.root_path
    )

    unexpected = [
        path
        for path in staged
        if path not in allowed
    ]

    if unexpected:
        raise RuntimeError(
            (
                "Unexpected staged files detected: "
                + ", ".join(
                    unexpected
                )
            )
        )

    transaction.status = "staged"

    save_transaction(
        transaction
    )

    return staged


def approve_transaction_commit(
    transaction_id: str,
    *,
    commit_message: str,
):
    transaction = load_transaction(
        transaction_id
    )

    if transaction is None:
        raise ValueError(
            f"Coding transaction does not exist: {transaction_id}"
        )

    if not commit_message.strip():
        raise ValueError(
            "Commit message cannot be empty."
        )

    transaction.approved_for_commit = True
    transaction.commit_message = commit_message.strip()
    transaction.status = "commit_approved"

    save_transaction(
        transaction
    )

    return transaction


def commit_transaction(
    transaction_id: str,
):
    transaction = load_transaction(
        transaction_id
    )

    if transaction is None:
        raise ValueError(
            f"Coding transaction does not exist: {transaction_id}"
        )

    if not transaction.approved_for_commit:
        raise RuntimeError(
            "Commit has not been explicitly approved."
        )

    if transaction.targeted_tests_passed is False:
        raise RuntimeError(
            "Targeted validation failed."
        )

    if transaction.regression_passed is not True:
        raise RuntimeError(
            "Full regression must pass before commit."
        )

    branch = current_branch(
        transaction.root_path
    )

    if branch != transaction.working_branch:
        raise RuntimeError(
            (
                "Current branch does not match transaction branch. "
                f"Expected {transaction.working_branch}, got {branch}."
            )
        )

    staged = staged_files(
        transaction.root_path
    )

    if not staged:
        raise RuntimeError(
            "No staged transaction changes exist."
        )

    allowed = set(
        transaction.planned_paths
    )

    unexpected = [
        path
        for path in staged
        if path not in allowed
    ]

    if unexpected:
        raise RuntimeError(
            (
                "Refusing commit because unrelated files are staged: "
                + ", ".join(
                    unexpected
                )
            )
        )

    result = _run_git(
        transaction.root_path,
        [
            "commit",
            "-m",
            transaction.commit_message,
        ],
    )

    if result.returncode != 0:
        raise RuntimeError(
            (
                "Git commit failed:\n"
                + result.stderr
            )
        )

    commit_result = _run_git(
        transaction.root_path,
        [
            "rev-parse",
            "HEAD",
        ],
    )

    commit_sha = (
        commit_result.stdout.strip()
        if commit_result.returncode == 0
        else ""
    )

    transaction.status = "committed"

    transaction.metadata[
        "commit_sha"
    ] = commit_sha

    save_transaction(
        transaction
    )

    return transaction
