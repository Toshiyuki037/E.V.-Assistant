
from assistant.voice.wake import (
    extract_wake_request,
    is_sleep_command,
)


def test_wake_word_and_inline_request():
    assert extract_wake_request("Evie") == (True, "")
    assert extract_wake_request(
        "Evie, what's on my calendar?"
    ) == (
        True,
        "what's on my calendar",
    )


def test_sleep_commands():
    assert is_sleep_command("Go to sleep.")
    assert is_sleep_command("Stand by.")
