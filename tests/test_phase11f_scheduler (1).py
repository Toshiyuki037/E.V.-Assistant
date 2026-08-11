"""
Phase 11F deterministic scheduler tests.
"""

from datetime import (
    datetime,
    timezone,
)

import assistant.workflows.schedules as schedules

from assistant.workflows.scheduler import (
    schedule_is_due,
)


def test_daily_schedule_next_run(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(
        schedules,
        "SCHEDULE_DIRECTORY",
        tmp_path
        / "schedules",
    )


    data = schedules.create_schedule(
        "morning-test",
        "morning",
        "daily",
        timezone="UTC",
        hour=8,
        minute=0,
    )


    assert (
        data[
            "schedule_type"
        ]
        == "daily"
    )

    assert data[
        "next_run_at"
    ]


def test_schedule_due_detection():
    schedule = {
        "enabled":
            True,

        "next_run_at":
            (
                "2026-08-10"
                "T10:00:00+00:00"
            ),
    }


    assert schedule_is_due(
        schedule,
        now=datetime(
            2026,
            8,
            10,
            10,
            1,
            tzinfo=timezone.utc,
        ),
    )


def test_schedule_not_due_when_disabled():
    schedule = {
        "enabled":
            False,

        "next_run_at":
            (
                "2026-08-10"
                "T10:00:00+00:00"
            ),
    }


    assert not schedule_is_due(
        schedule,
        now=datetime(
            2026,
            8,
            10,
            10,
            1,
            tzinfo=timezone.utc,
        ),
    )


def test_weekly_schedule_validation(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(
        schedules,
        "SCHEDULE_DIRECTORY",
        tmp_path
        / "schedules",
    )


    data = schedules.create_schedule(
        "weekday-test",
        "morning",
        "weekly",
        timezone=(
            "America/Los_Angeles"
        ),
        hour=7,
        minute=30,
        weekdays=[
            "monday",
            "tuesday",
            "wednesday",
            "thursday",
            "friday",
        ],
    )


    assert len(
        data[
            "weekdays"
        ]
    ) == 5


def test_one_time_schedule_disables_after_run(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(
        schedules,
        "SCHEDULE_DIRECTORY",
        tmp_path
        / "schedules",
    )


    schedules.create_schedule(
        "once-test",
        "morning",
        "once",
        timezone="UTC",
        run_at=(
            "2099-01-01"
            "T12:00:00+00:00"
        ),
    )


    updated = schedules.mark_schedule_run(
        "once-test",
        run_id="run_test",
        status="completed",
        completed_at=datetime(
            2099,
            1,
            1,
            12,
            0,
            tzinfo=timezone.utc,
        ),
    )


    assert updated[
        "enabled"
    ] is False

    assert updated[
        "next_run_at"
    ] == ""
