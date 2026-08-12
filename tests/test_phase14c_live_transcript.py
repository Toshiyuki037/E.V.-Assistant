"""
E.V.I.E. Phase 14C3 live transcript integration tests.
"""

from assistant.listen import (
    LiveTranscriptController,
)

from assistant.voice.transcription import (
    TranscriptEvent,
    TranscriptionResult,
)


def partial_event(
    text,
    *,
    language="en",
):
    return (
        TranscriptEvent(
            kind="partial",

            text=text,

            language=language,

            language_probability=0.99,

            timestamp=0.0,

            audio_seconds=1.0,
        )
    )


def test_live_controller_tracks_partial_text():

    controller = (
        LiveTranscriptController(
            required_stability=2
        )
    )


    update = (
        controller.handle_partial(
            partial_event(
                "What is a transistor"
            )
        )
    )


    assert (
        update.committed_text
        == ""
    )

    assert (
        update.unstable_text
        == "What is a transistor"
    )


def test_live_controller_commits_stable_sentence():

    controller = (
        LiveTranscriptController(
            required_stability=2
        )
    )


    controller.handle_partial(
        partial_event(
            "A transistor is a switch."
        )
    )


    update = (
        controller.handle_partial(
            partial_event(
                "A transistor is a switch."
            )
        )
    )


    assert (
        update.newly_committed
        == (
            "A transistor is a switch.",
        )
    )


def test_live_controller_preserves_committed_prefix():

    controller = (
        LiveTranscriptController(
            required_stability=2
        )
    )


    controller.handle_partial(
        partial_event(
            "Sentence one."
        )
    )

    controller.handle_partial(
        partial_event(
            "Sentence one."
        )
    )


    update = (
        controller.handle_partial(
            partial_event(
                "Sentence one. Sentence two"
            )
        )
    )


    assert (
        update.committed_text
        == "Sentence one."
    )

    assert (
        update.unstable_text
        == "Sentence two"
    )


def test_live_controller_detects_partial_rewrite():

    controller = (
        LiveTranscriptController()
    )


    controller.handle_partial(
        partial_event(
            "Turn on my light"
        )
    )


    update = (
        controller.handle_partial(
            partial_event(
                "Turn on the light"
            )
        )
    )


    assert (
        update.rewritten
        is True
    )


def test_final_result_is_authoritative():

    controller = (
        LiveTranscriptController(
            required_stability=2
        )
    )


    controller.handle_partial(
        partial_event(
            "Turn on the light."
        )
    )

    controller.handle_partial(
        partial_event(
            "Turn on the light."
        )
    )


    final = (
        controller.finalize(
            TranscriptionResult(
                text=
                    "Turn on the lights.",

                language=
                    "en",

                language_probability=
                    0.99,
            )
        )
    )


    assert (
        final.final
        is True
    )

    assert (
        final.committed_text
        == "Turn on the lights."
    )

    assert (
        final.rewritten
        is True
    )


def test_language_metadata_remains_english_only():

    controller = (
        LiveTranscriptController()
    )


    controller.handle_partial(
        partial_event(
            "Hola.",
            language="es",
        )
    )


    assert (
        controller.language
        == "en"
    )


    controller.finalize(
        TranscriptionResult(
            text="Hola.",

            language="es",

            language_probability=0.98,
        )
    )


    assert (
        controller.language
        == "en"
    )