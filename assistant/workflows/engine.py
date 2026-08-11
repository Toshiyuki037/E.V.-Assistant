"""
E.V.I.E. - Workflow Engine

Phase 11A / 11B / 11C / 11D

Adds:
- request-user recovery
- bounded replanning
- persistent awaiting-user state
- user recovery actions
"""

from __future__ import annotations

import time

from copy import deepcopy

from assistant.intelligence.context import (
    record_tool_context,
)

from assistant.intelligence.integration_runtime import (
    prepare_tool_arguments,
)

from assistant.tools.executor import (
    execute_tool,
)

from assistant.tools.verifier import (
    verify_tool_result,
)

from .audit import (
    record_audit_event,
)

from .conditions import (
    evaluate_condition,
)

from .data import (
    WorkflowReferenceError,
    apply_input_bindings,
)

from .models import (
    RUN_AWAITING_APPROVAL,
    RUN_AWAITING_USER,
    RUN_CANCELLED,
    RUN_COMPLETED,
    RUN_FAILED,
    RUN_RUNNING,
    STEP_AWAITING_APPROVAL,
    STEP_AWAITING_USER,
    STEP_CANCELLED,
    STEP_COMPLETED,
    STEP_FAILED,
    STEP_PENDING,
    STEP_READY,
    STEP_RUNNING,
    STEP_SKIPPED,
    WorkflowRun,
)

from .replanner import (
    propose_workflow_repair,
)

from .state import (
    archive_run,
    now_string,
    save_run,
)


def get_step_map(
    run: WorkflowRun,
):
    return {
        step.step_id:
            step
        for step
        in run.steps
    }


def dependencies_satisfied(
    run: WorkflowRun,
    step,
):
    if not step.dependencies:

        return True


    step_map = (
        get_step_map(
            run
        )
    )


    for dependency_id in (
        step.dependencies
    ):

        dependency = (
            step_map.get(
                dependency_id
            )
        )


        if dependency is None:

            return False


        if dependency.status not in {
            STEP_COMPLETED,
            STEP_SKIPPED,
        }:

            return False


    return True


def all_steps_completed(
    run: WorkflowRun,
):
    return all(
        step.status in {
            STEP_COMPLETED,
            STEP_SKIPPED,
        }
        for step
        in run.steps
    )


def find_next_ready_step(
    run: WorkflowRun,
):
    for step in run.steps:

        if step.status not in {
            STEP_PENDING,
            STEP_READY,
        }:

            continue


        if dependencies_satisfied(
            run,
            step,
        ):

            return step


    return None


def mark_run_failed(
    run: WorkflowRun,
    reason: str,
):
    run.status = (
        RUN_FAILED
    )

    run.failure_reason = (
        str(
            reason
            or "Workflow failed."
        )
    )

    run.completed_at = (
        now_string()
    )


    save_run(
        run
    )


    record_audit_event(
        run.run_id,
        "run_failed",

        workflow_id=
            run.workflow_id,

        message=
            run.failure_reason,
    )


    archive_run(
        run
    )


    return run


def mark_run_completed(
    run: WorkflowRun,
):
    run.status = (
        RUN_COMPLETED
    )

    run.completed_at = (
        now_string()
    )

    run.awaiting_user_reason = ""

    run.recovery_context = {}


    if not run.final_summary:

        run.final_summary = (
            "Workflow completed successfully."
        )


    save_run(
        run
    )


    record_audit_event(
        run.run_id,
        "run_completed",

        workflow_id=
            run.workflow_id,

        message=
            run.final_summary,
    )


    archive_run(
        run
    )


    return run


def resolve_step_arguments(
    run: WorkflowRun,
    step,
):
    arguments = deepcopy(
        step.arguments
    )


    arguments = (
        apply_input_bindings(
            arguments,
            step.input_bindings,
            run,
        )
    )


    return prepare_tool_arguments(
        step.tool_name,
        arguments,
    )


def should_run_step(
    run: WorkflowRun,
    step,
):
    return evaluate_condition(
        step.condition,
        run,
    )


def skip_step(
    run: WorkflowRun,
    step,
    reason: str = (
        "Condition evaluated to false."
    ),
):
    step.status = (
        STEP_SKIPPED
    )

    step.result = {
        "skipped":
            True,

        "reason":
            reason,
    }

    step.error = None

    step.completed_at = (
        now_string()
    )


    save_run(
        run
    )


    record_audit_event(
        run.run_id,
        "step_skipped",

        workflow_id=
            run.workflow_id,

        step_id=
            step.step_id,

        message=
            reason,
    )


    return step


def execute_workflow_step(
    run: WorkflowRun,
    step,
    approved: bool = False,
):
    try:

        if not should_run_step(
            run,
            step,
        ):

            skip_step(
                run,
                step,
            )

            return (
                "skipped",
                None,
            )


    except Exception as error:

        step.status = STEP_FAILED
        step.error = (
            f"Workflow condition failed: {error}"
        )
        step.completed_at = now_string()
        save_run(run)

        return (
            "failed",
            None,
        )


    try:

        arguments = resolve_step_arguments(
            run,
            step,
        )


    except WorkflowReferenceError as error:

        step.status = STEP_FAILED
        step.error = str(error)
        step.completed_at = now_string()
        save_run(run)

        return (
            "failed",
            None,
        )


    step.arguments = arguments
    step.status = STEP_RUNNING
    step.attempts += 1
    step.last_attempt_at = now_string()

    if not step.started_at:
        step.started_at = step.last_attempt_at

    save_run(run)


    record_audit_event(
        run.run_id,
        "step_started",

        workflow_id=
            run.workflow_id,

        step_id=
            step.step_id,

        message=
            step.description,

        data={
            "attempt":
                step.attempts,

            "tool":
                step.tool_name,
        },
    )


    execution = execute_tool(
        tool_name=
            step.tool_name,

        arguments=
            arguments,

        approved=
            approved,
    )


    if execution.get(
        "requires_approval",
        False,
    ):

        step.status = (
            STEP_AWAITING_APPROVAL
        )

        run.status = (
            RUN_AWAITING_APPROVAL
        )

        run.pending_action = {
            "step_id":
                step.step_id,

            "step_number":
                step.step_number,

            "tool_name":
                step.tool_name,

            "arguments":
                arguments,

            "risk":
                execution.get(
                    "risk"
                ),

            "description":
                step.description,
        }

        save_run(run)


        record_audit_event(
            run.run_id,
            "approval_required",

            workflow_id=
                run.workflow_id,

            step_id=
                step.step_id,

            message=
                step.description,

            data={
                "risk":
                    execution.get(
                        "risk"
                    )
            },
        )


        return (
            "approval_required",
            execution,
        )


    verification = verify_tool_result(
        execution
    )

    step.result = execution


    if verification.successful:

        step.status = STEP_COMPLETED
        step.error = None
        step.completed_at = now_string()

        if step.output_key:
            run.outputs[
                step.output_key
            ] = execution.get(
                "result"
            )

        record_tool_context(
            tool_name=
                step.tool_name,

            arguments=
                arguments,

            user_request=
                run.goal,
        )

        save_run(run)


        record_audit_event(
            run.run_id,
            "step_completed",

            workflow_id=
                run.workflow_id,

            step_id=
                step.step_id,

            message=
                step.description,

            data={
                "attempts":
                    step.attempts,

                "output_key":
                    step.output_key,
            },
        )


        return (
            "completed",
            execution,
        )


    step.status = STEP_FAILED
    step.error = verification.summary
    step.completed_at = now_string()
    save_run(run)


    record_audit_event(
        run.run_id,
        "step_failed",

        workflow_id=
            run.workflow_id,

        step_id=
            step.step_id,

        message=
            step.error,

        data={
            "attempts":
                step.attempts
        },
    )


    return (
        "failed",
        execution,
    )


def _retry_matches(
    step,
):
    retry_on = (
        step.retry_policy
        .retry_on
        or []
    )


    if not retry_on:

        return True


    error_text = (
        str(
            step.error
            or ""
        )
        .lower()
    )


    return any(
        str(
            fragment
        )
        .lower()
        in error_text

        for fragment
        in retry_on
    )


def pause_for_user(
    run: WorkflowRun,
    step,
    reason: str,
    *,
    recovery_context: dict | None = None,
):
    step.status = (
        STEP_AWAITING_USER
    )

    step.recovery_note = (
        reason
    )

    run.status = (
        RUN_AWAITING_USER
    )

    run.awaiting_user_reason = (
        reason
    )

    run.recovery_context = (
        recovery_context
        if isinstance(
            recovery_context,
            dict,
        )
        else {}
    )


    save_run(
        run
    )


    record_audit_event(
        run.run_id,
        "user_action_required",

        workflow_id=
            run.workflow_id,

        step_id=
            step.step_id,

        message=
            reason,

        data=
            run.recovery_context,
    )


    return run


def apply_repair_plan(
    run: WorkflowRun,
    step,
    repair: dict,
):
    action = (
        str(
            repair.get(
                "action",
                "stop",
            )
            or "stop"
        )
        .strip()
        .lower()
    )


    reason = (
        str(
            repair.get(
                "reason",
                "",
            )
            or ""
        )
    )


    record_audit_event(
        run.run_id,
        "replan_decision",

        workflow_id=
            run.workflow_id,

        step_id=
            step.step_id,

        message=
            reason,

        data={
            "action":
                action,

            "replan_count":
                run.replan_count,
        },
    )


    if action == "retry":

        step.status = STEP_PENDING
        step.error = None
        step.completed_at = ""
        step.recovery_note = reason

        save_run(run)

        return "continue"


    if action == "replace":

        tool_name = (
            str(
                repair.get(
                    "tool_name",
                    ""
                )
                or ""
            )
            .strip()
        )


        arguments = (
            repair.get(
                "arguments",
                {}
            )
        )


        if (
            not tool_name
            or not isinstance(
                arguments,
                dict,
            )
        ):

            return "stop"


        step.tool_name = tool_name
        step.arguments = arguments
        step.status = STEP_PENDING
        step.error = None
        step.completed_at = ""
        step.recovery_note = reason

        save_run(run)

        return "continue"


    if action == "request_user":

        user_message = (
            str(
                repair.get(
                    "user_message",
                    ""
                )
                or reason
                or (
                    "User input is required "
                    "to continue this workflow."
                )
            )
        )


        pause_for_user(
            run,
            step,
            user_message,

            recovery_context={
                "source":
                    "replan",

                "failed_step":
                    step.step_id,
            },
        )


        return "pause"


    return "stop"


def handle_failed_step(
    run: WorkflowRun,
    step,
):
    policy = (
        step.retry_policy
    )


    max_attempts = max(
        1,
        int(
            policy.max_attempts
            or 1
        ),
    )


    if (
        policy.failure_behavior
        == "retry"
        and step.attempts
        < max_attempts
        and _retry_matches(
            step
        )
    ):

        delay = max(
            0,
            int(
                policy.retry_delay_seconds
                or 0
            ),
        )


        record_audit_event(
            run.run_id,
            "retry_scheduled",

            workflow_id=
                run.workflow_id,

            step_id=
                step.step_id,

            message=(
                f"Retrying step after "
                f"{delay} second(s)."
            ),
        )


        if delay:

            time.sleep(
                delay
            )


        step.status = STEP_PENDING
        step.error = None
        step.completed_at = ""

        save_run(run)

        return "retry"


    if (
        policy.failure_behavior
        == "skip_step"
    ):

        skip_step(
            run,
            step,
            reason=(
                "Failure policy skipped "
                "this step."
            ),
        )

        return "continue"


    if (
        policy.failure_behavior
        == "request_user"
    ):

        pause_for_user(
            run,
            step,
            (
                step.error
                or (
                    "User action is required "
                    "to continue."
                )
            ),

            recovery_context={
                "source":
                    "failure_policy",

                "failed_step":
                    step.step_id,
            },
        )

        return "pause"


    if (
        policy.failure_behavior
        == "replan"
    ):

        if (
            run.replan_count
            >= max(
                0,
                run.max_replans,
            )
        ):

            record_audit_event(
                run.run_id,
                "replan_limit_reached",

                workflow_id=
                    run.workflow_id,

                step_id=
                    step.step_id,

                message=(
                    "Maximum workflow replans "
                    "reached."
                ),
            )

            return "fail"


        run.replan_count += 1
        save_run(run)


        try:

            repair = (
                propose_workflow_repair(
                    run,
                    step,
                )
            )


        except Exception as error:

            pause_for_user(
                run,
                step,
                (
                    "Automatic workflow repair "
                    f"failed: {error}"
                ),

                recovery_context={
                    "source":
                        "replanner_error",

                    "failed_step":
                        step.step_id,
                },
            )

            return "pause"


        return apply_repair_plan(
            run,
            step,
            repair,
        )


    return "fail"


def run_workflow_engine(
    run: WorkflowRun,
):
    if not run.started_at:

        run.started_at = now_string()

        record_audit_event(
            run.run_id,
            "run_started",

            workflow_id=
                run.workflow_id,

            message=
                run.goal,
        )

    else:

        run.resume_count += 1

        record_audit_event(
            run.run_id,
            "run_resumed",

            workflow_id=
                run.workflow_id,

            message=(
                "Workflow execution resumed."
            ),

            data={
                "resume_count":
                    run.resume_count
            },
        )


    run.status = RUN_RUNNING
    run.awaiting_user_reason = ""
    run.recovery_context = {}

    save_run(run)


    while True:

        if all_steps_completed(
            run
        ):

            return mark_run_completed(
                run
            )


        step = find_next_ready_step(
            run
        )


        if step is None:

            failed_step = next(
                (
                    item
                    for item
                    in run.steps
                    if item.status
                    == STEP_FAILED
                ),
                None,
            )


            if failed_step is not None:

                return mark_run_failed(
                    run,
                    (
                        failed_step.error
                        or (
                            "A workflow step "
                            "failed."
                        )
                    ),
                )


            return mark_run_failed(
                run,
                (
                    "No runnable workflow step "
                    "remained. Check dependencies."
                ),
            )


        status, _ = (
            execute_workflow_step(
                run,
                step,
                approved=False,
            )
        )


        if status == "approval_required":

            return run


        if status == "skipped":

            continue


        if status == "failed":

            failure_action = (
                handle_failed_step(
                    run,
                    step,
                )
            )


            if failure_action in {
                "retry",
                "continue",
            }:

                continue


            if failure_action == "pause":

                return run


            return mark_run_failed(
                run,
                (
                    step.error
                    or (
                        "Workflow step "
                        "failed."
                    )
                ),
            )


def resolve_workflow_approval(
    run: WorkflowRun,
    approved: bool,
):
    pending = run.pending_action

    if not pending:
        return run

    step_id = pending.get(
        "step_id"
    )

    step = next(
        (
            item
            for item
            in run.steps
            if item.step_id
            == step_id
        ),
        None,
    )


    if step is None:

        return mark_run_failed(
            run,
            (
                "Pending workflow step "
                "could not be found."
            ),
        )


    if not approved:

        step.status = STEP_CANCELLED
        step.error = (
            "Action rejected by user."
        )

        run.pending_action = None
        run.status = RUN_CANCELLED
        run.failure_reason = (
            "Workflow cancelled because "
            "the pending action was rejected."
        )
        run.completed_at = now_string()

        save_run(run)
        archive_run(run)

        return run


    run.pending_action = None

    status, _ = execute_workflow_step(
        run,
        step,
        approved=True,
    )


    if status == "failed":

        return mark_run_failed(
            run,
            (
                step.error
                or (
                    "Approved workflow "
                    "action failed."
                )
            ),
        )


    if status == "approval_required":

        return run


    return run_workflow_engine(
        run
    )


def resolve_user_recovery(
    run: WorkflowRun,
    action: str,
):
    action = (
        str(
            action
            or ""
        )
        .strip()
        .lower()
    )


    step = next(
        (
            item
            for item
            in run.steps
            if item.status
            == STEP_AWAITING_USER
        ),
        None,
    )


    if step is None:

        return run


    if action == "retry":

        step.status = STEP_PENDING
        step.error = None
        step.completed_at = ""
        step.recovery_note = ""

        run.status = RUN_RUNNING
        run.awaiting_user_reason = ""
        run.recovery_context = {}

        save_run(run)

        record_audit_event(
            run.run_id,
            "user_retry",

            workflow_id=
                run.workflow_id,

            step_id=
                step.step_id,
        )

        return run_workflow_engine(
            run
        )


    if action == "skip":

        skip_step(
            run,
            step,
            reason=(
                "Step skipped by user "
                "during recovery."
            ),
        )

        run.status = RUN_RUNNING
        run.awaiting_user_reason = ""
        run.recovery_context = {}

        save_run(run)

        record_audit_event(
            run.run_id,
            "user_skip",

            workflow_id=
                run.workflow_id,

            step_id=
                step.step_id,
        )

        return run_workflow_engine(
            run
        )


    if action == "cancel":

        step.status = STEP_CANCELLED

        run.status = RUN_CANCELLED
        run.failure_reason = (
            "Workflow cancelled by user "
            "during recovery."
        )
        run.awaiting_user_reason = ""
        run.recovery_context = {}
        run.completed_at = now_string()

        save_run(run)
        archive_run(run)

        return run


    return run
