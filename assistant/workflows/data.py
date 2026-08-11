"""
E.V.I.E. - Workflow Data Resolution

Phase 11B

Purpose:
Resolve workflow variables, prior step outputs, and input bindings.

Supported references:
    {{ variables.name }}
    {{ outputs.weather_result }}
    {{ outputs.weather_result.evidence.0.data.location }}

References may be used as:
    - an entire value
    - embedded inside a larger string

This module never executes tools.
"""

from __future__ import annotations

import re
from copy import deepcopy
from typing import Any


REFERENCE_PATTERN = re.compile(
    r"\{\{\s*([^{}]+?)\s*\}\}"
)


class WorkflowReferenceError(
    RuntimeError
):
    pass


# ---------------------------------------------------------------------------
# Path Resolution
# ---------------------------------------------------------------------------

def _split_reference(
    reference: str,
):
    return [
        part.strip()
        for part
        in str(
            reference
            or ""
        ).split(".")
        if part.strip()
    ]


def resolve_path(
    root: Any,
    path_parts: list[str],
):
    value = root

    for part in path_parts:

        if isinstance(
            value,
            dict,
        ):

            if part not in value:

                raise WorkflowReferenceError(
                    (
                        "Workflow reference path "
                        f"does not exist: {part}"
                    )
                )

            value = value[
                part
            ]

            continue


        if isinstance(
            value,
            (list, tuple),
        ):

            try:

                index = int(
                    part
                )

            except ValueError as error:

                raise WorkflowReferenceError(
                    (
                        "List workflow references "
                        "require numeric indexes: "
                        f"{part}"
                    )
                ) from error


            if (
                index < 0
                or index >= len(
                    value
                )
            ):

                raise WorkflowReferenceError(
                    (
                        "Workflow reference index "
                        f"is out of range: {index}"
                    )
                )


            value = value[
                index
            ]

            continue


        if hasattr(
            value,
            part,
        ):

            value = getattr(
                value,
                part,
            )

            continue


        raise WorkflowReferenceError(
            (
                "Workflow reference cannot "
                f"continue through value at: {part}"
            )
        )


    return value


# ---------------------------------------------------------------------------
# Context
# ---------------------------------------------------------------------------

def build_reference_context(
    run,
):
    return {
        "variables":
            deepcopy(
                run.variables
            ),

        "outputs":
            deepcopy(
                run.outputs
            ),
    }


# ---------------------------------------------------------------------------
# Reference Resolution
# ---------------------------------------------------------------------------

def resolve_reference(
    reference: str,
    run,
):
    parts = (
        _split_reference(
            reference
        )
    )


    if not parts:

        raise WorkflowReferenceError(
            "Workflow reference is empty."
        )


    root_name = (
        parts[
            0
        ]
    )


    context = (
        build_reference_context(
            run
        )
    )


    if root_name not in context:

        raise WorkflowReferenceError(
            (
                "Workflow reference must start "
                "with variables or outputs: "
                f"{reference}"
            )
        )


    return resolve_path(
        context[
            root_name
        ],
        parts[
            1:
        ],
    )


# ---------------------------------------------------------------------------
# Recursive Value Resolution
# ---------------------------------------------------------------------------

def resolve_value(
    value,
    run,
):
    if isinstance(
        value,
        dict,
    ):

        return {
            key:
                resolve_value(
                    item,
                    run,
                )
            for key, item
            in value.items()
        }


    if isinstance(
        value,
        list,
    ):

        return [
            resolve_value(
                item,
                run,
            )
            for item
            in value
        ]


    if isinstance(
        value,
        tuple,
    ):

        return tuple(
            resolve_value(
                item,
                run,
            )
            for item
            in value
        )


    if not isinstance(
        value,
        str,
    ):

        return deepcopy(
            value
        )


    matches = list(
        REFERENCE_PATTERN.finditer(
            value
        )
    )


    if not matches:

        return value


    # Entire value is one reference:
    # preserve the original object type.
    if (
        len(matches)
        == 1
        and matches[
            0
        ].span()
        == (
            0,
            len(
                value
            ),
        )
    ):

        return deepcopy(
            resolve_reference(
                matches[
                    0
                ].group(
                    1
                ),
                run,
            )
        )


    # Embedded references become text.
    rendered = value


    for match in reversed(
        matches
    ):

        resolved = (
            resolve_reference(
                match.group(
                    1
                ),
                run,
            )
        )


        start, end = (
            match.span()
        )


        rendered = (
            rendered[
                :start
            ]
            + str(
                resolved
            )
            + rendered[
                end:
            ]
        )


    return rendered


# ---------------------------------------------------------------------------
# Step Bindings
# ---------------------------------------------------------------------------

def apply_input_bindings(
    arguments: dict,
    bindings: dict,
    run,
):
    resolved = deepcopy(
        arguments
    )


    if not isinstance(
        bindings,
        dict,
    ):

        return resolve_value(
            resolved,
            run,
        )


    # Resolve references already embedded in the base arguments.
    resolved = (
        resolve_value(
            resolved,
            run,
        )
    )


    for key, binding in (
        bindings.items()
    ):

        resolved[
            key
        ] = (
            resolve_value(
                binding,
                run,
            )
        )


    return resolved
