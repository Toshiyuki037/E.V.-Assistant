"""
E.V.I.E. - Persistent Workflow Schedules

Phase 11F

Purpose:
Store one-time and recurring protocol schedules persistently.

Storage:
    runtime/workflows/schedules/<schedule_id>.json

Supported schedule types:
    once
    daily
    weekly

Safety:
Scheduling a protocol never grants approval to the protocol's actions.
The normal Phase 11 -> Phase 6 permission path remains authoritative.
"""

from __future__ import annotations

import json
import re

from copy import deepcopy
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo


SCHEDULE_DIRECTORY = (
    Path("runtime")
    / "workflows"
    / "schedules"
)


WEEKDAY_NAMES = (
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _slug(
    value: str,
):
    value = re.sub(
        r"[^a-zA-Z0-9_-]+",
        "-",
        str(
            value
            or ""
        ).strip(),
    )

    value = (
        value
        .strip("-")
        .lower()
    )

    return (
        value
        or "schedule"
    )


def _now_utc():
    return (
        datetime.now(
            ZoneInfo(
                "UTC"
            )
        )
    )


def _iso(
    value: datetime | None,
):
    if value is None:

        return ""

    return value.isoformat()


def _parse_iso(
    value: str,
):
    if not value:

        return None

    return datetime.fromisoformat(
        value
    )


def _path(
    schedule_id: str,
):
    return (
        SCHEDULE_DIRECTORY
        / f"{_slug(schedule_id)}.json"
    )


def _ensure_directory():
    SCHEDULE_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )


def _write(
    data: dict[str, Any],
):
    _ensure_directory()

    path = _path(
        data[
            "schedule_id"
        ]
    )

    temp = path.with_suffix(
        ".json.tmp"
    )

    temp.write_text(
        json.dumps(
            data,
            indent=2,
            ensure_ascii=False,
            default=str,
        ),
        encoding="utf-8",
    )

    temp.replace(
        path
    )

    return data


def _read(
    schedule_id: str,
):
    path = _path(
        schedule_id
    )

    if not path.exists():

        raise RuntimeError(
            (
                "Schedule does not exist: "
                f"{schedule_id}"
            )
        )

    data = json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )

    if not isinstance(
        data,
        dict,
    ):

        raise RuntimeError(
            (
                "Schedule file is invalid: "
                f"{schedule_id}"
            )
        )

    return data


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_schedule(
    data: dict[str, Any],
):
    schedule_type = (
        str(
            data.get(
                "schedule_type",
                ""
            )
            or ""
        )
        .strip()
        .lower()
    )


    if schedule_type not in {
        "once",
        "daily",
        "weekly",
    }:

        raise ValueError(
            (
                "Unsupported schedule type: "
                f"{schedule_type}"
            )
        )


    timezone_name = (
        str(
            data.get(
                "timezone",
                "UTC",
            )
            or "UTC"
        )
    )


    try:

        ZoneInfo(
            timezone_name
        )

    except Exception as error:

        raise ValueError(
            (
                "Invalid timezone: "
                f"{timezone_name}"
            )
        ) from error


    if not str(
        data.get(
            "protocol_id",
            ""
        )
        or ""
    ).strip():

        raise ValueError(
            "Schedule requires protocol_id."
        )


    if schedule_type == "once":

        if not data.get(
            "run_at"
        ):

            raise ValueError(
                "One-time schedule requires run_at."
            )


    if schedule_type in {
        "daily",
        "weekly",
    }:

        hour = int(
            data.get(
                "hour",
                -1,
            )
        )

        minute = int(
            data.get(
                "minute",
                -1,
            )
        )


        if not (
            0 <= hour <= 23
        ):

            raise ValueError(
                "Schedule hour must be 0-23."
            )


        if not (
            0 <= minute <= 59
        ):

            raise ValueError(
                "Schedule minute must be 0-59."
            )


    if schedule_type == "weekly":

        weekdays = (
            data.get(
                "weekdays",
                []
            )
            or []
        )


        if not weekdays:

            raise ValueError(
                "Weekly schedule requires weekdays."
            )


        for day in weekdays:

            if (
                str(
                    day
                )
                .strip()
                .lower()
                not in WEEKDAY_NAMES
            ):

                raise ValueError(
                    (
                        "Invalid weekday: "
                        f"{day}"
                    )
                )


    return True


# ---------------------------------------------------------------------------
# Next Run Calculation
# ---------------------------------------------------------------------------

def calculate_next_run(
    data: dict[str, Any],
    after: datetime | None = None,
):
    validate_schedule(
        data
    )

    timezone_name = (
        data.get(
            "timezone",
            "UTC",
        )
    )

    zone = ZoneInfo(
        timezone_name
    )


    if after is None:

        after = _now_utc()


    if after.tzinfo is None:

        after = after.replace(
            tzinfo=ZoneInfo(
                "UTC"
            )
        )


    local_after = (
        after.astimezone(
            zone
        )
    )

    schedule_type = (
        data[
            "schedule_type"
        ]
    )


    if schedule_type == "once":

        run_at = _parse_iso(
            data[
                "run_at"
            ]
        )


        if run_at is None:

            return None


        if run_at.tzinfo is None:

            run_at = run_at.replace(
                tzinfo=zone
            )


        if (
            run_at.astimezone(
                ZoneInfo(
                    "UTC"
                )
            )
            <= after.astimezone(
                ZoneInfo(
                    "UTC"
                )
            )
        ):

            return None


        return run_at.astimezone(
            ZoneInfo(
                "UTC"
            )
        )


    hour = int(
        data[
            "hour"
        ]
    )

    minute = int(
        data[
            "minute"
        ]
    )


    candidate = (
        local_after.replace(
            hour=hour,
            minute=minute,
            second=0,
            microsecond=0,
        )
    )


    if schedule_type == "daily":

        if candidate <= local_after:

            candidate = (
                candidate
                + timedelta(
                    days=1
                )
            )


        return candidate.astimezone(
            ZoneInfo(
                "UTC"
            )
        )


    weekdays = {
        WEEKDAY_NAMES.index(
            str(
                day
            )
            .strip()
            .lower()
        )
        for day
        in data[
            "weekdays"
        ]
    }


    for offset in range(
        0,
        8,
    ):

        candidate_day = (
            local_after
            + timedelta(
                days=offset
            )
        )


        if (
            candidate_day.weekday()
            not in weekdays
        ):

            continue


        candidate = (
            candidate_day.replace(
                hour=hour,
                minute=minute,
                second=0,
                microsecond=0,
            )
        )


        if candidate <= local_after:

            continue


        return candidate.astimezone(
            ZoneInfo(
                "UTC"
            )
        )


    return None


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------

def create_schedule(
    schedule_id: str,
    protocol_id: str,
    schedule_type: str,
    *,
    timezone: str = "UTC",
    run_at: str = "",
    hour: int | None = None,
    minute: int | None = None,
    weekdays: list[str] | None = None,
    variables: dict[str, Any] | None = None,
    enabled: bool = True,
    missed_run_policy: str = "run_once",
    overwrite: bool = False,
):
    schedule_id = _slug(
        schedule_id
    )

    path = _path(
        schedule_id
    )


    if (
        path.exists()
        and not overwrite
    ):

        raise RuntimeError(
            (
                "Schedule already exists: "
                f"{schedule_id}"
            )
        )


    now = _now_utc()


    data = {
        "schedule_id":
            schedule_id,

        "protocol_id":
            str(
                protocol_id
            ).strip(),

        "schedule_type":
            str(
                schedule_type
            ).strip()
            .lower(),

        "timezone":
            str(
                timezone
                or "UTC"
            ),

        "run_at":
            str(
                run_at
                or ""
            ),

        "hour":
            hour,

        "minute":
            minute,

        "weekdays":
            [
                str(
                    day
                )
                .strip()
                .lower()
                for day
                in (
                    weekdays
                    or []
                )
            ],

        "variables":
            deepcopy(
                variables
                or {}
            ),

        "enabled":
            bool(
                enabled
            ),

        "missed_run_policy":
            str(
                missed_run_policy
                or "run_once"
            ),

        "created_at":
            _iso(
                now
            ),

        "updated_at":
            _iso(
                now
            ),

        "last_run_at":
            "",

        "last_run_id":
            "",

        "last_status":
            "",

        "next_run_at":
            "",
    }


    validate_schedule(
        data
    )


    next_run = (
        calculate_next_run(
            data,
            after=(
                now
                - timedelta(
                    microseconds=1
                )
            ),
        )
    )


    data[
        "next_run_at"
    ] = _iso(
        next_run
    )


    return _write(
        data
    )


def get_schedule(
    schedule_id: str,
):
    return _read(
        schedule_id
    )


def list_schedules(
    include_disabled: bool = True,
):
    _ensure_directory()

    schedules = []


    for path in sorted(
        SCHEDULE_DIRECTORY.glob(
            "*.json"
        )
    ):

        try:

            data = json.loads(
                path.read_text(
                    encoding="utf-8"
                )
            )

        except Exception:

            continue


        if (
            include_disabled
            or data.get(
                "enabled",
                True,
            )
        ):

            schedules.append(
                data
            )


    return schedules


def update_schedule(
    schedule_id: str,
    **changes: Any,
):
    data = _read(
        schedule_id
    )


    protected = {
        "schedule_id",
        "created_at",
    }


    for key, value in (
        changes.items()
    ):

        if (
            key not in protected
            and value is not None
        ):

            data[
                key
            ] = deepcopy(
                value
            )


    data[
        "updated_at"
    ] = _iso(
        _now_utc()
    )


    validate_schedule(
        data
    )


    next_run = (
        calculate_next_run(
            data
        )
        if data.get(
            "enabled",
            True,
        )
        else None
    )


    data[
        "next_run_at"
    ] = _iso(
        next_run
    )


    return _write(
        data
    )


def set_schedule_enabled(
    schedule_id: str,
    enabled: bool,
):
    return update_schedule(
        schedule_id,
        enabled=bool(
            enabled
        ),
    )


def delete_schedule(
    schedule_id: str,
):
    path = _path(
        schedule_id
    )


    if not path.exists():

        return False


    path.unlink()

    return True


# ---------------------------------------------------------------------------
# Runtime Updates
# ---------------------------------------------------------------------------

def mark_schedule_run(
    schedule_id: str,
    *,
    run_id: str,
    status: str,
    completed_at: datetime | None = None,
):
    data = _read(
        schedule_id
    )

    completed_at = (
        completed_at
        or _now_utc()
    )


    data[
        "last_run_at"
    ] = _iso(
        completed_at
    )

    data[
        "last_run_id"
    ] = str(
        run_id
        or ""
    )

    data[
        "last_status"
    ] = str(
        status
        or ""
    )


    if (
        data[
            "schedule_type"
        ]
        == "once"
    ):

        data[
            "enabled"
        ] = False

        data[
            "next_run_at"
        ] = ""


    else:

        data[
            "next_run_at"
        ] = _iso(
            calculate_next_run(
                data,
                after=completed_at,
            )
        )


    data[
        "updated_at"
    ] = _iso(
        _now_utc()
    )


    return _write(
        data
    )
