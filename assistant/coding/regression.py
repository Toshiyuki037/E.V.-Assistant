"""
E.V.I.E. - Coding Regression Validation

Phase 12K

Runs targeted validation and full regression through the existing safe
transaction command executor.
"""

from __future__ import annotations

from .execution import (
    run_transaction_command,
)

from .state import (
    load_transaction,
    save_transaction,
)


def run_validation_sequence(
    transaction_id: str,
    *,
    targeted_commands: list[list[str]],
    regression_command: list[str],
):
    targeted_records = []

    for command in targeted_commands:
        record = run_transaction_command(
            transaction_id,
            command,
            mark_as=
                "targeted_tests",
        )

        targeted_records.append(
            record
        )

        if record.returncode != 0:
            return {
                "status":
                    "targeted_failed",

                "targeted":
                    targeted_records,

                "regression":
                    None,
            }

    regression = run_transaction_command(
        transaction_id,
        regression_command,
        mark_as=
            "regression",
    )

    transaction = load_transaction(
        transaction_id
    )

    if regression.returncode == 0:
        transaction.status = (
            "regression_passed"
        )
    else:
        transaction.status = (
            "regression_failed"
        )

    save_transaction(
        transaction
    )

    return {
        "status":
            transaction.status,

        "targeted":
            targeted_records,

        "regression":
            regression,
    }
