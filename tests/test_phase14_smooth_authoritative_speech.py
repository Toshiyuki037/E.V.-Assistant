"""
Phase 14 smooth authoritative speech tests.
"""

from __future__ import annotations

import threading

from assistant.voice.authoritative_speech import (
    AuthoritativeSpeechPipeline,
)


def test_two_sentences_are_combined_into_one_tts_call():

    synthesized = []

    played = []

    done = (
        threading.Event()
    )


    def synthesize(
        text,
    ):

        synthesized.append(
            text
        )

        return (
            text,
            24000,
        )


    def play(
        audio,
        sample_rate,
    ):

        played.append(
            audio
        )

        done.set()


    pipeline = (
        AuthoritativeSpeechPipeline(
            synthesize_fn=
                synthesize,

            play_fn=
                play,

            max_sentences=
                2,

            max_characters=
                260,
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


    assert done.wait(
        1.0
    )


    pipeline.finish_input()


    assert pipeline.wait(
        1.0
    )


    assert synthesized == [
        "Sentence one. Sentence two."
    ]


    assert played == [
        "Sentence one. Sentence two."
    ]


def test_single_sentence_flushes_when_response_finishes():

    synthesized = []


    pipeline = (
        AuthoritativeSpeechPipeline(
            synthesize_fn=
                lambda text:
                    (
                        synthesized.append(
                            text
                        )
                        or (
                            text,
                            24000,
                        )
                    ),

            play_fn=
                lambda audio, sample_rate:
                    None,
        )
    )


    pipeline.start()


    pipeline.submit_sentence(
        "Only sentence."
    )


    pipeline.finish_input()


    assert pipeline.wait(
        1.0
    )


    assert synthesized == [
        "Only sentence."
    ]


def test_formatter_runs_before_combining():

    synthesized = []


    pipeline = (
        AuthoritativeSpeechPipeline(
            synthesize_fn=
                lambda text:
                    (
                        synthesized.append(
                            text
                        )
                        or (
                            text,
                            24000,
                        )
                    ),

            play_fn=
                lambda audio, sample_rate:
                    None,

            prepare_fn=
                lambda text:
                    text.replace(
                        "**",
                        "",
                    ),
        )
    )


    pipeline.start()


    pipeline.submit_sentence(
        "A **transistor** is a switch."
    )


    pipeline.submit_sentence(
        "It controls current."
    )


    pipeline.finish_input()


    assert pipeline.wait(
        1.0
    )


    assert synthesized == [
        (
            "A transistor is a switch. "
            "It controls current."
        )
    ]
