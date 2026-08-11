"""
E.V.I.E. - Workflow Natural-Language Planner

Phase 11G / 11H

Adds bounded natural-language protocol authoring.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class WorkflowCommand:
    handled: bool = False
    action: str = ""
    protocol_id: str = ""
    schedule_id: str = ""
    run_id: str = ""
    arguments: dict[str, Any] = field(default_factory=dict)
    confidence: int = 0
    summary: str = ""


def _clean(text: str) -> str:
    return re.sub(
        r"\s+",
        " ",
        str(text or "").strip(),
    )


def _protocol_slug(name: str) -> str:
    value = _clean(name).lower()
    value = re.sub(r"\b(my|the)\b", " ", value)
    value = re.sub(r"\bprotocol\b", " ", value)
    value = re.sub(r"[^a-z0-9_-]+", "-", value)
    return value.strip("-")


def _parse_clock(hour_text: str, minute_text: str | None, ampm: str | None):
    hour = int(hour_text)
    minute = int(minute_text or 0)

    if not (0 <= minute <= 59):
        return None

    marker = (ampm or "").strip().lower()

    if marker:
        if not (1 <= hour <= 12):
            return None

        if marker == "am":
            if hour == 12:
                hour = 0
        elif marker == "pm":
            if hour != 12:
                hour += 12
        else:
            return None
    elif not (0 <= hour <= 23):
        return None

    return hour, minute


def _schedule_id(protocol_id: str, suffix: str):
    safe_suffix = re.sub(
        r"[^a-z0-9_-]+",
        "-",
        suffix.lower(),
    ).strip("-")

    return (
        f"{protocol_id}-{safe_suffix}"
        if safe_suffix
        else f"{protocol_id}-schedule"
    )


def _detect_actions(text: str):
    lowered = text.lower()
    actions = []

    if "weather" in lowered:
        actions.append(
            "weather"
        )

    if (
        "github" in lowered
        or "commit" in lowered
    ):
        actions.append(
            "github_commits"
        )

    return actions


def plan_workflow_command(
    user_message: str,
    *,
    default_timezone: str = "UTC",
):
    text = _clean(user_message)
    lowered = text.lower().rstrip(".!?")

    if not lowered:
        return WorkflowCommand()


    # -----------------------------------------------------------------------
    # Protocol authoring - inspect
    # -----------------------------------------------------------------------

    match = re.fullmatch(
        r"(?:what does|describe|show me)\s+(?:my\s+|the\s+)?(.+?)\s+protocol(?:\s+do)?",
        lowered,
    )

    if match:
        protocol_id = _protocol_slug(
            match.group(1)
        )

        return WorkflowCommand(
            handled=True,
            action="describe_protocol",
            protocol_id=protocol_id,
            confidence=100,
            summary=f"Describe protocol {protocol_id}.",
        )


    # -----------------------------------------------------------------------
    # Protocol authoring - create
    # -----------------------------------------------------------------------

    match = re.fullmatch(
        (
            r"create\s+(?:a\s+)?protocol\s+called\s+(.+?)\s+that\s+(.+)"
        ),
        lowered,
    )

    if match:
        name = _clean(
            match.group(1)
        ).title()

        action_text = (
            match.group(2)
        )

        actions = _detect_actions(
            action_text
        )

        return WorkflowCommand(
            handled=True,
            action="create_protocol",
            protocol_id=_protocol_slug(
                name
            ),
            arguments={
                "name": name,
                "goal": (
                    f"Run the saved {name} routine."
                ),
                "actions": actions,
                "source_text": action_text,
            },
            confidence=100,
            summary=f"Create protocol {name}.",
        )


    # -----------------------------------------------------------------------
    # Protocol authoring - add
    # -----------------------------------------------------------------------

    match = re.fullmatch(
        (
            r"add\s+(.+?)\s+to\s+(?:my\s+|the\s+)?(.+?)\s+protocol"
        ),
        lowered,
    )

    if match:
        actions = _detect_actions(
            match.group(1)
        )

        return WorkflowCommand(
            handled=True,
            action="add_protocol_actions",
            protocol_id=_protocol_slug(
                match.group(2)
            ),
            arguments={
                "actions": actions,
            },
            confidence=100,
            summary="Add actions to saved protocol.",
        )


    # -----------------------------------------------------------------------
    # Protocol authoring - remove
    # -----------------------------------------------------------------------

    match = re.fullmatch(
        (
            r"remove\s+(.+?)\s+from\s+(?:my\s+|the\s+)?(.+?)\s+protocol"
        ),
        lowered,
    )

    if match:
        actions = _detect_actions(
            match.group(1)
        )

        return WorkflowCommand(
            handled=True,
            action="remove_protocol_actions",
            protocol_id=_protocol_slug(
                match.group(2)
            ),
            arguments={
                "actions": actions,
            },
            confidence=100,
            summary="Remove actions from saved protocol.",
        )


    # -----------------------------------------------------------------------
    # Protocol authoring - delete
    # -----------------------------------------------------------------------

    match = re.fullmatch(
        r"delete\s+(?:my\s+|the\s+)?(.+?)\s+protocol",
        lowered,
    )

    if match:
        return WorkflowCommand(
            handled=True,
            action="delete_protocol",
            protocol_id=_protocol_slug(
                match.group(1)
            ),
            confidence=100,
            summary="Delete saved protocol.",
        )


    # -----------------------------------------------------------------------
    # Existing Phase 11G commands
    # -----------------------------------------------------------------------

    if lowered in {
        "what protocols do i have",
        "show my protocols",
        "list my protocols",
        "list protocols",
        "show protocols",
    }:
        return WorkflowCommand(
            handled=True,
            action="list_protocols",
            confidence=100,
            summary="List saved workflow protocols.",
        )


    match = re.fullmatch(
        r"(?:run|start)\s+(?:my\s+|the\s+)?(.+?)\s+protocol",
        lowered,
    )

    if match:
        protocol_id = _protocol_slug(
            match.group(1)
        )

        return WorkflowCommand(
            handled=True,
            action="run_protocol",
            protocol_id=protocol_id,
            confidence=100,
            summary=f"Run saved protocol {protocol_id}.",
        )


    match = re.fullmatch(
        r"(enable|disable)\s+(?:my\s+|the\s+)?(.+?)\s+protocol",
        lowered,
    )

    if match:
        action_word = match.group(1)
        protocol_id = _protocol_slug(
            match.group(2)
        )

        return WorkflowCommand(
            handled=True,
            action=(
                "enable_protocol"
                if action_word == "enable"
                else "disable_protocol"
            ),
            protocol_id=protocol_id,
            confidence=100,
            summary=f"{action_word.title()} saved protocol {protocol_id}.",
        )


    if lowered in {
        "what schedules do i have",
        "show my schedules",
        "list my schedules",
        "list schedules",
        "show schedules",
        "what protocols are scheduled",
    }:
        return WorkflowCommand(
            handled=True,
            action="list_schedules",
            confidence=100,
            summary="List persistent workflow schedules.",
        )


    match = re.fullmatch(
        (
            r"schedule\s+(?:my\s+|the\s+)?(.+?)\s+protocol\s+"
            r"(?:every\s+)?weekday(?:s)?\s+at\s+"
            r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)?"
        ),
        lowered,
    )

    if match:
        protocol_id = _protocol_slug(
            match.group(1)
        )

        parsed = _parse_clock(
            match.group(2),
            match.group(3),
            match.group(4),
        )

        if parsed is None:
            return WorkflowCommand(
                handled=True,
                action="invalid",
                confidence=100,
                summary="The schedule time was invalid.",
            )

        hour, minute = parsed

        return WorkflowCommand(
            handled=True,
            action="create_schedule",
            protocol_id=protocol_id,
            schedule_id=_schedule_id(
                protocol_id,
                "weekdays",
            ),
            arguments={
                "schedule_type": "weekly",
                "timezone": default_timezone,
                "hour": hour,
                "minute": minute,
                "weekdays": [
                    "monday",
                    "tuesday",
                    "wednesday",
                    "thursday",
                    "friday",
                ],
            },
            confidence=100,
            summary=(
                f"Schedule {protocol_id} every weekday "
                f"at {hour:02d}:{minute:02d}."
            ),
        )


    match = re.fullmatch(
        (
            r"schedule\s+(?:my\s+|the\s+)?(.+?)\s+protocol\s+"
            r"(?:every\s+day|daily)\s+at\s+"
            r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)?"
        ),
        lowered,
    )

    if match:
        protocol_id = _protocol_slug(
            match.group(1)
        )

        parsed = _parse_clock(
            match.group(2),
            match.group(3),
            match.group(4),
        )

        if parsed is None:
            return WorkflowCommand(
                handled=True,
                action="invalid",
                confidence=100,
                summary="The schedule time was invalid.",
            )

        hour, minute = parsed

        return WorkflowCommand(
            handled=True,
            action="create_schedule",
            protocol_id=protocol_id,
            schedule_id=_schedule_id(
                protocol_id,
                "daily",
            ),
            arguments={
                "schedule_type": "daily",
                "timezone": default_timezone,
                "hour": hour,
                "minute": minute,
            },
            confidence=100,
            summary=(
                f"Schedule {protocol_id} every day "
                f"at {hour:02d}:{minute:02d}."
            ),
        )


    if lowered in {
        "what workflows are running",
        "show running workflows",
        "list running workflows",
        "what workflow is running",
        "what are you working on",
    }:
        return WorkflowCommand(
            handled=True,
            action="list_active_runs",
            confidence=100,
            summary="List active workflow runs.",
        )


    if lowered in {
        "resume the current workflow",
        "resume current workflow",
        "continue the workflow",
        "continue workflow",
        "resume workflow",
    }:
        return WorkflowCommand(
            handled=True,
            action="resume_active_run",
            confidence=100,
            summary="Resume the active workflow.",
        )


    if lowered in {
        "cancel the current workflow",
        "cancel current workflow",
        "stop the current workflow",
        "stop current workflow",
        "cancel workflow",
    }:
        return WorkflowCommand(
            handled=True,
            action="cancel_active_run",
            confidence=100,
            summary="Cancel the active workflow.",
        )


    if lowered in {
        "retry that workflow step",
        "retry the workflow step",
        "retry that step",
        "retry workflow",
    }:
        return WorkflowCommand(
            handled=True,
            action="recover_active_run",
            arguments={
                "recovery_action": "retry",
            },
            confidence=100,
            summary="Retry the active workflow recovery step.",
        )


    if lowered in {
        "skip that workflow step",
        "skip the workflow step",
        "skip that step",
        "skip workflow step",
    }:
        return WorkflowCommand(
            handled=True,
            action="recover_active_run",
            arguments={
                "recovery_action": "skip",
            },
            confidence=100,
            summary="Skip the active workflow recovery step.",
        )


    return WorkflowCommand()
