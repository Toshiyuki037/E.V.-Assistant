"""
Phase 12L review and commit controls tests.
"""

import subprocess

import assistant.coding.state as coding_state

from assistant.coding.transaction import (
    create_transaction,
)
from assistant.coding.branch import (
    create_transaction_branch,
)
from assistant.coding.editing import (
    write_transaction_file,
)
from assistant.coding.execution import (
    run_transaction_command,
)
from assistant.coding.git_review import (
    stage_transaction_changes,
    approve_transaction_commit,
    commit_transaction,
)
from assistant.coding.completion import (
    completion_gate,
)


def _git(
    root,
    *args,
):
    return subprocess.run(
        [
            "git",
            *args,
        ],
        cwd=str(
            root
        ),
        capture_output=True,
        text=True,
        check=False,
    )


def _repo(
    tmp_path,
):
    _git(
        tmp_path,
        "init",
    )

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

    path = (
        tmp_path
        / "example.py"
    )

    path.write_text(
        "VALUE = 1\n",
        encoding="utf-8",
    )

    _git(
        tmp_path,
        "add",
        ".",
    )

    _git(
        tmp_path,
        "commit",
        "-m",
        "baseline",
    )

    return path


def test_commit_requires_regression_and_approval(
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

    _repo(
        tmp_path
    )

    tx = create_transaction(
        repository="test",
        root_path=str(
            tmp_path
        ),
        goal="Commit safe change.",
        planned_paths=[
            "example.py"
        ],
    )

    create_transaction_branch(
        tx.transaction_id,
        branch_name=
            "evie/commit-test",
    )

    write_transaction_file(
        tx.transaction_id,
        "example.py",
        "VALUE = 2\n",
    )

    run_transaction_command(
        tx.transaction_id,
        [
            "python",
            "-m",
            "py_compile",
            "example.py",
        ],
        mark_as=
            "targeted_tests",
    )

    run_transaction_command(
        tx.transaction_id,
        [
            "python",
            "-m",
            "py_compile",
            "example.py",
        ],
        mark_as=
            "regression",
    )

    gate = completion_gate(
        tx.transaction_id
    )

    assert gate[
        "ready"
    ]

    stage_transaction_changes(
        tx.transaction_id
    )

    approve_transaction_commit(
        tx.transaction_id,
        commit_message=
            "Update example",
    )

    committed = commit_transaction(
        tx.transaction_id
    )

    assert (
        committed.status
        == "committed"
    )

    assert committed.metadata.get(
        "commit_sha"
    )


def test_commit_without_approval_rejected(
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

    _repo(
        tmp_path
    )

    tx = create_transaction(
        repository="test",
        root_path=str(
            tmp_path
        ),
        goal="Reject unsafe commit.",
        planned_paths=[
            "example.py"
        ],
    )

    create_transaction_branch(
        tx.transaction_id,
        branch_name=
            "evie/no-approval",
    )

    write_transaction_file(
        tx.transaction_id,
        "example.py",
        "VALUE = 3\n",
    )

    run_transaction_command(
        tx.transaction_id,
        [
            "python",
            "-m",
            "py_compile",
            "example.py",
        ],
        mark_as=
            "targeted_tests",
    )

    run_transaction_command(
        tx.transaction_id,
        [
            "python",
            "-m",
            "py_compile",
            "example.py",
        ],
        mark_as=
            "regression",
    )

    stage_transaction_changes(
        tx.transaction_id
    )

    try:
        commit_transaction(
            tx.transaction_id
        )

    except RuntimeError:
        return

    assert False, (
        "Commit without approval must fail."
    )
