"""
E.V.I.E. - Workflow Validation

Phase 11B / 11D
"""

from __future__ import annotations


VALID_FAILURE_BEHAVIORS = {
    "stop_workflow",
    "retry",
    "skip_step",
    "request_user",
    "replan",
}

VALID_CONDITION_OPERATORS = {
    "exists",
    "not_exists",
    "equals",
    "not_equals",
    "greater_than",
    "greater_than_or_equal",
    "less_than",
    "less_than_or_equal",
    "contains",
    "not_contains",
    "truthy",
    "falsy",
}


class WorkflowValidationError(
    ValueError
):
    pass


def _validate_cycles(
    steps,
):
    graph = {
        step.step_id:
            list(
                step.dependencies
            )
        for step
        in steps
    }

    visiting = set()
    visited = set()


    def visit(
        node,
    ):
        if node in visited:

            return


        if node in visiting:

            raise WorkflowValidationError(
                (
                    "Workflow dependency cycle "
                    f"detected at step: {node}"
                )
            )


        visiting.add(
            node
        )


        for dependency in (
            graph.get(
                node,
                []
            )
        ):

            visit(
                dependency
            )


        visiting.remove(
            node
        )

        visited.add(
            node
        )


    for node in graph:

        visit(
            node
        )


def validate_workflow_definition(
    definition,
):
    if not str(
        definition.workflow_id
        or ""
    ).strip():

        raise WorkflowValidationError(
            "Workflow ID cannot be empty."
        )


    if not str(
        definition.name
        or ""
    ).strip():

        raise WorkflowValidationError(
            "Workflow name cannot be empty."
        )


    if not str(
        definition.goal
        or ""
    ).strip():

        raise WorkflowValidationError(
            "Workflow goal cannot be empty."
        )


    if not definition.steps:

        raise WorkflowValidationError(
            "Workflow requires at least one step."
        )


    step_ids = [
        step.step_id
        for step
        in definition.steps
    ]


    if (
        len(
            step_ids
        )
        != len(
            set(
                step_ids
            )
        )
    ):

        raise WorkflowValidationError(
            "Workflow step IDs must be unique."
        )


    known_ids = set(
        step_ids
    )

    output_keys = []


    for step in definition.steps:

        if not str(
            step.step_id
            or ""
        ).strip():

            raise WorkflowValidationError(
                "Workflow step ID cannot be empty."
            )


        if not str(
            step.tool_name
            or ""
        ).strip():

            raise WorkflowValidationError(
                (
                    "Workflow step requires a tool: "
                    f"{step.step_id}"
                )
            )


        if step.step_id in (
            step.dependencies
        ):

            raise WorkflowValidationError(
                (
                    "Workflow step cannot depend "
                    f"on itself: {step.step_id}"
                )
            )


        for dependency in (
            step.dependencies
        ):

            if dependency not in known_ids:

                raise WorkflowValidationError(
                    (
                        "Workflow dependency "
                        f"does not exist: {dependency}"
                    )
                )


        failure_behavior = (
            step.retry_policy
            .failure_behavior
        )


        if (
            failure_behavior
            not in VALID_FAILURE_BEHAVIORS
        ):

            raise WorkflowValidationError(
                (
                    "Unknown workflow failure "
                    f"behavior: {failure_behavior}"
                )
            )


        if step.condition is not None:

            if not isinstance(
                step.condition,
                dict,
            ):

                raise WorkflowValidationError(
                    (
                        "Workflow condition must "
                        f"be a dictionary: {step.step_id}"
                    )
                )


            operator = (
                str(
                    step.condition.get(
                        "operator",
                        "",
                    )
                    or ""
                )
                .strip()
                .lower()
            )


            if (
                operator
                not in VALID_CONDITION_OPERATORS
            ):

                raise WorkflowValidationError(
                    (
                        "Unknown workflow condition "
                        f"operator: {operator}"
                    )
                )


        if step.output_key:

            output_keys.append(
                step.output_key
            )


    if (
        len(
            output_keys
        )
        != len(
            set(
                output_keys
            )
        )
    ):

        raise WorkflowValidationError(
            "Workflow output keys must be unique."
        )


    _validate_cycles(
        definition.steps
    )


    return True
