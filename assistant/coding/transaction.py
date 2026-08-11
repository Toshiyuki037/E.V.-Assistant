"""
E.V.I.E. - Safe Coding Transactions

Phase 12I

This layer creates a transaction baseline BEFORE any coding agent edits a
repository.

Safety properties:
- records current branch/commit
- refuses dirty repositories by default
- records planned paths
- snapshots file contents
- persists transaction state
- supports exact snapshot rollback
- does NOT create branches or commits yet
- does NOT perform AI-generated edits yet
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
from pathlib import Path
import uuid

from .git import (
    current_branch,
    current_commit,
    diff_text,
    working_tree_status,
)

from .models import (
    CodingTransaction,
    FileSnapshot,
)

from .state import (
    load_transaction,
    save_transaction,
)


def _now():
    return (
        datetime.now(
            timezone.utc
        ).isoformat()
    )


def _hash_content(
    content: str,
):
    return (
        hashlib.sha256(
            content.encode(
                "utf-8"
            )
        ).hexdigest()
    )


def new_transaction_id():
    return (
        "code_tx_"
        + uuid.uuid4().hex[
            :12
        ]
    )


def _resolve_safe_path(
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


def snapshot_path(
    root_path: str,
    relative_path: str,
):
    target = _resolve_safe_path(
        root_path,
        relative_path,
    )

    if not target.exists():
        return FileSnapshot(
            path=relative_path,
            existed=False,
            content="",
            sha256="",
        )

    if not target.is_file():
        raise ValueError(
            (
                "Coding transaction path is not a file: "
                f"{relative_path}"
            )
        )

    content = target.read_text(
        encoding="utf-8",
        errors="ignore",
    )

    return FileSnapshot(
        path=relative_path,
        existed=True,
        content=content,
        sha256=_hash_content(
            content
        ),
    )


def create_transaction(
    *,
    repository: str,
    root_path: str,
    goal: str,
    planned_paths: list[str],
    require_clean_tree: bool = True,
    approval_required: bool = True,
):
    """
    Create and persist the repository baseline.

    This does not edit files.
    """

    root = Path(
        root_path
    ).resolve()

    if not root.exists():
        raise ValueError(
            (
                "Repository root does not exist: "
                f"{root}"
            )
        )

    dirty = working_tree_status(
        str(
            root
        )
    )

    if (
        require_clean_tree
        and dirty
    ):
        raise RuntimeError(
            (
                "Repository working tree is not clean. "
                "Refusing to create a safe coding transaction."
            )
        )

    branch = current_branch(
        str(
            root
        )
    )

    commit = current_commit(
        str(
            root
        )
    )

    if not commit:
        raise RuntimeError(
            (
                "Could not resolve repository baseline commit."
            )
        )

    snapshots = {}

    for relative_path in planned_paths:
        snapshot = snapshot_path(
            str(
                root
            ),
            relative_path,
        )

        snapshots[
            relative_path
        ] = snapshot

    now = _now()

    transaction = CodingTransaction(
        transaction_id=
            new_transaction_id(),

        repository=
            repository,

        root_path=
            str(
                root
            ),

        goal=
            goal,

        status=
            "baselined",

        baseline_branch=
            branch,

        baseline_commit=
            commit,

        planned_paths=
            list(
                planned_paths
            ),

        snapshots=
            snapshots,

        approval_required=
            approval_required,

        created_at=
            now,

        updated_at=
            now,

        metadata={
            "initial_working_tree":
                dirty,
        },
    )

    return save_transaction(
        transaction
    )


def refresh_transaction_diff(
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

    transaction.diff_text = diff_text(
        transaction.root_path
    )

    transaction.updated_at = _now()

    save_transaction(
        transaction
    )

    return transaction


def detect_changed_paths(
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

    changed = []

    for relative_path, snapshot in (
        transaction.snapshots.items()
    ):
        target = _resolve_safe_path(
            transaction.root_path,
            relative_path,
        )

        if not target.exists():
            current_exists = False
            current_content = ""
        else:
            current_exists = True
            current_content = target.read_text(
                encoding="utf-8",
                errors="ignore",
            )

        if (
            current_exists
            != snapshot.existed
        ):
            changed.append(
                relative_path
            )
            continue

        if current_exists:
            current_hash = _hash_content(
                current_content
            )

            if (
                current_hash
                != snapshot.sha256
            ):
                changed.append(
                    relative_path
                )

    transaction.changed_paths = changed

    transaction.updated_at = _now()

    save_transaction(
        transaction
    )

    return changed


def rollback_transaction(
    transaction_id: str,
):
    """
    Restore every snapshotted path exactly to baseline.

    Files that did not exist at baseline are deleted if created.
    """

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

    for relative_path, snapshot in (
        transaction.snapshots.items()
    ):
        target = _resolve_safe_path(
            transaction.root_path,
            relative_path,
        )

        if snapshot.existed:
            target.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            target.write_text(
                snapshot.content,
                encoding="utf-8",
            )

        elif target.exists():
            if target.is_file():
                target.unlink()

    transaction.rollback_performed = True

    transaction.status = (
        "rolled_back"
    )

    transaction.changed_paths = []

    transaction.diff_text = diff_text(
        transaction.root_path
    )

    transaction.updated_at = _now()

    save_transaction(
        transaction
    )

    return transaction
