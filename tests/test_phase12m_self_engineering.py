"""
Phase 12M self-engineering controller tests.

These tests use explicit EngineeringPlan objects and do not call the LLM.
"""

import subprocess

import assistant.coding.state as coding_state

from assistant.coding.models import (
    EngineeringEdit,
    EngineeringPlan,
)
from assistant.coding.controller import (
    execute_engineering_plan,
)
from assistant.coding.approval import (
    approve_and_commit_engineering_transaction,
)


def _git(root, *args):
    return subprocess.run(
        ["git", *args],
        cwd=str(root),
        capture_output=True,
        text=True,
        check=False,
    )


def _repo(tmp_path):
    _git(tmp_path, "init")
    _git(
        tmp_path,
        "config",
        "user.email",
        "test@example.com",
    )
    _git(
        tmp_path,
        "config",
        "user.name",
        "E.V.I.E. Test",
    )

    path = tmp_path / "example.py"
    path.write_text(
        "VALUE = 1\n",
        encoding="utf-8",
    )

    _git(tmp_path, "add", ".")
    _git(
        tmp_path,
        "commit",
        "-m",
        "baseline",
    )

    return path


def test_self_engineering_stops_for_commit_approval(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(
        coding_state,
        "TRANSACTION_RUNTIME",
        tmp_path
        / "runtime"
        / "transactions",
    )

    _repo(tmp_path)

    plan = EngineeringPlan(
        goal="Update example value.",
        repository="test",
        planned_paths=[
            "example.py"
        ],
        edits=[
            EngineeringEdit(
                path="example.py",
                content="VALUE = 2\n",
            )
        ],
        targeted_commands=[
            [
                "python",
                "-m",
                "py_compile",
                "example.py",
            ]
        ],
        regression_command=[
            "python",
            "-m",
            "py_compile",
            "example.py",
        ],
        commit_message="Update example value",
        confidence=100,
    )

    result = execute_engineering_plan(
        plan,
        root_path=str(tmp_path),
        branch_name="evie/self-engineering-test",
    )

    assert (
        result["status"]
        == "awaiting_commit_approval"
    )

    committed = (
        approve_and_commit_engineering_transaction(
            result["transaction_id"],
            commit_message=
                result[
                    "suggested_commit_message"
                ],
        )
    )

    assert committed.status == "committed"
    assert committed.metadata.get("commit_sha")


def test_no_safe_plan_does_nothing(
    tmp_path,
):
    plan = EngineeringPlan(
        goal="Impossible change.",
        repository="test",
    )

    result = execute_engineering_plan(
        plan,
        root_path=str(tmp_path),
    )

    assert result["status"] == "no_safe_plan"
    assert result["transaction_id"] == ""
