"""
Phase 14B persistent voice-session tests.

No microphone, CUDA, Whisper, F5-TTS, or reasoning model is required.
"""

from assistant.voice.session import (
    classify_voice_session_command,
    normalize_voice_command,
    run_voice_session,
)


# ---------------------------------------------------------------------------
# Command Normalization
# ---------------------------------------------------------------------------

def test_normalize_voice_command():

    assert (
        normalize_voice_command(
            "  Stop   Listening! "
        )
        == "stop listening"
    )


# ---------------------------------------------------------------------------
# Session Command Classification
# ---------------------------------------------------------------------------

def test_stop_listening_returns_to_mode():

    assert (
        classify_voice_session_command(
            "stop listening"
        )
        == "return_to_mode"
    )


def test_goodbye_quits_application():

    assert (
        classify_voice_session_command(
            "Goodbye."
        )
        == "quit_application"
    )


def test_normal_prompt_is_not_session_command():

    assert (
        classify_voice_session_command(
            "What is a transistor?"
        )
        is None
    )


# ---------------------------------------------------------------------------
# Persistent Loop
# ---------------------------------------------------------------------------

def test_multiple_prompts_are_processed_in_one_session():

    utterances = iter(
        [
            "What is two plus two?",
            "What is a transistor?",
            "stop listening",
        ]
    )


    processed = []


    result = (
        run_voice_session(
            listen_fn=
                lambda: next(
                    utterances
                ),

            process_prompt_fn=
                processed.append,
        )
    )


    assert processed == [
        "What is two plus two?",
        "What is a transistor?",
    ]


    assert (
        result.quit_application
        is False
    )


    assert (
        result.reason
        == "return_to_mode"
    )


def test_empty_transcription_does_not_end_session():

    utterances = iter(
        [
            "",
            "",
            "Hello E.V.I.E.",
            "stop listening",
        ]
    )


    processed = []


    result = (
        run_voice_session(
            listen_fn=
                lambda: next(
                    utterances
                ),

            process_prompt_fn=
                processed.append,
        )
    )


    assert processed == [
        "Hello E.V.I.E."
    ]


    assert (
        result.quit_application
        is False
    )


def test_quit_command_requests_application_shutdown():

    utterances = iter(
        [
            "goodbye",
        ]
    )


    processed = []


    result = (
        run_voice_session(
            listen_fn=
                lambda: next(
                    utterances
                ),

            process_prompt_fn=
                processed.append,
        )
    )


    assert processed == []


    assert (
        result.quit_application
        is True
    )


    assert (
        result.reason
        == "quit_application"
    )


def test_stop_is_not_interpreted_as_voice_mode_exit():

    assert (
        classify_voice_session_command(
            "stop"
        )
        is None
    )


def test_never_mind_is_not_interpreted_as_voice_mode_exit():

    assert (
        classify_voice_session_command(
            "never mind"
        )
        is None
    )