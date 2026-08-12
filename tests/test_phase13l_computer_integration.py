
import pytest

import assistant.computer.integration as integration
import assistant.computer.integration_runtime as runtime
from assistant.computer.integration_planner import (
    plan_computer_message,
)


def test_focus_notepad_routes_to_native_control():
    plan = plan_computer_message(
        "focus Notepad"
    )

    assert plan.handled is True
    assert plan.action == "window.focus"
    assert plan.target == "Notepad"


def test_open_display_settings_routes_to_safe_settings():
    plan = plan_computer_message(
        "open display settings"
    )

    assert plan.handled is True
    assert plan.action == "settings.open"
    assert plan.target == "display"


def test_type_into_notepad_routes_to_structured_accessibility():
    plan = plan_computer_message(
        "type hello world into Notepad"
    )

    assert plan.handled is True
    assert plan.action == "accessibility.set_value"
    assert plan.target == "Notepad"
    assert (
        plan.arguments["selector"]["control_type"]
        == "Document"
    )


def test_unrelated_conversation_falls_through():
    plan = plan_computer_message(
        "what do you think about embedded systems?"
    )

    assert plan.handled is False


def test_integration_executes_planned_action(
    monkeypatch,
):
    seen = {}

    def fake_execute(
        plan,
        *,
        browser_session=None,
    ):
        seen["action"] = plan.action
        seen["target"] = plan.target

        return {
            "success": True,
            "action": plan.action,
            "method": "native",
            "verified": True,
            "result": {},
            "attempts": [],
            "detail": "",
        }

    monkeypatch.setattr(
        integration,
        "execute_computer_plan",
        fake_execute,
    )

    result = integration.handle_computer_message(
        "focus Notepad"
    )

    assert result["handled"] is True
    assert seen["action"] == "window.focus"
    assert seen["target"] == "Notepad"
    assert "verified" in result["response"]


def test_vision_capture_uses_specialized_capture_path(
    monkeypatch,
):
    monkeypatch.setattr(
        runtime,
        "capture_local_monitor",
        lambda path, monitor_index=1: {
            "path": path,
            "width": 1920,
            "height": 1080,
            "success": True,
        },
    )

    plan = plan_computer_message(
        "take a screenshot"
    )

    result = runtime.execute_computer_plan(
        plan
    )

    assert result["success"] is True
    assert result["method"] == "vision"
    assert result["verified"] is True
