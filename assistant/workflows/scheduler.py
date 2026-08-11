"""
E.V.I.E. - Workflow Scheduler

Phase 11F

Purpose:
Find due persistent schedules and trigger their saved protocols.

Architecture:
The scheduler remains lightweight while idle.

Protocol/workflow execution is imported lazily only when a schedule
actually becomes due.
"""

from __future__ import annotations

from datetime import (
    datetime,
    timezone,
)

from typing import Any

from .schedules import (
    list_schedules,
    mark_schedule_run,
)


# ---------------------------------------------------------------------------
# Time
# ---------------------------------------------------------------------------

def _utc_now():

    return datetime.now(
        timezone.utc
    )


def _parse(
    value: str,
):

    if not value:

        return None


    result = (
        datetime.fromisoformat(
            value
        )
    )


    if result.tzinfo is None:

        result = (
            result.replace(
                tzinfo=
                    timezone.utc
            )
        )


    return result.astimezone(
        timezone.utc
    )


# ---------------------------------------------------------------------------
# Due Check
# ---------------------------------------------------------------------------

def schedule_is_due(
    schedule: dict[str, Any],
    now: datetime | None = None,
):

    if not schedule.get(
        "enabled",
        True,
    ):

        return False


    next_run = (
        _parse(
            schedule.get(
                "next_run_at",
                "",
            )
        )
    )


    if next_run is None:

        return False


    now = (
        now
        or _utc_now()
    )


    if now.tzinfo is None:

        now = (
            now.replace(
                tzinfo=
                    timezone.utc
            )
        )


    return (
        next_run
        <= now.astimezone(
            timezone.utc
        )
    )


# ---------------------------------------------------------------------------
# Lazy Protocol Loader
# ---------------------------------------------------------------------------

def _run_protocol(
    protocol_id: str,
    variables: dict,
):
    """
    Import workflow/protocol execution only when a scheduled task
    actually needs to run.

    The idle scheduler therefore stays extremely lightweight.
    """

    from .protocols import (
        run_protocol,
    )


    return run_protocol(
        protocol_id,
        variables=
            variables,
    )


# ---------------------------------------------------------------------------
# Execute One Schedule
# ---------------------------------------------------------------------------

def execute_due_schedule(
    schedule: dict[str, Any],
):

    protocol_id = (
        schedule[
            "protocol_id"
        ]
    )


    variables = (
        schedule.get(
            "variables",
            {},
        )
        or {}
    )


    try:

        run = (
            _run_protocol(
                protocol_id,
                variables,
            )
        )


        mark_schedule_run(
            schedule[
                "schedule_id"
            ],

            run_id=
                run.run_id,

            status=
                run.status,
        )


        return {
            "schedule_id":
                schedule[
                    "schedule_id"
                ],

            "protocol_id":
                protocol_id,

            "success":
                True,

            "run_id":
                run.run_id,

            "status":
                run.status,
        }


    except Exception as error:

        mark_schedule_run(
            schedule[
                "schedule_id"
            ],

            run_id=
                "",

            status=(
                "error: "
                + str(
                    error
                )
            ),
        )


        return {
            "schedule_id":
                schedule[
                    "schedule_id"
                ],

            "protocol_id":
                protocol_id,

            "success":
                False,

            "run_id":
                "",

            "status":
                "error",

            "error":
                str(
                    error
                ),
        }


# ---------------------------------------------------------------------------
# Scheduler Tick
# ---------------------------------------------------------------------------

def scheduler_tick(
    now: datetime | None = None,
):

    now = (
        now
        or _utc_now()
    )


    results = []


    for schedule in (
        list_schedules(
            include_disabled=False
        )
    ):

        if (
            schedule_is_due(
                schedule,
                now=now,
            )
        ):

            results.append(
                execute_due_schedule(
                    schedule
                )
            )


    return results


# ---------------------------------------------------------------------------
# Inspection
# ---------------------------------------------------------------------------

def get_due_schedules(
    now: datetime | None = None,
):

    now = (
        now
        or _utc_now()
    )


    return [
        schedule

        for schedule
        in list_schedules(
            include_disabled=False
        )

        if schedule_is_due(
            schedule,
            now=now,
        )
    ]