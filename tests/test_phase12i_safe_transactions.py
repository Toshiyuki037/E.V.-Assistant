"""
Phase 12I safe coding transaction tests.
"""

import subprocess

import assistant.coding.state as coding_state

from assistant.coding.transaction import (
    create_transaction,
    detect_changed_paths,
    rollback_transaction,
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


def test_transaction_snapshots_and_rolls_back(
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

    transaction = create_transaction(
        repository="test",
        root_path=str(
            tmp_path
        ),
        goal="Modify example.",
        planned_paths=[
            "example.py"
        ],
    )

    path.write_text(
        "VALUE = 2\n",
        encoding="utf-8",
    )

    changed = detect_changed_paths(
        transaction.transaction_id
    )

    assert (
        "example.py"
        in changed
    )

    rollback_transaction(
        transaction.transaction_id
    )

    assert (
        path.read_text(
            encoding="utf-8"
        )
        == "VALUE = 1\n"
    )


def test_dirty_tree_refused(
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

    path.write_text(
        "DIRTY = True\n",
        encoding="utf-8",
    )

    try:
        create_transaction(
            repository="test",
            root_path=str(
                tmp_path
            ),
            goal="Unsafe test.",
            planned_paths=[
                "example.py"
            ],
        )

    except RuntimeError:
        return

    assert False, (
        "Dirty repository should have been refused."
    )
