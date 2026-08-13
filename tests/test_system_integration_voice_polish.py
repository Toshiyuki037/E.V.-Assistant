from assistant.system.integration import (
    _normalize,
    handle_system_message,
)


def test_filler_words_do_not_block_health_command():
    result = (
        handle_system_message(
            "Um, are you healthy?"
        )
    )

    assert result["handled"] is True
    assert "overall system health" in result["response"].lower()
    assert "healthy systems" in result["response"].lower()


def test_multiple_fillers_do_not_block_health_command():
    result = (
        handle_system_message(
            "Okay, um, Evie, are you healthy please?"
        )
    )

    assert result["handled"] is True
    assert "overall system health" in result["response"].lower()


def test_stt_version_alias():
    result = (
        handle_system_message(
            "What vision are you?"
        )
    )

    assert result["handled"] is True
    assert "version" in result["response"].lower()


def test_filler_does_not_rewrite_ordinary_conversation():
    result = (
        handle_system_message(
            "Um, tell me about transistors."
        )
    )

    assert result["handled"] is False


def test_capabilities_still_route():
    result = (
        handle_system_message(
            "Hey Evie, what can you do?"
        )
    )

    assert result["handled"] is True
    assert "capabilities" in result["response"].lower()


def test_normalize_filler():
    assert (
        _normalize(
            "Okay, um, Evie, run a diagnostic please."
        )
        == "run a diagnostic"
    )
