"""
E.V.I.E. - Workflow Models

Phase 11A / 11B / 11C / 11D
"""

from __future__ import annotations

from dataclasses import (
    asdict,
    dataclass,
    field,
)

from typing import Any


STEP_PENDING = "pending"
STEP_READY = "ready"
STEP_RUNNING = "running"
STEP_COMPLETED = "completed"
STEP_FAILED = "failed"
STEP_SKIPPED = "skipped"
STEP_AWAITING_APPROVAL = "awaiting_approval"
STEP_AWAITING_USER = "awaiting_user"
STEP_CANCELLED = "cancelled"

RUN_PLANNED = "planned"
RUN_RUNNING = "running"
RUN_AWAITING_APPROVAL = "awaiting_approval"
RUN_AWAITING_USER = "awaiting_user"
RUN_COMPLETED = "completed"
RUN_FAILED = "failed"
RUN_CANCELLED = "cancelled"
RUN_PAUSED = "paused"


@dataclass
class WorkflowRetryPolicy:
    max_attempts: int = 1
    retry_delay_seconds: int = 0
    failure_behavior: str = "stop_workflow"

    retry_on: list[str] = field(
        default_factory=list
    )


@dataclass
class WorkflowStep:
    step_id: str
    step_number: int
    description: str

    tool_name: str = ""

    arguments: dict[str, Any] = field(
        default_factory=dict
    )

    dependencies: list[str] = field(
        default_factory=list
    )

    condition: dict[str, Any] | None = None

    input_bindings: dict[str, Any] = field(
        default_factory=dict
    )

    output_key: str = ""

    retry_policy: WorkflowRetryPolicy = field(
        default_factory=WorkflowRetryPolicy
    )

    status: str = STEP_PENDING

    attempts: int = 0

    result: Any = None

    error: str | None = None

    started_at: str = ""

    completed_at: str = ""

    last_attempt_at: str = ""

    recovery_note: str = ""


@dataclass
class WorkflowDefinition:
    workflow_id: str
    name: str
    goal: str

    description: str = ""

    steps: list[WorkflowStep] = field(
        default_factory=list
    )

    enabled: bool = True

    created_at: str = ""

    updated_at: str = ""


@dataclass
class WorkflowRun:
    run_id: str
    workflow_id: str
    workflow_name: str
    goal: str

    steps: list[WorkflowStep] = field(
        default_factory=list
    )

    status: str = RUN_PLANNED

    variables: dict[str, Any] = field(
        default_factory=dict
    )

    outputs: dict[str, Any] = field(
        default_factory=dict
    )

    pending_action: dict[str, Any] | None = None

    failure_reason: str = ""

    final_summary: str = ""

    created_at: str = ""

    started_at: str = ""

    updated_at: str = ""

    completed_at: str = ""

    resume_count: int = 0

    replan_count: int = 0

    max_replans: int = 3

    awaiting_user_reason: str = ""

    recovery_context: dict[str, Any] = field(
        default_factory=dict
    )


def step_to_dict(
    step: WorkflowStep,
):
    return asdict(
        step
    )


def definition_to_dict(
    definition: WorkflowDefinition,
):
    return asdict(
        definition
    )


def run_to_dict(
    run: WorkflowRun,
):
    return asdict(
        run
    )


def retry_policy_from_dict(
    data,
):
    data = (
        data
        if isinstance(
            data,
            dict,
        )
        else {}
    )

    retry_on = (
        data.get(
            "retry_on",
            [],
        )
        or []
    )

    return WorkflowRetryPolicy(
        max_attempts=int(
            data.get(
                "max_attempts",
                1,
            )
            or 1
        ),

        retry_delay_seconds=int(
            data.get(
                "retry_delay_seconds",
                0,
            )
            or 0
        ),

        failure_behavior=str(
            data.get(
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
            in retry_on
        ],
    )


def step_from_dict(
    data: dict,
    fallback_number: int = 1,
):
    return WorkflowStep(
        step_id=str(
            data.get(
                "step_id",
                f"step_{fallback_number}",
            )
        ),

        step_number=int(
            data.get(
                "step_number",
                fallback_number,
            )
            or fallback_number
        ),

        description=str(
            data.get(
                "description",
                "",
            )
            or ""
        ),

        tool_name=str(
            data.get(
                "tool_name",
                "",
            )
            or ""
        ),

        arguments=(
            data.get(
                "arguments",
                {},
            )
            if isinstance(
                data.get(
                    "arguments",
                    {},
                ),
                dict,
            )
            else {}
        ),

        dependencies=[
            str(
                item
            )
            for item
            in (
                data.get(
                    "dependencies",
                    [],
                )
                or []
            )
        ],

        condition=(
            data.get(
                "condition"
            )
            if isinstance(
                data.get(
                    "condition"
                ),
                dict,
            )
            else None
        ),

        input_bindings=(
            data.get(
                "input_bindings",
                {},
            )
            if isinstance(
                data.get(
                    "input_bindings",
                    {},
                ),
                dict,
            )
            else {}
        ),

        output_key=str(
            data.get(
                "output_key",
                "",
            )
            or ""
        ),

        retry_policy=retry_policy_from_dict(
            data.get(
                "retry_policy"
            )
        ),

        status=str(
            data.get(
                "status",
                STEP_PENDING,
            )
            or STEP_PENDING
        ),

        attempts=int(
            data.get(
                "attempts",
                0,
            )
            or 0
        ),

        result=data.get(
            "result"
        ),

        error=data.get(
            "error"
        ),

        started_at=str(
            data.get(
                "started_at",
                "",
            )
            or ""
        ),

        completed_at=str(
            data.get(
                "completed_at",
                "",
            )
            or ""
        ),

        last_attempt_at=str(
            data.get(
                "last_attempt_at",
                "",
            )
            or ""
        ),

        recovery_note=str(
            data.get(
                "recovery_note",
                "",
            )
            or ""
        ),
    )


def definition_from_dict(
    data: dict,
):
    steps = [
        step_from_dict(
            item,
            index,
        )
        for index, item
        in enumerate(
            data.get(
                "steps",
                [],
            )
            or [],
            start=1,
        )
        if isinstance(
            item,
            dict,
        )
    ]

    return WorkflowDefinition(
        workflow_id=str(
            data.get(
                "workflow_id",
                "",
            )
            or ""
        ),

        name=str(
            data.get(
                "name",
                "",
            )
            or ""
        ),

        goal=str(
            data.get(
                "goal",
                "",
            )
            or ""
        ),

        description=str(
            data.get(
                "description",
                "",
            )
            or ""
        ),

        steps=
            steps,

        enabled=bool(
            data.get(
                "enabled",
                True,
            )
        ),

        created_at=str(
            data.get(
                "created_at",
                "",
            )
            or ""
        ),

        updated_at=str(
            data.get(
                "updated_at",
                "",
            )
            or ""
        ),
    )


def run_from_dict(
    data: dict,
):
    steps = [
        step_from_dict(
            item,
            index,
        )
        for index, item
        in enumerate(
            data.get(
                "steps",
                [],
            )
            or [],
            start=1,
        )
        if isinstance(
            item,
            dict,
        )
    ]

    return WorkflowRun(
        run_id=str(
            data.get(
                "run_id",
                "",
            )
            or ""
        ),

        workflow_id=str(
            data.get(
                "workflow_id",
                "",
            )
            or ""
        ),

        workflow_name=str(
            data.get(
                "workflow_name",
                "",
            )
            or ""
        ),

        goal=str(
            data.get(
                "goal",
                "",
            )
            or ""
        ),

        steps=
            steps,

        status=str(
            data.get(
                "status",
                RUN_PLANNED,
            )
            or RUN_PLANNED
        ),

        variables=(
            data.get(
                "variables",
                {},
            )
            if isinstance(
                data.get(
                    "variables",
                    {},
                ),
                dict,
            )
            else {}
        ),

        outputs=(
            data.get(
                "outputs",
                {},
            )
            if isinstance(
                data.get(
                    "outputs",
                    {},
                ),
                dict,
            )
            else {}
        ),

        pending_action=(
            data.get(
                "pending_action"
            )
            if isinstance(
                data.get(
                    "pending_action"
                ),
                dict,
            )
            else None
        ),

        failure_reason=str(
            data.get(
                "failure_reason",
                "",
            )
            or ""
        ),

        final_summary=str(
            data.get(
                "final_summary",
                "",
            )
            or ""
        ),

        created_at=str(
            data.get(
                "created_at",
                "",
            )
            or ""
        ),

        started_at=str(
            data.get(
                "started_at",
                "",
            )
            or ""
        ),

        updated_at=str(
            data.get(
                "updated_at",
                "",
            )
            or ""
        ),

        completed_at=str(
            data.get(
                "completed_at",
                "",
            )
            or ""
        ),

        resume_count=int(
            data.get(
                "resume_count",
                0,
            )
            or 0
        ),

        replan_count=int(
            data.get(
                "replan_count",
                0,
            )
            or 0
        ),

        max_replans=int(
            data.get(
                "max_replans",
                3,
            )
            or 3
        ),

        awaiting_user_reason=str(
            data.get(
                "awaiting_user_reason",
                "",
            )
            or ""
        ),

        recovery_context=(
            data.get(
                "recovery_context",
                {},
            )
            if isinstance(
                data.get(
                    "recovery_context",
                    {},
                ),
                dict,
            )
            else {}
        ),
    )
