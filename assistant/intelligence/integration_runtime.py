"""
E.V.I.E. - Integration Runtime Normalization

Phase 10E

Purpose:
Provides one shared preparation layer for integration_execute
arguments before execution.

Used by:
    Phase 6 tool planning
    Phase 7 agent execution

Responsibilities:
    - canonical capability normalization
    - explicit preference application

Does NOT:
    - execute tools
    - approve actions
    - lower risk
"""

from __future__ import annotations

from copy import deepcopy

from .aliases import (
    normalize_capability,
)

from .preferences import (
    apply_integration_preferences,
)


# ---------------------------------------------------------------------------
# Prepare Integration Arguments
# ---------------------------------------------------------------------------

def prepare_integration_arguments(
    arguments: dict,
):
    if not isinstance(
        arguments,
        dict,
    ):

        return arguments


    prepared = deepcopy(
        arguments
    )


    capability = (
        prepared.get(
            "capability"
        )
    )


    if isinstance(
        capability,
        str,
    ):

        prepared[
            "capability"
        ] = (
            normalize_capability(
                capability
            )
        )


    prepared = (
        apply_integration_preferences(
            prepared
        )
    )


    return prepared


# ---------------------------------------------------------------------------
# Prepare Any Tool
# ---------------------------------------------------------------------------

def prepare_tool_arguments(
    tool_name: str,
    arguments: dict,
):
    if (
        str(
            tool_name
            or ""
        )
        .strip()
        .lower()
        != "integration_execute"
    ):

        return arguments


    return (
        prepare_integration_arguments(
            arguments
        )
    )


# ---------------------------------------------------------------------------
# Diagnostic
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    sample = {
        "capability":
            "repos.read",

        "provider":
            "github",

        "arguments":
            {},
    }


    print(
        prepare_integration_arguments(
            sample
        )
    )