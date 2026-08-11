"""
E.V.I.E. - Workflow Runtime Integration

Phase 11G / 11H
"""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from assistant.tools.session import (
    parse_approval_response,
)

from .authoring import (
    add_action_to_protocol,
    create_protocol_from_actions,
    describe_protocol,
    remove_action_from_protocol,
)

from .controller import (
    cancel_workflow_run,
    list_active_workflow_runs,
    resume_workflow_run,
)

from .planner import (
    plan_workflow_command,
)

from .presentation import (
    format_workflow_outputs,
)

from .protocols import (
    delete_protocol,
    get_protocol,
    list_protocols,
    run_protocol,
    set_protocol_enabled,
)

from .schedules import (
    create_schedule,
    list_schedules,
)


def _format_protocols(
    protocols,
):
    if not protocols:
        return "You do not have any saved protocols."

    lines = [
        "Saved protocols:"
    ]

    for protocol in protocols:
        status = (
            "enabled"
            if protocol.get(
                "enabled",
                True,
            )
            else "disabled"
        )

        lines.append(
            (
                f"- {protocol.get('name', protocol.get('protocol_id'))} "
                f"({protocol.get('protocol_id')}) — {status}"
            )
        )

    return "\n".join(
        lines
    )


def _format_timezone_suffix(
    zone: ZoneInfo,
    local: datetime,
    *,
    timezone_name: str,
):
    """
    Display-only helper.

    Keeps scheduling semantics unchanged by:
    - never writing schedule state
    - never influencing next_run_at calculations

    Goal:
    Provide a clearer human-facing timezone suffix than just the IANA
    name by including an offset.

    Example:
        "America/Los_Angeles (UTC-07:00)"

    Falls back to the original timezone name when the offset cannot be
    determined.
    """

    try:
        offset = local.utcoffset()

        if offset is None:
            return timezone_name

        total_minutes = int(
            offset.total_seconds() // 60
        )

        sign = "+" if total_minutes >= 0 else "-"
        total_minutes = abs(total_minutes)
        hours = total_minutes // 60
        minutes = total_minutes % 60

        return (
            f"{timezone_name} "
            f"(UTC{sign}{hours:02d}:{minutes:02d})"
        )

    except Exception:
        return timezone_name


def _format_schedule_next_run(
    schedule,
):
    value = (
        schedule.get(
            "next_run_at"
        )
        or ""
    )

    if not value:
        return "none"

    timezone_name = str(
        schedule.get(
            "timezone",
            "UTC",
        )
        or "UTC"
    )

    try:
        zone = ZoneInfo(
            timezone_name
        )

        parsed = datetime.fromisoformat(
            str(
                value
            )
        )

        if parsed.tzinfo is None:
            parsed = parsed.replace(
                tzinfo=ZoneInfo(
                    "UTC"
                )
            )

        local = parsed.astimezone(
            zone
        )

    except Exception:
        return str(
            value
        )

    stamp = local.strftime(
        "%Y-%m-%d %I:%M %p"
    ).replace(
        " 0",
        " ",
    )

    suffix = _format_timezone_suffix(
        zone,
        local,
        timezone_name=timezone_name,
    )

    return (
        f"{stamp} {suffix}"
    )


def _format_schedules(
    schedules,
):
    if not schedules:
        return "You do not have any saved workflow schedules."

    lines = [
        "Saved workflow schedules:"
    ]

    for schedule in schedules:
        status = (
            "enabled"
            if schedule.get(
                "enabled",
                True,
            )
            else "disabled"
        )

        next_run = _format_schedule_next_run(
            schedule
        )

        lines.append(
            (
                f"- {schedule.get('schedule_id')} → "
                f"{schedule.get('protocol_id')} — "
                f"{status}; next run {next_run}"
            )
        )

    return "\n".join(
        lines
    )


def _format_run_state(
    run,
):
    lines = [
        (
            f"Workflow: {run.workflow_name}"
        ),
        (
            f"Status: {run.status}"
        ),
        (
            f"Run: {run.run_id}"
        ),
    ]

    if run.awaiting_user_reason:
        lines.append(
            (
                "Needs input: "
                f"{run.awaiting_user_reason}"
            )
        )

    if run.pending_action:
        description = (
            run.pending_action.get(
                "description"
            )
            or "workflow action"
        )

        risk = (
            run.pending_action.get(
                "risk"
            )
            or "unknown"
        )

        lines.append(
            (
                f"Pending approval: {description} "
                f"(risk: {risk})"
            )
        )

    if run.steps:
        lines.append(
            "Steps:"
        )

        for step in run.steps:
            lines.append(
                (
                    f"- {step.step_number}. "
                    f"{step.description} "
                    f"[{step.status}]"
                )
            )

    return "\n".join(
        lines
    )


def _active_runs():
    return list_active_workflow_runs()


def _single_active_run():
    runs = _active_runs()

    if len(runs) == 1:
        return runs[0]

    return None


def _active_run_error():
    runs = _active_runs()

    if not runs:
        return "There is no active workflow."

    return (
        "More than one workflow is active. "
        "Specify the workflow run before continuing."
    )


def handle_pending_workflow_approval(
    user_message: str,
):
    runs = [
        run
        for run
        in _active_runs()
        if run.pending_action
    ]

    if not runs:
        return {
            "handled": False,
            "response": None,
        }

    if len(runs) != 1:
        return {
            "handled": False,
            "response": None,
        }

    approval = parse_approval_response(
        user_message
    )

    if approval.decision not in {
        "approve",
        "reject",
    }:
        return {
            "handled": False,
            "response": None,
        }

    run = resume_workflow_run(
        runs[0].run_id,
        approved=(
            approval.decision
            == "approve"
        ),
    )

    return {
        "handled": True,
        "response": (
            format_workflow_outputs(
                run
            )
            if run.status == "completed"
            else _format_run_state(
                run
            )
        ),
        "follow_up": approval.remainder,
    }


def handle_workflow_message(
    user_message: str,
    *,
    default_timezone: str = "UTC",
):
    command = plan_workflow_command(
        user_message,
        default_timezone=default_timezone,
    )

    if not command.handled:
        return {
            "handled": False,
            "response": None,
            "follow_up": "",
        }


    if command.action == "invalid":
        return {
            "handled": True,
            "response": command.summary,
            "follow_up": "",
        }


    if command.action == "describe_protocol":
        try:
            response = describe_protocol(
                command.protocol_id
            )
        except Exception as error:
            response = (
                "I could not describe that protocol: "
                f"{error}"
            )

        return {
            "handled": True,
            "response": response,
            "follow_up": "",
        }


    if command.action == "create_protocol":
        actions = (
            command.arguments.get(
                "actions",
                []
            )
            or []
        )

        if not actions:
            return {
                "handled": True,
                "response": (
                    "I understood that you want to create a protocol, "
                    "but I could not map its requested actions to a "
                    "supported Phase 11 protocol action yet."
                ),
                "follow_up": "",
            }

        defaults = {}

        if "weather" in actions:
            defaults[
                "location"
            ] = "Honolulu"

        if "github_commits" in actions:
            defaults[
                "repo"
            ] = "E.V.-Assistant"

        try:
            protocol = create_protocol_from_actions(
                protocol_id=
                    command.protocol_id,
                name=
                    command.arguments[
                        "name"
                    ],
                goal=
                    command.arguments[
                        "goal"
                    ],
                actions=
                    actions,
                default_variables=
                    defaults,
            )
        except Exception as error:
            return {
                "handled": True,
                "response": (
                    "I could not create that protocol: "
                    f"{error}"
                ),
                "follow_up": "",
            }

        return {
            "handled": True,
            "response": (
                f"Created {protocol['name']} "
                f"({protocol['protocol_id']})."
            ),
            "follow_up": "",
        }


    if command.action in {
        "add_protocol_actions",
        "remove_protocol_actions",
    }:
        actions = (
            command.arguments.get(
                "actions",
                []
            )
            or []
        )

        if not actions:
            return {
                "handled": True,
                "response": (
                    "I could not map that requested change "
                    "to a supported protocol action."
                ),
                "follow_up": "",
            }

        try:
            for action in actions:
                if command.action == "add_protocol_actions":
                    add_action_to_protocol(
                        command.protocol_id,
                        action,
                    )
                else:
                    remove_action_from_protocol(
                        command.protocol_id,
                        action,
                    )
        except Exception as error:
            return {
                "handled": True,
                "response": (
                    "I could not modify that protocol: "
                    f"{error}"
                ),
                "follow_up": "",
            }

        return {
            "handled": True,
            "response": describe_protocol(
                command.protocol_id
            ),
            "follow_up": "",
        }


    if command.action == "delete_protocol":
        deleted = delete_protocol(
            command.protocol_id
        )

        return {
            "handled": True,
            "response": (
                "Protocol deleted."
                if deleted
                else "That protocol does not exist."
            ),
            "follow_up": "",
        }


    if command.action == "list_protocols":
        return {
            "handled": True,
            "response": _format_protocols(
                list_protocols()
            ),
            "follow_up": "",
        }


    if command.action == "run_protocol":
        try:
            run = run_protocol(
                command.protocol_id
            )
        except Exception as error:
            return {
                "handled": True,
                "response": (
                    "I could not run that protocol: "
                    f"{error}"
                ),
                "follow_up": "",
            }

        return {
            "handled": True,
            "response": (
                format_workflow_outputs(
                    run
                )
                if run.status == "completed"
                else _format_run_state(
                    run
                )
            ),
            "follow_up": "",
        }


    if command.action in {
        "enable_protocol",
        "disable_protocol",
    }:
        try:
            protocol = set_protocol_enabled(
                command.protocol_id,
                command.action
                == "enable_protocol",
            )
        except Exception as error:
            return {
                "handled": True,
                "response": (
                    "I could not update that protocol: "
                    f"{error}"
                ),
                "follow_up": "",
            }

        state = (
            "enabled"
            if protocol.get(
                "enabled",
                True,
            )
            else "disabled"
        )

        return {
            "handled": True,
            "response": (
                f"{protocol.get('name', command.protocol_id)} "
                f"is now {state}."
            ),
            "follow_up": "",
        }


    if command.action == "list_schedules":
        return {
            "handled": True,
            "response": _format_schedules(
                list_schedules()
            ),
            "follow_up": "",
        }


    if command.action == "create_schedule":
        try:
            get_protocol(
                command.protocol_id
            )

            schedule = create_schedule(
                command.schedule_id,
                command.protocol_id,
                command.arguments[
                    "schedule_type"
                ],
                timezone=command.arguments.get(
                    "timezone",
                    default_timezone,
                ),
                hour=command.arguments.get(
                    "hour"
                ),
                minute=command.arguments.get(
                    "minute"
                ),
                weekdays=command.arguments.get(
                    "weekdays"
                ),
                overwrite=True,
            )
        except Exception as error:
            return {
                "handled": True,
                "response": (
                    "I could not create that schedule: "
                    f"{error}"
                ),
                "follow_up": "",
            }

        return {
            "handled": True,
            "response": (
                f"Scheduled {command.protocol_id} as "
                f"{schedule['schedule_id']}. "
                f"Next run: {_format_schedule_next_run(schedule)}."
            ),
            "follow_up": "",
        }


    if command.action == "list_active_runs":
        runs = _active_runs()

        if not runs:
            response = (
                "There are no active workflows."
            )
        else:
            response = "\n\n".join(
                _format_run_state(
                    run
                )
                for run
                in runs
            )

        return {
            "handled": True,
            "response": response,
            "follow_up": "",
        }


    if command.action == "resume_active_run":
        run = _single_active_run()

        if run is None:
            return {
                "handled": True,
                "response": _active_run_error(),
                "follow_up": "",
            }

        try:
            resumed = resume_workflow_run(
                run.run_id
            )
        except Exception as error:
            return {
                "handled": True,
                "response": (
                    "I could not resume the workflow: "
                    f"{error}"
                ),
                "follow_up": "",
            }

        return {
            "handled": True,
            "response": (
                format_workflow_outputs(
                    resumed
                )
                if resumed.status == "completed"
                else _format_run_state(
                    resumed
                )
            ),
            "follow_up": "",
        }


    if command.action == "cancel_active_run":
        run = _single_active_run()

        if run is None:
            return {
                "handled": True,
                "response": _active_run_error(),
                "follow_up": "",
            }

        cancelled = cancel_workflow_run(
            run.run_id
        )

        return {
            "handled": True,
            "response": (
                "Workflow cancelled."
                if cancelled
                else "I could not cancel the workflow."
            ),
            "follow_up": "",
        }


    if command.action == "recover_active_run":
        run = _single_active_run()

        if run is None:
            return {
                "handled": True,
                "response": _active_run_error(),
                "follow_up": "",
            }

        try:
            recovered = resume_workflow_run(
                run.run_id,
                recovery_action=command.arguments[
                    "recovery_action"
                ],
            )
        except Exception as error:
            return {
                "handled": True,
                "response": (
                    "I could not apply that workflow recovery action: "
                    f"{error}"
                ),
                "follow_up": "",
            }

        return {
            "handled": True,
            "response": (
                format_workflow_outputs(
                    recovered
                )
                if recovered.status == "completed"
                else _format_run_state(
                    recovered
                )
            ),
            "follow_up": "",
        }


    return {
        "handled": False,
        "response": None,
        "follow_up": "",
    }
