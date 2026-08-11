"""
Phase 12J controlled branch/edit/execution tests.
"""

import subprocess

import assistant.coding.state as coding_state

from assistant.coding.transaction import (
    create_transaction,
    rollback_transaction,
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
from assistant.coding.verification import (
    transaction_ready_for_review,
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


def test_branch_edit_and_validate(
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

    path = _repo(
        tmp_path
    )

    tx = create_transaction(
        repository="test",
        root_path=str(
            tmp_path
        ),
        goal="Change value.",
        planned_paths=[
            "example.py"
        ],
    )

    tx = create_transaction_branch(
        tx.transaction_id,
        branch_name=
            "evie/test-change",
    )

    assert (
        tx.working_branch
        == "evie/test-change"
    )

    changed = write_transaction_file(
        tx.transaction_id,
        "example.py",
        "VALUE = 2\n",
    )

    assert (
        "example.py"
        in changed
    )

    record = run_transaction_command(
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

    assert (
        record.returncode
        == 0
    )

    assert transaction_ready_for_review(
        tx.transaction_id
    )

    rollback_transaction(
        tx.transaction_id
    )

    assert (
        path.read_text(
            encoding="utf-8"
        )
        == "VALUE = 1\n"
    )


def test_edit_outside_plan_rejected(
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
        goal="Safe edit.",
        planned_paths=[
            "example.py"
        ],
    )

    create_transaction_branch(
        tx.transaction_id,
        branch_name=
            "evie/scope-test",
    )

    try:
        write_transaction_file(
            tx.transaction_id,
            "outside.py",
            "X = 1\n",
        )

    except RuntimeError:
        return

    assert False, (
        "Editing outside planned paths should fail."
    )
