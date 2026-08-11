"""
Phase 11G deterministic natural-language workflow tests.
"""

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
