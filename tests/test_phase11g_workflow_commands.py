"""
Phase 11G deterministic natural-language workflow tests.
"""

from assistant.workflows.integration import (
    _format_schedules,
)

from assistant.workflows.planner import (
    plan_workflow_command,
)


def test_run_protocol_command():
    plan = plan_workflow_command(
        "Run my morning protocol."
    )

    assert plan.handled
    assert plan.action == "run_protocol"
    assert plan.protocol_id == "morning"


def test_list_protocols_command():
    plan = plan_workflow_command(
        "What protocols do I have?"
    )

    assert plan.handled
    assert plan.action == "list_protocols"


def test_disable_protocol_command():
    plan = plan_workflow_command(
        "Disable my research protocol."
    )

    assert plan.handled
    assert plan.action == "disable_protocol"
    assert plan.protocol_id == "research"


def test_weekday_schedule_command():
    plan = plan_workflow_command(
        (
            "Schedule my morning protocol "
            "every weekday at 7:30 AM."
        ),
        default_timezone=(
            "America/Los_Angeles"
        ),
    )

    assert plan.handled
    assert plan.action == "create_schedule"
    assert plan.protocol_id == "morning"
    assert plan.arguments["schedule_type"] == "weekly"
    assert plan.arguments["hour"] == 7
    assert plan.arguments["minute"] == 30
    assert len(
        plan.arguments[
            "weekdays"
        ]
    ) == 5


def test_daily_schedule_command():
    plan = plan_workflow_command(
        (
            "Schedule my research protocol "
            "every day at 6 PM."
        )
    )

    assert plan.handled
    assert plan.action == "create_schedule"
    assert plan.arguments["schedule_type"] == "daily"
    assert plan.arguments["hour"] == 18
    assert plan.arguments["minute"] == 0


def test_list_running_workflows():
    plan = plan_workflow_command(
        "What workflows are running?"
    )

    assert plan.handled
    assert plan.action == "list_active_runs"


def test_retry_workflow_step():
    plan = plan_workflow_command(
        "Retry that workflow step."
    )

    assert plan.handled
    assert plan.action == "recover_active_run"
    assert (
        plan.arguments[
            "recovery_action"
        ]
        == "retry"
    )


def test_unrelated_message_falls_through():
    plan = plan_workflow_command(
        "Explain FPGA timing closure."
    )

    assert not plan.handled


def test_schedule_response_formats_next_run_in_schedule_timezone():
    response = _format_schedules(
        [
            {
                "schedule_id": "morning-schedule",
                "protocol_id": "morning",
                "enabled": True,
                "timezone": "America/Los_Angeles",
                "next_run_at": "2026-08-11T14:30:00+00:00",
            }
        ]
    )

    assert "2026-08-11T14:30:00+00:00" not in response
    assert "2026-08-11 7:30 AM" in response

    # Display-only improvement: include explicit UTC offset in the suffix.
    # August is DST for America/Los_Angeles, so it should be UTC-07:00.
    assert "America/Los_Angeles (UTC-07:00)" in response
