"""
E.V.I.E. - Self-Engineering Controller

Phase 12M / Phase 12N

Purpose:
Orchestrate the repository-level engineering pipeline built across
Phase 12H-12N.

The controller can:

1. accept an already-bounded EngineeringPlan
2. create a safe transaction
3. persist the full engineering plan immediately
4. create a safe transaction branch
5. apply planned edits
6. run targeted validation
7. invoke bounded repair on failure
8. run full regression
9. generate diff review
10. stop for explicit commit approval

It intentionally does NOT auto-approve a commit.
"""

from __future__ import annotations

from .branch import (
    create_transaction_branch,
)

from .completion import (
    completion_gate,
)

from .diff_review import (
    review_transaction,
)

from .editing import (
    write_transaction_file,
)

from .execution import (
    run_transaction_command,
)

from .repair_loop import (
    run_repair_loop,
)

from .state import (
    load_transaction,
    save_transaction,
)

from .transaction import (
    create_transaction,
    detect_changed_paths,
    refresh_transaction_diff,
)


def _persist_engineering_plan(
    transaction,
    plan,
):
    """
    Persist the complete engineering plan inside the coding transaction.

    This happens immediately after transaction creation so interrupted
    or awaiting_user transactions retain enough information to resume
    validation safely later.
    """

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

        "targeted_commands":
            plan.targeted_commands,

        "regression_command":
            plan.regression_command,
    }

    save_transaction(
        transaction
    )

    return transaction


def execute_engineering_plan(
    plan,
    *,
    root_path: str,
    branch_name: str | None = None,
    max_repairs: int = 3,
):
    """
    Execute an already-approved EngineeringPlan.

    Important safety boundaries:

    - Empty plans do nothing.
    - Transaction scope is fixed before editing.
    - Full plan metadata is persisted before branch/edit execution.
    - Targeted validation runs before regression.
    - Failed validation enters the bounded repair loop.
    - Full regression must pass before completion review.
    - This function never approves or performs the final commit.
    """

    # -----------------------------------------------------------------------
    # Validate plan scope
    # -----------------------------------------------------------------------

    if not plan.planned_paths:
        return {
            "status":
                "no_safe_plan",

            "message":
                (
                    "Engineering plan contains no "
                    "safe planned paths."
                ),

            "transaction_id":
                "",
        }


    # -----------------------------------------------------------------------
    # Create safe transaction
    # -----------------------------------------------------------------------

    transaction = create_transaction(
        repository=
            plan.repository,

        root_path=
            root_path,

        goal=
            plan.goal,

        planned_paths=
            plan.planned_paths,

        require_clean_tree=
            True,

        approval_required=
            True,
    )


    # -----------------------------------------------------------------------
    # Persist FULL engineering plan immediately
    # -----------------------------------------------------------------------
    #
    # This is critical for Phase 12N recovery.
    #
    # If validation later fails because of:
    #
    # - environment failure
    # - API/tool failure
    # - machine restart
    # - user intervention
    #
    # the persisted transaction still knows:
    #
    # - targeted validation commands
    # - full regression command
    # - commit message
    # - documentation note
    # - original rationale
    #
    # -----------------------------------------------------------------------

    _persist_engineering_plan(
        transaction,
        plan,
    )


    # -----------------------------------------------------------------------
    # Create isolated branch
    # -----------------------------------------------------------------------

    create_transaction_branch(
        transaction.transaction_id,
        branch_name=
            branch_name,
    )


    # -----------------------------------------------------------------------
    # Apply approved edits
    # -----------------------------------------------------------------------

    for edit in plan.edits:

        write_transaction_file(
            transaction.transaction_id,
            edit.path,
            edit.content,
        )


    # -----------------------------------------------------------------------
    # Refresh change state before validation
    # -----------------------------------------------------------------------

    detect_changed_paths(
        transaction.transaction_id
    )

    refresh_transaction_diff(
        transaction.transaction_id
    )


    # -----------------------------------------------------------------------
    # Targeted validation
    # -----------------------------------------------------------------------

    for command in plan.targeted_commands:

        record = run_transaction_command(
            transaction.transaction_id,
            command,
            mark_as=
                "targeted_tests",
        )


        if record.returncode != 0:

            repair = run_repair_loop(
                transaction.transaction_id,
                record,
                max_repairs=
                    max_repairs,
                auto_rollback_on_exhaustion=
                    True,
            )


            if (
                repair[
                    "status"
                ]
                != "repair_validated"
            ):
                return {
                    "status":
                        repair[
                            "status"
                        ],

                    "transaction_id":
                        transaction.transaction_id,

                    "repair":
                        repair,
                }


    # -----------------------------------------------------------------------
    # Full regression command required
    # -----------------------------------------------------------------------

    if not plan.regression_command:

        transaction = load_transaction(
            transaction.transaction_id
        )

        transaction.status = (
            "awaiting_user"
        )

        transaction.error = (
            "Engineering plan did not provide "
            "a full regression command."
        )

        save_transaction(
            transaction
        )


        return {
            "status":
                "awaiting_user",

            "transaction_id":
                transaction.transaction_id,

            "message":
                transaction.error,
        }


    # -----------------------------------------------------------------------
    # Full regression
    # -----------------------------------------------------------------------

    regression = run_transaction_command(
        transaction.transaction_id,
        plan.regression_command,
        mark_as=
            "regression",
    )


    if regression.returncode != 0:

        repair = run_repair_loop(
            transaction.transaction_id,
            regression,
            max_repairs=
                max_repairs,
            auto_rollback_on_exhaustion=
                True,
        )


        if (
            repair[
                "status"
            ]
            != "repair_validated"
        ):
            return {
                "status":
                    repair[
                        "status"
                    ],

                "transaction_id":
                    transaction.transaction_id,

                "repair":
                    repair,
            }


        # -------------------------------------------------------------------
        # A repair after a regression failure must be followed by another
        # complete regression run.
        # -------------------------------------------------------------------

        regression = run_transaction_command(
            transaction.transaction_id,
            plan.regression_command,
            mark_as=
                "regression",
        )


        if regression.returncode != 0:

            transaction = load_transaction(
                transaction.transaction_id
            )

            transaction.regression_passed = (
                False
            )

            transaction.status = (
                "regression_failed"
            )

            transaction.error = (
                regression.stderr
                or regression.stdout
                or "Full regression failed."
            )

            save_transaction(
                transaction
            )


            return {
                "status":
                    "regression_failed",

                "transaction_id":
                    transaction.transaction_id,

                "record":
                    regression,
            }


    # -----------------------------------------------------------------------
    # Refresh final repository change state
    # -----------------------------------------------------------------------

    detect_changed_paths(
        transaction.transaction_id
    )

    refresh_transaction_diff(
        transaction.transaction_id
    )


    # -----------------------------------------------------------------------
    # Completion safety gate
    # -----------------------------------------------------------------------

    gate = completion_gate(
        transaction.transaction_id
    )


    # -----------------------------------------------------------------------
    # Diff review
    # -----------------------------------------------------------------------

    review = review_transaction(
        transaction.transaction_id
    )


    # -----------------------------------------------------------------------
    # Reload final transaction state
    # -----------------------------------------------------------------------

    transaction = load_transaction(
        transaction.transaction_id
    )


    # -----------------------------------------------------------------------
    # Re-persist full engineering plan
    # -----------------------------------------------------------------------
    #
    # This keeps final transaction metadata complete even if other coding
    # stages updated metadata during validation/repair.
    # -----------------------------------------------------------------------

    _persist_engineering_plan(
        transaction,
        plan,
    )


    # Reload after metadata persistence in case save/load normalization
    # changes the stored transaction representation.
    transaction = load_transaction(
        transaction.transaction_id
    )


    # -----------------------------------------------------------------------
    # Final state
    # -----------------------------------------------------------------------

    transaction.status = (
        "awaiting_commit_approval"
        if gate[
            "ready"
        ]
        else "review_blocked"
    )


    if gate[
        "ready"
    ]:

        transaction.error = ""

    else:

        transaction.error = (
            "; ".join(
                gate[
                    "reasons"
                ]
            )
        )


    save_transaction(
        transaction
    )


    # -----------------------------------------------------------------------
    # Return review state
    # -----------------------------------------------------------------------

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