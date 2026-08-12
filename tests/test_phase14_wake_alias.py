from assistant.voice.wake import extract_wake_request


def test_eevee_is_valid_stt_wake_alias():
    assert extract_wake_request("Eevee") == (True, "")
    assert extract_wake_request(
        "Eevee, what's the weather today?"
    ) == (
        True,
        "what's the weather today",
    )
