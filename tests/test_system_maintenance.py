from assistant.system.maintenance import (
    list_maintenance_actions,
    run_maintenance_action,
)


def test_unknown_maintenance_action_fails_closed():
    result = (
        run_maintenance_action(
            "invented action"
        )
    )

    assert result.success is False
    assert result.detail == "Unknown maintenance action."


def test_action_registry_contains_safe_actions():
    actions = (
        list_maintenance_actions()
    )

    assert "clear_stale_agent_state" in actions
    assert "reload_tool_registry" in actions
    assert "ensure_runtime_directories" in actions
    assert "prune_telemetry" in actions


def test_runtime_directory_maintenance():
    result = (
        run_maintenance_action(
            "ensure runtime directories"
        )
    )

    assert result.success is True
    assert result.action == "ensure_runtime_directories"
