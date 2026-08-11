"""
E.V.I.E. - Coding Repair Loop

Phase 12K

Purpose:
Execute a bounded diagnose -> repair -> validate loop inside an existing
coding transaction.

Safety:
- repairs stay inside planned_paths
- each iteration is bounded
- failed repair may rollback
- no commit/push
"""

from __future__ import annotations

from .diagnostics import (
    diagnose_command_failure,
)

from .editing import (
    write_transaction_file,
)

from .execution import (
    run_transaction_command,
)

from .repair_planner import (
    plan_repair,
)

from .state import (
    load_transaction,
    save_transaction,
)

from .transaction import (
    rollback_transaction,
)


def run_repair_loop(
    transaction_id: str,
    failed_record,
    *,
    max_repairs: int = 3,
    auto_rollback_on_exhaustion: bool = True,
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

    diagnostic = diagnose_command_failure(
        failed_record
    )

    attempts = []

    for attempt_number in range(
        1,
        max(
            1,
            max_repairs,
        )
        + 1,
    ):
        plan = plan_repair(
            transaction_id,
            diagnostic,
        )

        attempts.append(
            {
                "attempt":
                    attempt_number,

                "action":
                    plan.action,

                "diagnosis":
                    plan.diagnosis,

                "confidence":
                    plan.confidence,

                "rationale":
                    plan.rationale,
            }
        )

        if plan.action == "rollback":
            rollback_transaction(
                transaction_id
            )

            return {
                "status":
                    "rolled_back",

                "attempts":
                    attempts,

                "diagnostic":
                    diagnostic,
            }

        if plan.action in {
            "request_user",
            "stop",
        }:
            transaction = load_transaction(
                transaction_id
            )

            transaction.status = (
                "awaiting_user"
                if plan.action
                == "request_user"
                else "repair_stopped"
            )

            transaction.error = (
                plan.diagnosis
                or diagnostic.summary
            )

            save_transaction(
                transaction
            )

            return {
                "status":
                    transaction.status,

                "attempts":
                    attempts,

                "diagnostic":
                    diagnostic,
            }

        if plan.action == "retry":
            validation_commands = (
                plan.validation_commands
            )

        else:
            for edit in plan.edits:
                write_transaction_file(
                    transaction_id,
                    edit.path,
                    edit.content,
                )

            validation_commands = (
                plan.validation_commands
            )

        if not validation_commands:
            transaction = load_transaction(
                transaction_id
            )

            transaction.status = (
                "awaiting_user"
            )

            transaction.error = (
                "Repair plan supplied no "
                "validation commands."
            )

            save_transaction(
                transaction
            )

            return {
                "status":
                    "awaiting_user",

                "attempts":
                    attempts,

                "diagnostic":
                    diagnostic,
            }

        last_record = None

        all_passed = True

        for command in validation_commands:
            last_record = (
                run_transaction_command(
                    transaction_id,
                    command,
                    mark_as=
                        "targeted_tests",
                )
            )

            if last_record.returncode != 0:
                all_passed = False
                break

        if all_passed:
            transaction = load_transaction(
                transaction_id
            )

            transaction.status = (
                "repair_validated"
            )

            transaction.error = ""

            save_transaction(
                transaction
            )

            return {
                "status":
                    "repair_validated",

                "attempts":
                    attempts,

                "diagnostic":
                    diagnostic,

                "last_record":
                    last_record,
            }

        diagnostic = diagnose_command_failure(
            last_record
        )

    if auto_rollback_on_exhaustion:
        rollback_transaction(
            transaction_id
        )

        status = "rolled_back"

    else:
        transaction = load_transaction(
            transaction_id
        )

        transaction.status = (
            "repair_exhausted"
        )

        transaction.error = (
            diagnostic.summary
        )

        save_transaction(
            transaction
        )

        status = "repair_exhausted"

    return {
        "status":
            status,

        "attempts":
            attempts,

        "diagnostic":
            diagnostic,
    }
