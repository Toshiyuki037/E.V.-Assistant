"""
E.V.I.E. - Protocol Authoring

Phase 11H

Purpose:
Create, inspect, modify, clone, and delete saved protocols through a
bounded protocol-authoring interface.

This module never executes tools. It only edits saved protocol
definitions. Actual protocol execution continues through the Phase 11
workflow engine and Phase 6 permission system.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from .protocols import (
    clone_protocol,
    create_protocol,
    delete_protocol,
    get_protocol,
    update_protocol,
)


# ---------------------------------------------------------------------------
# Supported High-Level Actions
# ---------------------------------------------------------------------------

def build_weather_step(
    *,
    step_id: str = "weather",
    location_reference: str = "{{ variables.location }}",
):
    return {
        "step_id": step_id,
        "description": "Read current weather.",
        "tool_name": "integration_execute",
        "arguments": {
            "capability": "weather.current",
            "provider": "weather",
            "account_id": "public",
            "routing_mode": "explicit_account",
            "arguments": {
                "location": location_reference,
            },
        },
        "output_key": "weather",
    }


def build_github_commits_step(
    *,
    step_id: str = "commits",
    repo_reference: str = "{{ variables.repo }}",
):
    return {
        "step_id": step_id,
        "description": "Read latest repository commits.",
        "tool_name": "integration_execute",
        "arguments": {
            "capability": "github.commits",
            "provider": "github",
            "account_id": "primary",
            "routing_mode": "explicit_account",
            "arguments": {
                "repo": repo_reference,
            },
        },
        "output_key": "github_commits",
    }


SUPPORTED_STEP_BUILDERS = {
    "weather": build_weather_step,
    "github_commits": build_github_commits_step,
}


# ---------------------------------------------------------------------------
# Protocol Description
# ---------------------------------------------------------------------------

def describe_protocol(
    protocol_id: str,
):
    protocol = get_protocol(
        protocol_id
    )

    lines = [
        f"{protocol.get('name', protocol_id)} ({protocol_id})",
        f"Goal: {protocol.get('goal', '')}",
        (
            "Status: enabled"
            if protocol.get("enabled", True)
            else "Status: disabled"
        ),
    ]

    description = (
        protocol.get(
            "description",
            ""
        )
        or ""
    )

    if description:
        lines.append(
            f"Description: {description}"
        )

    steps = (
        protocol.get(
            "steps",
            []
        )
        or []
    )

    if steps:
        lines.append(
            "Steps:"
        )

        for index, step in enumerate(
            steps,
            start=1,
        ):
            lines.append(
                (
                    f"- {index}. "
                    f"{step.get('description', step.get('step_id', 'step'))}"
                )
            )
    else:
        lines.append(
            "Steps: none"
        )

    defaults = (
        protocol.get(
            "default_variables",
            {}
        )
        or {}
    )

    if defaults:
        lines.append(
            f"Default variables: {defaults}"
        )

    return "\n".join(
        lines
    )


# ---------------------------------------------------------------------------
# Create From Supported Actions
# ---------------------------------------------------------------------------

def create_protocol_from_actions(
    *,
    protocol_id: str,
    name: str,
    goal: str,
    actions: list[str],
    description: str = "",
    default_variables: dict[str, Any] | None = None,
    overwrite: bool = False,
):
    steps = []

    for action in actions:
        builder = (
            SUPPORTED_STEP_BUILDERS.get(
                action
            )
        )

        if builder is None:
            raise ValueError(
                (
                    "Unsupported protocol action: "
                    f"{action}"
                )
            )

        steps.append(
            builder()
        )

    return create_protocol(
        protocol_id=protocol_id,
        name=name,
        goal=goal,
        description=description,
        steps=steps,
        default_variables=deepcopy(
            default_variables
            or {}
        ),
        overwrite=overwrite,
    )


# ---------------------------------------------------------------------------
# Add / Remove Supported Actions
# ---------------------------------------------------------------------------

def add_action_to_protocol(
    protocol_id: str,
    action: str,
):
    protocol = get_protocol(
        protocol_id
    )

    builder = (
        SUPPORTED_STEP_BUILDERS.get(
            action
        )
    )

    if builder is None:
        raise ValueError(
            (
                "Unsupported protocol action: "
                f"{action}"
            )
        )

    steps = deepcopy(
        protocol.get(
            "steps",
            []
        )
        or []
    )

    new_step = (
        builder()
    )

    new_output = (
        new_step.get(
            "output_key"
        )
    )

    if any(
        step.get(
            "output_key"
        )
        == new_output
        for step
        in steps
    ):
        return protocol

    steps.append(
        new_step
    )

    return update_protocol(
        protocol_id,
        steps=steps,
    )


def remove_action_from_protocol(
    protocol_id: str,
    action: str,
):
    protocol = get_protocol(
        protocol_id
    )

    builder = (
        SUPPORTED_STEP_BUILDERS.get(
            action
        )
    )

    if builder is None:
        raise ValueError(
            (
                "Unsupported protocol action: "
                f"{action}"
            )
        )

    target_output = (
        builder()
        .get(
            "output_key"
        )
    )

    steps = [
        step
        for step
        in (
            protocol.get(
                "steps",
                []
            )
            or []
        )
        if (
            step.get(
                "output_key"
            )
            != target_output
        )
    ]

    return update_protocol(
        protocol_id,
        steps=steps,
    )
