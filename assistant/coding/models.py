"""
E.V.I.E. - Coding Models

Phase 12I / 12M

Purpose:
Shared data structures for safe coding transactions and repository-level
self-engineering plans.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any


# ---------------------------------------------------------------------------
# Phase 12I Transaction Models
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Phase 12M Self-Engineering Models
# ---------------------------------------------------------------------------

@dataclass
class EngineeringEdit:
    path: str
    content: str
    reason: str = ""


@dataclass
class EngineeringPlan:
    goal: str
    repository: str

    planned_paths: list[str] = field(
        default_factory=list
    )

    edits: list[EngineeringEdit] = field(
        default_factory=list
    )

    targeted_commands: list[list[str]] = field(
        default_factory=list
    )

    regression_command: list[str] = field(
        default_factory=list
    )

    commit_message: str = ""
    documentation_note: str = ""

    confidence: int = 0
    rationale: str = ""

    metadata: dict[str, Any] = field(
        default_factory=dict
    )
