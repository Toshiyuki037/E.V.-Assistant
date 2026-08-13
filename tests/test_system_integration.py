from assistant.system.integration import (
    handle_system_message,
)


def test_version_routes_to_system():
    result = (
        handle_system_message(
            "What version are you?"
        )
    )

    assert result["handled"] is True
    assert "version" in result["response"].lower()


def test_unknown_conversation_yields():
    result = (
        handle_system_message(
            "Tell me about transistors."
        )
    )

    assert result["handled"] is False


def test_capabilities_route():
    result = (
        handle_system_message(
            "What can you do?"
        )
    )

    assert result["handled"] is True
    assert "capabilities" in result["response"].lower()


def test_unknown_repair_component_fails_closed():
    result = (
        handle_system_message(
            "prepare repair teleportation.engine"
        )
    )

    assert result["handled"] is True
    assert "no architecture ownership record" in result["response"].lower()
