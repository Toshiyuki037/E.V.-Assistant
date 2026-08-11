"""
E.V.I.E. - Phase 11 Final Regression Tests
"""

from types import SimpleNamespace

import assistant.workflows.protocols as protocols

from assistant.workflows.authoring import (
    add_action_to_protocol,
    create_protocol_from_actions,
    describe_protocol,
    remove_action_from_protocol,
)

from assistant.workflows.planner import (
    plan_workflow_command,
)

from assistant.workflows.presentation import (
    format_workflow_outputs,
)


def test_create_protocol_command_parsing():
    plan = plan_workflow_command(
        (
            "Create a protocol called College Morning "
            "that checks the weather."
        )
    )

    assert plan.handled
    assert plan.action == "create_protocol"
    assert plan.protocol_id == "college-morning"
    assert plan.arguments["actions"] == ["weather"]


def test_describe_protocol_command_parsing():
    plan = plan_workflow_command(
        "What does my morning protocol do?"
    )

    assert plan.handled
    assert plan.action == "describe_protocol"
    assert plan.protocol_id == "morning"


def test_add_github_to_protocol_parsing():
    plan = plan_workflow_command(
        (
            "Add GitHub commits to my "
            "research protocol."
        )
    )

    assert plan.handled
    assert plan.action == "add_protocol_actions"
    assert plan.arguments["actions"] == ["github_commits"]


def test_remove_weather_from_protocol_parsing():
    plan = plan_workflow_command(
        (
            "Remove weather from my "
            "morning protocol."
        )
    )

    assert plan.handled
    assert plan.action == "remove_protocol_actions"
    assert plan.arguments["actions"] == ["weather"]


def test_delete_protocol_parsing():
    plan = plan_workflow_command(
        "Delete my College Morning protocol."
    )

    assert plan.handled
    assert plan.action == "delete_protocol"
    assert plan.protocol_id == "college-morning"


def test_protocol_authoring_round_trip(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(
        protocols,
        "PROTOCOL_DIR",
        tmp_path / "protocols",
    )

    created = create_protocol_from_actions(
        protocol_id="college-morning",
        name="College Morning",
        goal="Prepare for college.",
        actions=["weather"],
        default_variables={
            "location": "Corvallis",
        },
    )

    assert created["protocol_id"] == "college-morning"
    assert len(created["steps"]) == 1

    text = describe_protocol(
        "college-morning"
    )

    assert "College Morning" in text
    assert "Read current weather" in text

    add_action_to_protocol(
        "college-morning",
        "github_commits",
    )

    updated = protocols.get_protocol(
        "college-morning"
    )

    assert len(updated["steps"]) == 2

    remove_action_from_protocol(
        "college-morning",
        "weather",
    )

    updated = protocols.get_protocol(
        "college-morning"
    )

    assert len(updated["steps"]) == 1
    assert (
        updated["steps"][0]["output_key"]
        == "github_commits"
    )


def test_workflow_output_formatter_weather():
    run = SimpleNamespace(
        workflow_name="Morning Protocol",
        status="completed",
        outputs={
            "weather": {
                "evidence": [
                    {
                        "data": {
                            "location": "Corvallis",
                            "temperature_f": 61,
                            "condition": "clear",
                            "humidity": 45,
                        }
                    }
                ]
            }
        },
        awaiting_user_reason="",
        pending_action=None,
    )

    text = format_workflow_outputs(
        run
    )

    assert "Morning Protocol completed." in text
    assert "Corvallis" in text
    assert "61°F" in text


def test_workflow_output_formatter_github():
    run = SimpleNamespace(
        workflow_name="Research Protocol",
        status="completed",
        outputs={
            "github_commits": {
                "evidence": [
                    {
                        "data": {
                            "commits": [
                                {
                                    "sha": "abcdef123456",
                                    "message": "Complete Phase 11",
                                }
                            ]
                        }
                    }
                ]
            }
        },
        awaiting_user_reason="",
        pending_action=None,
    )

    text = format_workflow_outputs(
        run
    )

    assert "abcdef1" in text
    assert "Complete Phase 11" in text


def test_unrelated_request_still_falls_through():
    plan = plan_workflow_command(
        "Explain FPGA timing closure."
    )

    assert not plan.handled
