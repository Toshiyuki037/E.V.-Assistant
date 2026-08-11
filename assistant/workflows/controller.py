"""
E.V.I.E. - Workflow Controller

Phase 11A / 11B / 11C / 11D
"""

from __future__ import annotations

from copy import deepcopy

from uuid import uuid4

from .audit import (
    load_audit_events,
    record_audit_event,
)

from .engine import (
    resolve_user_recovery,
    resolve_workflow_approval,
    run_workflow_engine,
)

from .models import (
    RUN_AWAITING_USER,
    RUN_CANCELLED,
    WorkflowDefinition,
    WorkflowRetryPolicy,
    WorkflowRun,
    WorkflowStep,
)

from .recovery import (
    recover_active_runs,
    repair_interrupted_run,
)

from .state import (
    archive_run,
    list_active_runs,
    list_definitions,
    load_definition,
    load_run,
    now_string,
    save_definition,
    save_run,
)

from .validation import (
    validate_workflow_definition,
)


def new_workflow_id():
    return (
        "wf_"
        + uuid4().hex[
            :12
        ]
    )


def new_run_id():
    return (
        "run_"
        + uuid4().hex[
            :12
        ]
    )


def normalize_retry_policy(
    value,
):
    if isinstance(
        value,
        WorkflowRetryPolicy,
    ):

        return deepcopy(
            value
        )


    if isinstance(
        value,
        dict,
    ):

        return WorkflowRetryPolicy(
            max_attempts=int(
                value.get(
                    "max_attempts",
                    1,
                )
                or 1
            ),

            retry_delay_seconds=int(
                value.get(
                    "retry_delay_seconds",
                    0,
                )
                or 0
            ),

            failure_behavior=str(
                value.get(
                    "failure_behavior",
                    "stop_workflow",
                )
                or "stop_workflow"
            ),

            retry_on=[
                str(
                    item
                )
                for item
                in (
                    value.get(
                        "retry_on",
                        [],
                    )
                    or []
                )
            ],
        )


    return WorkflowRetryPolicy()


def normalize_steps(
    steps,
):
    normalized = []


    for index, step in enumerate(
        steps,
        start=1,
    ):

        if isinstance(
            step,
            WorkflowStep,
        ):

            item = deepcopy(
                step
            )


        elif isinstance(
            step,
            dict,
        ):

            item = WorkflowStep(
                step_id=str(
                    step.get(
                        "step_id",
                        f"step_{index}",
                    )
                    or f"step_{index}"
                ),

                step_number=
                    index,

                description=str(
                    step.get(
                        "description",
                        "",
                    )
                    or ""
                ),

                tool_name=str(
                    step.get(
                        "tool_name",
                        "",
                    )
                    or ""
                ),

                arguments=deepcopy(
                    (
                        step.get(
                            "arguments",
                            {},
                        )
                        if isinstance(
                            step.get(
                                "arguments",
                                {},
                            ),
                            dict,
                        )
                        else {}
                    )
                ),

                dependencies=[
                    str(
                        value
                    )
                    for value
                    in (
                        step.get(
                            "dependencies",
                            [],
                        )
                        or []
                    )
                ],

                condition=deepcopy(
                    step.get(
                        "condition"
                    )
                    if isinstance(
                        step.get(
                            "condition"
                        ),
                        dict,
                    )
                    else None
                ),

                input_bindings=deepcopy(
                    (
                        step.get(
                            "input_bindings",
                            {},
                        )
                        if isinstance(
                            step.get(
                                "input_bindings",
                                {},
                            ),
                            dict,
                        )
                        else {}
                    )
                ),

                output_key=str(
                    step.get(
                        "output_key",
                        "",
                    )
                    or ""
                ),

                retry_policy=(
                    normalize_retry_policy(
                        step.get(
                            "retry_policy"
                        )
                    )
                ),
            )


        else:

            raise TypeError(
                (
                    "Workflow steps must be "
                    "WorkflowStep objects "
                    "or dictionaries."
                )
            )


        item.step_number = (
            index
        )

        normalized.append(
            item
        )


    return normalized


def create_workflow(
    name: str,
    goal: str,
    steps,
    description: str = "",
    workflow_id: str | None = None,
):
    workflow_id = (
        workflow_id
        or new_workflow_id()
    )


    definition = WorkflowDefinition(
        workflow_id=
            workflow_id,

        name=
            str(
                name
                or workflow_id
            ).strip(),

        goal=
            str(
                goal
                or ""
            ).strip(),

        description=
            str(
                description
                or ""
            ).strip(),

        steps=
            normalize_steps(
                steps
            ),
    )


    validate_workflow_definition(
        definition
    )

    save_definition(
        definition
    )

    return definition


def create_workflow_run(
    definition: WorkflowDefinition,
    variables: dict | None = None,
    max_replans: int = 3,
):
    if not definition.enabled:

        raise RuntimeError(
            "Workflow definition is disabled."
        )


    validate_workflow_definition(
        definition
    )


    run = WorkflowRun(
        run_id=
            new_run_id(),

        workflow_id=
            definition.workflow_id,

        workflow_name=
            definition.name,

        goal=
            definition.goal,

        steps=
            deepcopy(
                definition.steps
            ),

        variables=
            deepcopy(
                variables
                or {}
            ),

        max_replans=max(
            0,
            int(
                max_replans
                or 0
            ),
        ),
    )


    save_run(
        run
    )


    record_audit_event(
        run.run_id,
        "run_created",

        workflow_id=
            run.workflow_id,

        message=
            run.goal,
    )


    return run


def run_workflow(
    workflow_id: str,
    variables: dict | None = None,
    max_replans: int = 3,
):
    definition = (
        load_definition(
            workflow_id
        )
    )


    if definition is None:

        raise RuntimeError(
            (
                "Workflow definition "
                "does not exist: "
                f"{workflow_id}"
            )
        )


    run = create_workflow_run(
        definition,
        variables=
            variables,
        max_replans=
            max_replans,
    )


    return run_workflow_engine(
        run
    )


def resume_workflow_run(
    run_id: str,
    approved: bool | None = None,
    recovery_action: str | None = None,
):
    run = load_run(
        run_id
    )


    if run is None:

        raise RuntimeError(
            (
                "Workflow run "
                "does not exist: "
                f"{run_id}"
            )
        )


    run = repair_interrupted_run(
        run
    )


    if run.status == RUN_AWAITING_USER:

        if not recovery_action:

            return run


        return resolve_user_recovery(
            run,
            recovery_action,
        )


    if run.pending_action:

        if approved is None:

            return run


        return resolve_workflow_approval(
            run,
            approved=
                approved,
        )


    return run_workflow_engine(
        run
    )


def cancel_workflow_run(
    run_id: str,
):
    run = load_run(
        run_id
    )


    if run is None:

        return False


    run.status = RUN_CANCELLED
    run.failure_reason = (
        "Workflow cancelled by user."
    )
    run.completed_at = now_string()

    save_run(run)
    archive_run(run)

    return True


def get_workflow_definition(
    workflow_id: str,
):
    return load_definition(
        workflow_id
    )


def list_workflow_definitions():
    return list_definitions()


def get_workflow_run(
    run_id: str,
):
    return load_run(
        run_id
    )


def list_active_workflow_runs():
    return list_active_runs()


def recover_workflows():
    return recover_active_runs()


def get_workflow_audit(
    run_id: str,
):
    return load_audit_events(
        run_id
    )
