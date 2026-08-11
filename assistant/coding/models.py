"""
E.V.I.E. - Coding Transaction Models

Phase 12I

Purpose:
Represent one safe repository change transaction from baseline through
planned edits, verification, rollback, review, and commit preparation.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass
class FileSnapshot:
    path: str
    existed: bool
    content: str = ""
    sha256: str = ""


@dataclass
class CommandRecord:
    command: str
    returncode: int | None = None
    stdout: str = ""
    stderr: str = ""
    started_at: str = ""
    completed_at: str = ""


@dataclass
class CodingTransaction:
    transaction_id: str
    repository: str
    root_path: str
    goal: str

    status: str = "created"

    baseline_branch: str = ""
    baseline_commit: str = ""
    working_branch: str = ""

    planned_paths: list[str] = field(default_factory=list)

    snapshots: dict[str, FileSnapshot] = field(
        default_factory=dict
    )

    commands: list[CommandRecord] = field(
        default_factory=list
    )

    changed_paths: list[str] = field(
        default_factory=list
    )

    diff_text: str = ""

    targeted_tests_passed: bool | None = None
    regression_passed: bool | None = None

    rollback_performed: bool = False

    approval_required: bool = True
    approved_for_commit: bool = False

    commit_message: str = ""

    error: str = ""

    created_at: str = ""
    updated_at: str = ""

    metadata: dict[str, Any] = field(
        default_factory=dict
    )


def transaction_to_dict(
    transaction: CodingTransaction,
):
    return asdict(
        transaction
    )
