"""
E.V.I.E. - Self-Engineering Conversation Integration

Phase 12N

Purpose:
Expose the Phase 12M repository engineering system through normal E.V.I.E.
conversation while preserving two explicit gates:

Gate 1:
    read-only plan -> user approves execution

Gate 2:
    validated diff -> user approves commit

This module does not auto-commit.
"""

from __future__ import annotations

from assistant.tools.session import (
    parse_approval_response,
)

from .approval import (
    approve_and_commit_engineering_transaction,
)

from .controller import (
    execute_engineering_plan,
)

from .discovery import (
    discover_candidate_paths,
)

from .documentation import (
    build_engineering_documentation_note,
)

from .pending import (
    clear_pending_engineering,
    load_pending_engineering,
    pending_plan_from_payload,
    save_pending_plan,
    save_pending_transaction,
)

from .planner import (
    plan_engineering_change,
)

from .presentation import (
    format_engineering_plan,
    format_execution_result,
)

from .request_planner import (
    plan_coding_request,
)


DEFAULT_REPOSITORY = "E.V.-Assistant"
DEFAULT_ROOT = "."


def _handle_pending(
    user_message: str,
    pending,
):
    state = pending.get(
        "state",
        ""
    )

    approval = parse_approval_response(
        user_message
    )

    # -----------------------------------------------------------------------
    # Plan execution approval
    # -----------------------------------------------------------------------

    if state == "awaiting_execution_approval":
        if approval.decision == "reject":
            clear_pending_engineering()

            return {
                "handled":
                    True,

                "response":
                    "Self-engineering execution cancelled.",

                "follow_up":
                    approval.remainder,
            }

        if approval.decision == "approve":
            plan = pending_plan_from_payload(
                pending
            )

            result = execute_engineering_plan(
                plan,
                root_path=pending.get(
                    "root_path",
                    DEFAULT_ROOT,
                ),
            )

            if (
                result.get(
                    "status"
                )
                == "awaiting_commit_approval"
            ):
                save_pending_transaction(
                    result[
                        "transaction_id"
                    ],
                    root_path=pending.get(
                        "root_path",
                        DEFAULT_ROOT,
                    ),
                    suggested_commit_message=(
                        result.get(
                            "suggested_commit_message",
                            ""
                        )
                        or "E.V.I.E. self-engineering change"
                    ),
                )

            else:
                clear_pending_engineering()

            return {
                "handled":
                    True,

                "response":
                    format_execution_result(
                        result
                    ),

                "follow_up":
                    approval.remainder,
            }

        return {
            "handled":
                True,

            "response":
                (
                    "A self-engineering plan is waiting for execution "
                    "approval. Say yes/approve to execute it, or no/reject "
                    "to cancel it."
                ),

            "follow_up":
                "",
        }

    # -----------------------------------------------------------------------
    # Commit approval
    # -----------------------------------------------------------------------

    if state == "awaiting_commit_approval":
        request = plan_coding_request(
            user_message
        )

        explicit_commit_approval = (
            request.handled
            and request.action
            == "approve_commit"
        )

        explicit_commit_reject = (
            request.handled
            and request.action
            == "reject_commit"
        )

        # Also accept ordinary approval only because a coding commit is
        # already pending and has already passed review/regression.
        if approval.decision == "approve":
            explicit_commit_approval = True

        if approval.decision == "reject":
            explicit_commit_reject = True

        if explicit_commit_reject:
            clear_pending_engineering()

            return {
                "handled":
                    True,

                "response":
                    (
                        "Commit approval rejected. "
                        "The validated transaction remains on its branch "
                        "but will not be committed automatically."
                    ),

                "follow_up":
                    approval.remainder,
            }

        if explicit_commit_approval:
            transaction_id = pending.get(
                "transaction_id",
                "",
            )

            message = (
                (
                    pending.get(
                        "plan",
                        {}
                    )
                    or {}
                ).get(
                    "commit_message",
                    "",
                )
                or "E.V.I.E. self-engineering change"
            )

            transaction = (
                approve_and_commit_engineering_transaction(
                    transaction_id,
                    commit_message=message,
                )
            )

            note = (
                build_engineering_documentation_note(
                    transaction_id
                )
            )

            clear_pending_engineering()

            return {
                "handled":
                    True,

                "response":
                    (
                        "Self-engineering commit completed.\n"
                        f"Commit: "
                        f"{transaction.metadata.get('commit_sha', '')}\n\n"
                        "Documentation note:\n"
                        + note
                    ),

                "follow_up":
                    approval.remainder,
            }

        return {
            "handled":
                True,

            "response":
                (
                    "A validated self-engineering change is waiting for "
                    "commit approval. Say 'approve commit' to commit it "
                    "or 'reject commit' to leave it uncommitted."
                ),

            "follow_up":
                "",
        }

    return None


def handle_coding_message(
    user_message: str,
    *,
    repository: str = DEFAULT_REPOSITORY,
    root_path: str = DEFAULT_ROOT,
):
    """
    Return:
        {
            "handled": bool,
            "response": str | None,
            "follow_up": str,
        }
    """

    pending = load_pending_engineering()

    if pending is not None:
        handled = _handle_pending(
            user_message,
            pending,
        )

        if handled is not None:
            return handled

    request = plan_coding_request(
        user_message
    )

    if not request.handled:
        return {
            "handled":
                False,

            "response":
                None,

            "follow_up":
                "",
        }

    if request.action == "status":
        pending = load_pending_engineering()

        if pending is None:
            response = (
                "There is no pending self-engineering plan or commit."
            )
        else:
            response = (
                "Self-engineering state: "
                + pending.get(
                    "state",
                    "unknown",
                )
            )

        return {
            "handled":
                True,

            "response":
                response,

            "follow_up":
                "",
        }

    if request.action in {
        "approve_commit",
        "reject_commit",
    }:
        return {
            "handled":
                False,

            "response":
                None,

            "follow_up":
                "",
        }

    if request.action == "plan_change":
        candidate_paths = (
            discover_candidate_paths(
                repository,
                request.goal,
                max_candidates=8,
            )
        )

        if not candidate_paths:
            return {
                "handled":
                    True,

                "response":
                    (
                        "I could not identify a bounded set of repository "
                        "files for that engineering request, so I did not "
                        "make any changes."
                    ),

                "follow_up":
                    "",
            }

        plan = plan_engineering_change(
            goal=request.goal,
            repository=repository,
            root_path=root_path,
            candidate_paths=candidate_paths,
        )

        save_pending_plan(
            plan,
            root_path=root_path,
            candidate_paths=candidate_paths,
        )

        return {
            "handled":
                True,

            "response":
                format_engineering_plan(
                    plan,
                    candidate_paths=
                        candidate_paths,
                ),

            "follow_up":
                "",
        }

    return {
        "handled":
            False,

        "response":
            None,

        "follow_up":
            "",
    }
