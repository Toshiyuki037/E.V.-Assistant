"""
E.V.I.E. - Self-Engineering Controller

Phase 12M

Purpose:
Orchestrate the repository-level engineering pipeline built across
Phase 12H-12L.

The controller can:
1. accept an already-bounded EngineeringPlan
2. create a safe transaction
3. create a transaction branch
4. apply planned edits
5. run targeted validation
6. invoke bounded repair on failure
7. run full regression
8. generate diff review
9. stop for explicit commit approval

It intentionally does NOT auto-approve a commit.
"""

from __future__ import annotations

from .branch import create_transaction_branch
from .completion import completion_gate
from .diff_review import review_transaction
from .editing import write_transaction_file
from .execution import run_transaction_command
from .repair_loop import run_repair_loop
from .state import load_transaction, save_transaction
from .transaction import (
    create_transaction,
    detect_changed_paths,
    refresh_transaction_diff,
)


def execute_engineering_plan(
    plan,
    *,
    root_path: str,
    branch_name: str | None = None,
    max_repairs: int = 3,
):
    if not plan.planned_paths:
        return {
            "status": "no_safe_plan",
            "message": (
                "Engineering plan contains no safe planned paths."
            ),
            "transaction_id": "",
        }

    transaction = create_transaction(
        repository=plan.repository,
        root_path=root_path,
        goal=plan.goal,
        planned_paths=plan.planned_paths,
        require_clean_tree=True,
        approval_required=True,
    )

    create_transaction_branch(
        transaction.transaction_id,
        branch_name=branch_name,
    )

    for edit in plan.edits:
        write_transaction_file(
            transaction.transaction_id,
            edit.path,
            edit.content,
        )

    detect_changed_paths(
        transaction.transaction_id
    )

    refresh_transaction_diff(
        transaction.transaction_id
    )

    for command in plan.targeted_commands:
        record = run_transaction_command(
            transaction.transaction_id,
            command,
            mark_as="targeted_tests",
        )

        if record.returncode != 0:
            repair = run_repair_loop(
                transaction.transaction_id,
                record,
                max_repairs=max_repairs,
                auto_rollback_on_exhaustion=True,
            )

            if repair["status"] != "repair_validated":
                return {
                    "status": repair["status"],
                    "transaction_id":
                        transaction.transaction_id,
                    "repair": repair,
                }

    if not plan.regression_command:
        transaction = load_transaction(
            transaction.transaction_id
        )
        transaction.status = "awaiting_user"
        transaction.error = (
            "Engineering plan did not provide "
            "a full regression command."
        )
        save_transaction(
            transaction
        )

        return {
            "status": "awaiting_user",
            "transaction_id":
                transaction.transaction_id,
            "message":
                transaction.error,
        }

    regression = run_transaction_command(
        transaction.transaction_id,
        plan.regression_command,
        mark_as="regression",
    )

    if regression.returncode != 0:
        repair = run_repair_loop(
            transaction.transaction_id,
            regression,
            max_repairs=max_repairs,
            auto_rollback_on_exhaustion=True,
        )

        if repair["status"] != "repair_validated":
            return {
                "status": repair["status"],
                "transaction_id":
                    transaction.transaction_id,
                "repair": repair,
            }

        # A repair after regression failure must be followed by another
        # full regression. A targeted repair success is not sufficient.
        regression = run_transaction_command(
            transaction.transaction_id,
            plan.regression_command,
            mark_as="regression",
        )

        if regression.returncode != 0:
            return {
                "status": "regression_failed",
                "transaction_id":
                    transaction.transaction_id,
                "record": regression,
            }

    detect_changed_paths(
        transaction.transaction_id
    )

    refresh_transaction_diff(
        transaction.transaction_id
    )

    gate = completion_gate(
        transaction.transaction_id
    )

    review = review_transaction(
        transaction.transaction_id
    )

    transaction = load_transaction(
        transaction.transaction_id
    )

    transaction.metadata[
        "engineering_plan"
    ] = {
        "confidence":
            plan.confidence,
        "rationale":
            plan.rationale,
        "documentation_note":
            plan.documentation_note,
        "commit_message":
            plan.commit_message,
    }

    transaction.status = (
        "awaiting_commit_approval"
        if gate["ready"]
        else "review_blocked"
    )

    save_transaction(
        transaction
    )

    return {
        "status":
            transaction.status,

        "transaction_id":
            transaction.transaction_id,

        "completion_gate":
            gate,

        "review":
            review,

        "suggested_commit_message":
            plan.commit_message,

        "documentation_note":
            plan.documentation_note,
    }
