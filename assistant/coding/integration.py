from __future__ import annotations

from assistant.tools.session import parse_approval_response

from .approval import (
    approve_and_commit_engineering_transaction,
)
from .controller import execute_engineering_plan
from .discovery import discover_candidate_paths
from .documentation import (
    build_engineering_documentation_note,
)
from .pending import (
    clear_pending_engineering,
    load_pending_engineering,
    pending_plan_from_payload,
    save_pending_plan,
    save_pending_recovery,
    save_pending_transaction,
)
from .planner import plan_engineering_change
from .presentation import (
    format_engineering_plan,
    format_execution_result,
)
from .recovery import (
    find_latest_recoverable_transaction,
    resume_engineering_transaction,
)
from .request_planner import plan_coding_request


DEFAULT_REPOSITORY = "E.V.-Assistant"
DEFAULT_ROOT = "."


def _result_to_pending_state(
    result,
    *,
    root_path: str,
):
    status = result.get("status", "")
    transaction_id = result.get(
        "transaction_id",
        "",
    )

    if not transaction_id:
        clear_pending_engineering()
        return

    if status == "awaiting_commit_approval":
        save_pending_transaction(
            transaction_id,
            root_path=root_path,
            suggested_commit_message=(
                result.get(
                    "suggested_commit_message",
                    "",
                )
                or "E.V.I.E. self-engineering change"
            ),
        )
        return

    if status in {
        "awaiting_user",
        "validation_failed",
        "repair_exhausted",
        "regression_failed",
    }:
        save_pending_recovery(
            transaction_id,
            root_path=root_path,
        )
        return

    clear_pending_engineering()


def _resume_transaction(
    transaction_id: str,
    *,
    root_path: str,
):
    result = resume_engineering_transaction(
        transaction_id
    )

    _result_to_pending_state(
        result,
        root_path=root_path,
    )

    return {
        "handled": True,
        "response": format_execution_result(
            result
        ),
        "follow_up": "",
    }


def _handle_pending(
    user_message: str,
    pending,
):
    state = pending.get(
        "state",
        "",
    )

    approval = parse_approval_response(
        user_message
    )

    if state == "awaiting_execution_approval":
        if approval.decision == "reject":
            clear_pending_engineering()

            return {
                "handled": True,
                "response": (
                    "Self-engineering execution "
                    "cancelled."
                ),
                "follow_up": approval.remainder,
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

            _result_to_pending_state(
                result,
                root_path=pending.get(
                    "root_path",
                    DEFAULT_ROOT,
                ),
            )

            return {
                "handled": True,
                "response": format_execution_result(
                    result
                ),
                "follow_up": approval.remainder,
            }

        return {
            "handled": True,
            "response": (
                "A self-engineering plan is waiting "
                "for execution approval. Say "
                "yes/approve to execute it, or "
                "no/reject to cancel it."
            ),
            "follow_up": "",
        }

    if state == "awaiting_recovery":
        request = plan_coding_request(
            user_message
        )

        wants_resume = (
            request.handled
            and request.action
            == "resume_transaction"
        )

        if approval.decision == "approve":
            wants_resume = True

        if approval.decision == "reject":
            clear_pending_engineering()

            return {
                "handled": True,
                "response": (
                    "Self-engineering recovery "
                    "cancelled. The transaction "
                    "remains persisted on its branch."
                ),
                "follow_up": approval.remainder,
            }

        if wants_resume:
            return _resume_transaction(
                pending.get(
                    "transaction_id",
                    "",
                ),
                root_path=pending.get(
                    "root_path",
                    DEFAULT_ROOT,
                ),
            )

        return {
            "handled": True,
            "response": (
                "A self-engineering transaction is "
                "paused and waiting for recovery. "
                "Say 'continue the pending "
                "self-engineering transaction' "
                "after the external issue is fixed."
            ),
            "follow_up": "",
        }

    if state == "awaiting_commit_approval":
        request = plan_coding_request(
            user_message
        )

        commit_yes = (
            request.handled
            and request.action
            == "approve_commit"
        )

        commit_no = (
            request.handled
            and request.action
            == "reject_commit"
        )

        if approval.decision == "approve":
            commit_yes = True

        if approval.decision == "reject":
            commit_no = True

        if commit_no:
            clear_pending_engineering()

            return {
                "handled": True,
                "response": (
                    "Commit approval rejected. "
                    "The validated transaction "
                    "remains on its branch."
                ),
                "follow_up": approval.remainder,
            }

        if commit_yes:
            transaction_id = pending.get(
                "transaction_id",
                "",
            )

            message = (
                (
                    pending.get(
                        "plan",
                        {},
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
                "handled": True,
                "response": (
                    "Self-engineering commit "
                    "completed.\n"
                    f"Commit: "
                    f"{transaction.metadata.get('commit_sha', '')}"
                    "\n\nDocumentation note:\n"
                    + note
                ),
                "follow_up": approval.remainder,
            }

        return {
            "handled": True,
            "response": (
                "A validated self-engineering change "
                "is waiting for commit approval. "
                "Say 'approve commit' to commit it "
                "or 'reject commit' to leave it "
                "uncommitted."
            ),
            "follow_up": "",
        }

    return None


def handle_coding_message(
    user_message: str,
    *,
    repository: str = DEFAULT_REPOSITORY,
    root_path: str = DEFAULT_ROOT,
):
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
            "handled": False,
            "response": None,
            "follow_up": "",
        }

    if request.action == "resume_transaction":
        transaction = (
            find_latest_recoverable_transaction()
        )

        if transaction is None:
            return {
                "handled": True,
                "response": (
                    "There is no recoverable "
                    "self-engineering transaction."
                ),
                "follow_up": "",
            }

        return _resume_transaction(
            transaction.transaction_id,
            root_path=transaction.root_path,
        )

    if request.action == "status":
        transaction = (
            find_latest_recoverable_transaction()
        )

        if transaction is None:
            response = (
                "There is no pending or recoverable "
                "self-engineering transaction."
            )
        else:
            response = (
                "Recoverable self-engineering "
                f"transaction: "
                f"{transaction.transaction_id} "
                f"[{transaction.status}]"
            )

        return {
            "handled": True,
            "response": response,
            "follow_up": "",
        }

    if request.action in {
        "approve_commit",
        "reject_commit",
    }:
        return {
            "handled": False,
            "response": None,
            "follow_up": "",
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
                "handled": True,
                "response": (
                    "I could not identify a bounded "
                    "set of repository files for "
                    "that engineering request."
                ),
                "follow_up": "",
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
            "handled": True,
            "response": format_engineering_plan(
                plan,
                candidate_paths=candidate_paths,
            ),
            "follow_up": "",
        }

    return {
        "handled": False,
        "response": None,
        "follow_up": "",
    }
