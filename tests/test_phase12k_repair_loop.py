"""
Phase 12K diagnostic and repair-loop tests.

The tests do not call the real reasoning model.
Repair planning is monkeypatched with a deterministic bounded plan.
"""

import subprocess

import assistant.coding.state as coding_state
import assistant.coding.repair_loop as repair_loop_module

from assistant.coding.branch import (
    create_transaction_branch,
)
from assistant.coding.editing import (
    write_transaction_file,
)
from assistant.coding.execution import (
    run_transaction_command,
)
from assistant.coding.repair_models import (
    RepairEdit,
    RepairPlan,
)
from assistant.coding.transaction import (
    create_transaction,
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

    file_path = (
        tmp_path
        / "example.py"
    )

    file_path.write_text(
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

    return file_path


def test_repair_loop_repairs_syntax_error(
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

    file_path = _repo(
        tmp_path
    )

    tx = create_transaction(
        repository="test",
        root_path=str(
            tmp_path
        ),
        goal="Keep example valid.",
        planned_paths=[
            "example.py"
        ],
    )

    create_transaction_branch(
        tx.transaction_id,
        branch_name=
            "evie/repair-test",
    )

    write_transaction_file(
        tx.transaction_id,
        "example.py",
        "VALUE =\n",
    )

    failed = run_transaction_command(
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
        failed.returncode
        != 0
    )

    def fake_plan(
        transaction_id,
        diagnostic,
    ):
        return RepairPlan(
            action=
                "repair",

            diagnosis=
                "Syntax error in example.py.",

            edits=[
                RepairEdit(
                    path=
                        "example.py",

                    content=
                        "VALUE = 2\n",

                    reason=
                        "Restore valid assignment.",
                )
            ],

            validation_commands=[
                [
                    "python",
                    "-m",
                    "py_compile",
                    "example.py",
                ]
            ],

            confidence=
                100,
        )

    monkeypatch.setattr(
        repair_loop_module,
        "plan_repair",
        fake_plan,
    )

    result = (
        repair_loop_module.run_repair_loop(
            tx.transaction_id,
            failed,
            max_repairs=2,
        )
    )

    assert (
        result[
            "status"
        ]
        == "repair_validated"
    )

    assert (
        file_path.read_text(
            encoding="utf-8"
        )
        == "VALUE = 2\n"
    )


def test_repair_plan_outside_scope_never_applied(
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
        goal="Bounded repair.",
        planned_paths=[
            "example.py"
        ],
    )

    create_transaction_branch(
        tx.transaction_id,
        branch_name=
            "evie/bounded-test",
    )

    failed = run_transaction_command(
        tx.transaction_id,
        [
            "python",
            "-c",
            "raise SystemExit(1)",
        ],
        mark_as=
            "targeted_tests",
    )

    def fake_plan(
        transaction_id,
        diagnostic,
    ):
        return RepairPlan(
            action=
                "request_user",

            diagnosis=
                "Cannot safely repair "
                "inside planned scope.",

            confidence=
                100,
        )

    monkeypatch.setattr(
        repair_loop_module,
        "plan_repair",
        fake_plan,
    )

    result = (
        repair_loop_module.run_repair_loop(
            tx.transaction_id,
            failed,
        )
    )

    assert (
        result[
            "status"
        ]
        == "awaiting_user"
    )
