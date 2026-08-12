"""
Phase 14 authoritative voice-budget tests.
"""

from __future__ import annotations

import threading

from assistant.voice.authoritative_speech import (
    AuthoritativeSpeechPipeline,
)


def test_voice_budget_limits_sentence_count():

    played = []


    pipeline = (
        AuthoritativeSpeechPipeline(
            synthesize_fn=
                lambda text:
                    (
                        text,
                        24000,
                    ),

            play_fn=
                lambda audio, sample_rate:
                    played.append(
                        audio
                    ),

            max_sentences=
                2,

            max_characters=
                500,
        )
    )


    pipeline.start()


    assert pipeline.submit_sentence(
        "Sentence one."
    )


    assert pipeline.submit_sentence(
        "Sentence two."
    )


    assert (
        pipeline.submit_sentence(
            "Sentence three."
        )
        is False
    )


    pipeline.finish_input()


    assert pipeline.wait(
        1.0
    )


    assert played == [
        "Sentence one. Sentence two."
    ]


def test_voice_budget_limits_total_characters():

    played = []


    pipeline = (
        AuthoritativeSpeechPipeline(
            synthesize_fn=
                lambda text:
                    (
                        text,
                        24000,
                    ),

            play_fn=
                lambda audio, sample_rate:
                    played.append(
                        audio
                    ),

            max_sentences=
                4,

            max_characters=
                50,
        )
    )


    pipeline.start()


    assert pipeline.submit_sentence(
        "This is the first short sentence."
    )


    assert pipeline.submit_sentence(
        (
            "This second sentence is much "
            "longer than the remaining budget."
        )
    )


    assert (
        pipeline.submit_sentence(
            "This should not be spoken."
        )
        is False
    )


    pipeline.finish_input()


    assert pipeline.wait(
        1.0
    )


    assert len(
        " ".join(
            played
        )
    ) <= 55


def test_formatter_applies_before_budget():

    played = []


    pipeline = (
        AuthoritativeSpeechPipeline(
            synthesize_fn=
                lambda text:
                    (
                        text,
                        24000,
                    ),

            play_fn=
                lambda audio, sample_rate:
                    played.append(
                        audio
                    ),

            prepare_fn=
                lambda text:
                    text.replace(
                        "**",
                        "",
                    ),

            max_sentences=
                2,

            max_characters=
                260,
        )
    )


    pipeline.start()


    pipeline.submit_sentence(
        "A **transistor** is a switch."
    )


    pipeline.finish_input()


    assert pipeline.wait(
        1.0
    )


    assert played == [
        "A transistor is a switch."
    ]


def test_first_audio_event_is_emitted():

    events = []

    finished = (
        threading.Event()
    )


    def play(
        audio,
        sample_rate,
    ):

        finished.set()


    pipeline = (
        AuthoritativeSpeechPipeline(
            synthesize_fn=
                lambda text:
                    (
                        text,
                        24000,
                    ),

            play_fn=
                play,

            emit_fn=
                events.append,
        )
    )


    pipeline.start()


    pipeline.submit_sentence(
        "First sentence."
    )


    pipeline.finish_input()


    assert finished.wait(
        1.0
    )


    assert pipeline.wait(
        1.0
    )


    assert any(
        event.kind
        == "playback_started"

        for event in events
    )
