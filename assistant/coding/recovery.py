"""
E.V.I.E. - Self-Engineering Transaction Recovery

Phase 12N Final

Purpose:
Resume a persisted coding transaction that paused because validation,
regression, or an external environment problem required user intervention.

This module never commits automatically.
"""

from __future__ import annotations

from pathlib import Path
import shlex

from . import state as coding_state

from .completion import (
    completion_gate,
)

from .diff_review import (
    review_transaction,
)

from .execution import (
    run_transaction_command,
)

from .git_review import (
    current_branch,
)

from .repair_loop import (
    run_repair_loop,
)

from .transaction import (
    detect_changed_paths,
    refresh_transaction_diff,
)


RECOVERABLE_STATUSES = {
    "awaiting_user",
    "validation_failed",
    "repair_exhausted",
    "regression_failed",
}


# ---------------------------------------------------------------------------
# Command Helpers
# ---------------------------------------------------------------------------

def _normalize_command(
    command,
):
    if isinstance(
        command,
        (
            list,
            tuple,
        ),
    ):
        return [
            str(
                part
            )
            for part
            in command
        ]

    value = str(
        command
        or ""
    ).strip()

    if not value:
        return []

    try:
        return shlex.split(
            value,
            posix=False,
        )

    except ValueError:
        return value.split()


def _plan_metadata(
    transaction,
):
    return (
        transaction.metadata.get(
            "engineering_plan",
            {},
        )
        or {}
    )


def _targeted_commands(
    transaction,
):
    """
    Prefer validation commands persisted in the EngineeringPlan.

    Older Phase 12N transactions may not have them, so fall back to
    commands already attempted by the transaction.
    """

    commands = (
        _plan_metadata(
            transaction
        ).get(
            "targeted_commands",
            [],
        )
        or []
    )

    normalized = [
        _normalize_command(
            command
        )
        for command
        in commands
    ]

    normalized = [
        command
        for command
        in normalized
        if command
    ]

    if normalized:
        return normalized


    # -----------------------------------------------------------------------
    # Backward compatibility
    # -----------------------------------------------------------------------

    fallback = []

    for record in transaction.commands:

        command = _normalize_command(
            record.command
        )

        if (
            command
            and command
            not in fallback
        ):
            fallback.append(
                command
            )

    return fallback


def _regression_command(
    transaction,
):
    """
    Read the original full-regression command when available.

    Older transactions safely fall back to the project's standard full
    pytest regression.
    """

    command = _normalize_command(
        _plan_metadata(
            transaction
        ).get(
            "regression_command",
            [],
        )
    )

    if command:
        return command

    return [
        "python",
        "-m",
        "pytest",
        "-q",
    ]


# ---------------------------------------------------------------------------
# Persisted Transaction Discovery
# ---------------------------------------------------------------------------

def _transaction_files():
    """
    Read TRANSACTION_RUNTIME dynamically.

    This is intentionally referenced through coding_state rather than
    imported as a module-level constant so pytest monkeypatching and future
    runtime relocation work correctly.
    """

    directory = Path(
        coding_state.TRANSACTION_RUNTIME
    )

    if not directory.exists():
        return []

    return sorted(
        directory.glob(
            "*.json"
        ),
        key=lambda path:
            path.stat().st_mtime,
        reverse=True,
    )


def find_latest_recoverable_transaction():
    """
    Return the newest persisted recoverable CodingTransaction.
    """

    for path in _transaction_files():

        transaction_id = (
            path.stem
        )

        try:
            transaction = (
                coding_state.load_transaction(
                    transaction_id
                )
            )

        except Exception:
            continue

        if transaction is None:
            continue

        if (
            transaction.status
            in RECOVERABLE_STATUSES
        ):
            return transaction

    return None


# ---------------------------------------------------------------------------
# Pause Helper
# ---------------------------------------------------------------------------

def _pause(
    transaction,
    message: str,
):
    transaction.status = (
        "awaiting_user"
    )

    transaction.error = (
        message
    )

    coding_state.save_transaction(
        transaction
    )

    return {
        "status":
            "awaiting_user",

        "transaction_id":
            transaction.transaction_id,

        "message":
            message,
    }


# ---------------------------------------------------------------------------
# Recovery Execution
# ---------------------------------------------------------------------------

def resume_engineering_transaction(
    transaction_id: str,
    *,
    max_repairs: int = 3,
):
    """
    Resume one persisted self-engineering transaction.

    Flow:

        verify recoverable state
            ->
        verify branch
            ->
        rerun targeted validation
            ->
        bounded repair if necessary
            ->
        run full regression
            ->
        bounded repair if necessary
            ->
        refresh diff
            ->
        completion gate
            ->
        awaiting_commit_approval

    No commit occurs here.
    """

    transaction = (
        coding_state.load_transaction(
            transaction_id
        )
    )

    if transaction is None:
        raise RuntimeError(
            (
                "Coding transaction does not exist: "
                f"{transaction_id}"
            )
        )


    # -----------------------------------------------------------------------
    # Validate state
    # -----------------------------------------------------------------------

    if (
        transaction.status
        not in RECOVERABLE_STATUSES
    ):
        raise RuntimeError(
            (
                "Coding transaction is not recoverable "
                "from status: "
                f"{transaction.status}"
            )
        )


    # -----------------------------------------------------------------------
    # Verify current branch
    # -----------------------------------------------------------------------

    branch = current_branch(
        transaction.root_path
    )

    if (
        transaction.working_branch
        and branch
        != transaction.working_branch
    ):
        return _pause(
            transaction,
            (
                "The repository is on the wrong branch "
                "for recovery. "
                f"Expected {transaction.working_branch}, "
                f"got {branch}."
            ),
        )


    # -----------------------------------------------------------------------
    # Resolve validation commands
    # -----------------------------------------------------------------------

    targeted_commands = (
        _targeted_commands(
            transaction
        )
    )

    if not targeted_commands:
        return _pause(
            transaction,
            (
                "No targeted validation commands are "
                "persisted for this transaction, so "
                "recovery cannot continue safely."
            ),
        )


    regression_command = (
        _regression_command(
            transaction
        )
    )


    # -----------------------------------------------------------------------
    # Enter recovering state
    # -----------------------------------------------------------------------

    transaction.status = (
        "recovering"
    )

    transaction.error = ""

    coding_state.save_transaction(
        transaction
    )


    # -----------------------------------------------------------------------
    # Targeted validation
    # -----------------------------------------------------------------------

    for command in targeted_commands:

        record = run_transaction_command(
            transaction_id,
            command,
            mark_as=
                "targeted_tests",
        )


        if record.returncode != 0:

            repair = run_repair_loop(
                transaction_id,
                record,
                max_repairs=
                    max_repairs,
                auto_rollback_on_exhaustion=
                    True,
            )


            if (
                repair.get(
                    "status"
                )
                != "repair_validated"
            ):
                return {
                    "status":
                        repair.get(
                            "status",
                            "awaiting_user",
                        ),

                    "transaction_id":
                        transaction_id,

                    "repair":
                        repair,
                }


    # -----------------------------------------------------------------------
    # Targeted validation succeeded
    # -----------------------------------------------------------------------

    transaction = (
        coding_state.load_transaction(
            transaction_id
        )
    )

    transaction.targeted_tests_passed = (
        True
    )

    transaction.error = ""

    coding_state.save_transaction(
        transaction
    )


    # -----------------------------------------------------------------------
    # Full regression
    # -----------------------------------------------------------------------

    regression = run_transaction_command(
        transaction_id,
        regression_command,
        mark_as=
            "regression",
    )


    if regression.returncode != 0:

        repair = run_repair_loop(
            transaction_id,
            regression,
            max_repairs=
                max_repairs,
            auto_rollback_on_exhaustion=
                True,
        )


        if (
            repair.get(
                "status"
            )
            != "repair_validated"
        ):
            return {
                "status":
                    repair.get(
                        "status",
                        "awaiting_user",
                    ),

                "transaction_id":
                    transaction_id,

                "repair":
                    repair,
            }


        # -------------------------------------------------------------------
        # Any regression repair must be followed by another complete
        # regression run.
        # -------------------------------------------------------------------

        regression = run_transaction_command(
            transaction_id,
            regression_command,
            mark_as=
                "regression",
        )


        if regression.returncode != 0:

            transaction = (
                coding_state.load_transaction(
                    transaction_id
                )
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

            coding_state.save_transaction(
                transaction
            )


            return {
                "status":
                    "regression_failed",

                "transaction_id":
                    transaction_id,

                "record":
                    regression,
            }


    # -----------------------------------------------------------------------
    # Regression succeeded
    # -----------------------------------------------------------------------

    transaction = (
        coding_state.load_transaction(
            transaction_id
        )
    )

    transaction.regression_passed = (
        True
    )

    transaction.error = ""

    coding_state.save_transaction(
        transaction
    )


    # -----------------------------------------------------------------------
    # Refresh repository state
    # -----------------------------------------------------------------------

    detect_changed_paths(
        transaction_id
    )

    refresh_transaction_diff(
        transaction_id
    )


    # -----------------------------------------------------------------------
    # Completion gate
    # -----------------------------------------------------------------------

    gate = completion_gate(
        transaction_id
    )


    # -----------------------------------------------------------------------
    # Diff review
    # -----------------------------------------------------------------------

    review = review_transaction(
        transaction_id
    )


    # -----------------------------------------------------------------------
    # Final persisted state
    # -----------------------------------------------------------------------

    transaction = (
        coding_state.load_transaction(
            transaction_id
        )
    )


    if gate[
        "ready"
    ]:

        transaction.status = (
            "awaiting_commit_approval"
        )

        transaction.error = ""

    else:

        transaction.status = (
            "review_blocked"
        )

        transaction.error = (
            "; ".join(
                gate[
                    "reasons"
                ]
            )
        )


    coding_state.save_transaction(
        transaction
    )


    metadata = (
        _plan_metadata(
            transaction
        )
    )


    return {
        "status":
            transaction.status,

        "transaction_id":
            transaction_id,

        "completion_gate":
            gate,

        "review":
            review,

        "suggested_commit_message":
            (
                metadata.get(
                    "commit_message",
                    "",
                )
                or "E.V.I.E. self-engineering change"
            ),

        "documentation_note":
            metadata.get(
                "documentation_note",
                "",
            ),
    }