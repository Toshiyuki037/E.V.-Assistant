"""
E.V.I.E. - Workflow Conditions

Phase 11B

Purpose:
Evaluate constrained workflow conditions without arbitrary code execution.

Supported operators:
    exists
    not_exists
    equals
    not_equals
    greater_than
    greater_than_or_equal
    less_than
    less_than_or_equal
    contains
    not_contains
    truthy
    falsy

Condition format:

    {
        "left": "{{ outputs.weather.current.temperature_2m }}",
        "operator": "less_than",
        "right": 60
    }

or:

    {
        "value": "{{ outputs.github_result }}",
        "operator": "exists"
    }
"""

from __future__ import annotations

from .data import (
    WorkflowReferenceError,
    resolve_value,
)


class WorkflowConditionError(
    RuntimeError
):
    pass


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _exists(
    value,
):
    return value is not None


def _contains(
    left,
    right,
):
    try:

        return (
            right
            in left
        )

    except TypeError:

        return False


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------

def evaluate_condition(
    condition,
    run,
):
    if condition is None:

        return True


    if not isinstance(
        condition,
        dict,
    ):

        raise WorkflowConditionError(
            "Workflow condition must be a dictionary."
        )


    operator = (
        str(
            condition.get(
                "operator",
                "",
            )
            or ""
        )
        .strip()
        .lower()
    )


    if not operator:

        raise WorkflowConditionError(
            "Workflow condition requires an operator."
        )


    left_source = (
        condition.get(
            "left",
            condition.get(
                "value"
            ),
        )
    )


    try:

        left = (
            resolve_value(
                left_source,
                run,
            )
        )

    except WorkflowReferenceError:

        if operator in {
            "exists",
            "not_exists",
        }:

            left = None

        else:

            raise


    if operator == "exists":

        return _exists(
            left
        )


    if operator == "not_exists":

        return not _exists(
            left
        )


    if operator == "truthy":

        return bool(
            left
        )


    if operator == "falsy":

        return not bool(
            left
        )


    right = (
        resolve_value(
            condition.get(
                "right"
            ),
            run,
        )
    )


    if operator == "equals":

        return (
            left
            == right
        )


    if operator == "not_equals":

        return (
            left
            != right
        )


    if operator == "greater_than":

        return (
            left
            > right
        )


    if operator == "greater_than_or_equal":

        return (
            left
            >= right
        )


    if operator == "less_than":

        return (
            left
            < right
        )


    if operator == "less_than_or_equal":

        return (
            left
            <= right
        )


    if operator == "contains":

        return _contains(
            left,
            right,
        )


    if operator == "not_contains":

        return not _contains(
            left,
            right,
        )


    raise WorkflowConditionError(
        (
            "Unknown workflow condition "
            f"operator: {operator}"
        )
    )
