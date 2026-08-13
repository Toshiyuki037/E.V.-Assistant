from assistant.voice.response_length import (
    apply_response_length_policy,
    choose_response_length_policy,
    explicitly_requests_detail,
)


def test_normal_voice_is_concise():
    policy = (
        choose_response_length_policy(
            "How do transistors work?",
            voice_mode=
                True,
        )
    )

    assert policy.mode == "concise"
    assert policy.maximum_words <= 130


def test_exactly_does_not_mean_exhaustive():
    policy = (
        choose_response_length_policy(
            "Explain exactly what your system is doing right now.",
            voice_mode=
                True,
        )
    )

    assert policy.mode == "concise"


def test_explicit_detail_gets_detailed_mode():
    policy = (
        choose_response_length_policy(
            "Explain how transistors work in extreme detail.",
            voice_mode=
                True,
        )
    )

    assert policy.mode == "detailed"
    assert policy.maximum_words >= 400


def test_health_and_error_requests_preserve_important_information():
    health = (
        choose_response_length_policy(
            "Are you healthy?",
            voice_mode=
                True,
        )
    )

    error = (
        choose_response_length_policy(
            "Why did the tool fail?",
            voice_mode=
                True,
        )
    )

    assert health.mode == "important"
    assert error.mode == "important"
    assert "NEVER omit" in health.instruction


def test_policy_does_not_replace_original_request():
    original = (
        "What is my current bottleneck?"
    )

    augmented = (
        apply_response_length_policy(
            original,
            voice_mode=
                True,
        )
    )

    assert augmented.startswith(
        original
    )

    assert (
        "INTERNAL RUNTIME INSTRUCTION"
        in augmented
    )


def test_terminal_is_not_forced_into_voice_budget():
    policy = (
        choose_response_length_policy(
            "Explain this architecture.",
            voice_mode=
                False,
        )
    )

    assert policy.mode == "standard"
    assert policy.maximum_words > 130
