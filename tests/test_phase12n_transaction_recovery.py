import subprocess

import assistant.coding.state as coding_state

from assistant.coding.branch import create_transaction_branch
from assistant.coding.editing import write_transaction_file
from assistant.coding.recovery import (
    find_latest_recoverable_transaction,
    resume_engineering_transaction,
)
from assistant.coding.transaction import create_transaction


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
    _git(tmp_path, "config", "user.email", "test@example.com")
    _git(tmp_path, "config", "user.name", "E.V.I.E. Test")

    path = tmp_path / "example.py"
    path.write_text("VALUE = 1\n", encoding="utf-8")

    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-m", "baseline")

    return path


def test_awaiting_user_transaction_can_resume_to_commit_gate(
    tmp_path,
    monkeypatch,
):
    runtime = tmp_path / "runtime" / "transactions"

    monkeypatch.setattr(
        coding_state,
        "TRANSACTION_RUNTIME",
        runtime,
    )

    _repo(tmp_path)

    tx = create_transaction(
        repository="test",
        root_path=str(tmp_path),
        goal="Recover validation.",
        planned_paths=["example.py"],
    )

    create_transaction_branch(
        tx.transaction_id,
        branch_name="evie/recovery-test",
    )

    write_transaction_file(
        tx.transaction_id,
        "example.py",
        "VALUE = 2\n",
    )

    tx = coding_state.load_transaction(
        tx.transaction_id
    )

    tx.status = "awaiting_user"
    tx.error = "External environment failure."

    tx.metadata["engineering_plan"] = {
        "targeted_commands": [
            [
                "python",
                "-m",
                "py_compile",
                "example.py",
            ]
        ],
        "regression_command": [
            "python",
            "-m",
            "py_compile",
            "example.py",
        ],
        "commit_message": "Recover validation",
    }

    coding_state.save_transaction(tx)

    result = resume_engineering_transaction(
        tx.transaction_id
    )

    assert result["status"] == "awaiting_commit_approval"

    updated = coding_state.load_transaction(
        tx.transaction_id
    )

    assert updated.targeted_tests_passed is True
    assert updated.regression_passed is True
    assert updated.error == ""


def test_latest_recoverable_transaction_is_found(
    tmp_path,
    monkeypatch,
):
    runtime = tmp_path / "runtime" / "transactions"

    monkeypatch.setattr(
        coding_state,
        "TRANSACTION_RUNTIME",
        runtime,
    )

    _repo(tmp_path)

    tx = create_transaction(
        repository="test",
        root_path=str(tmp_path),
        goal="Find recovery transaction.",
        planned_paths=["example.py"],
    )

    tx.status = "awaiting_user"
    coding_state.save_transaction(tx)

    found = find_latest_recoverable_transaction()

    assert found is not None
    assert found.transaction_id == tx.transaction_id
