from __future__ import annotations

import threading

from assistant.voice.authoritative_speech import (
    AuthoritativeSpeechPipeline,
)


def test_authoritative_sentences_combine_in_order():

    synthesized = []

    played = []

    finished = (
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

        finished.set()


    pipeline = (
        AuthoritativeSpeechPipeline(
            synthesize_fn=
                synthesize,

            play_fn=
                play,

            prepare_fn=
                lambda text:
                    text.replace(
                        "**",
                        "",
                    ),

            max_sentences=
                3,

            max_characters=
                500,
        )
    )


    pipeline.start()


    assert pipeline.submit_sentence(
        "Sentence **one**."
    )


    assert pipeline.submit_sentence(
        "Sentence two."
    )


    assert pipeline.submit_sentence(
        "Sentence three."
    )


    assert finished.wait(
        1.0
    )


    pipeline.finish_input()


    assert pipeline.wait(
        1.0
    )


    assert synthesized == [
        (
            "Sentence one. "
            "Sentence two. "
            "Sentence three."
        )
    ]


    assert played == [
        (
            "Sentence one. "
            "Sentence two. "
            "Sentence three."
        )
    ]


def test_generation_starts_when_voice_budget_fills():

    generation_started = (
        threading.Event()
    )


    generated = []


    def synthesize(
        text,
    ):

        generated.append(
            text
        )

        generation_started.set()

        return (
            text,
            24000,
        )


    pipeline = (
        AuthoritativeSpeechPipeline(
            synthesize_fn=
                synthesize,

            play_fn=
                lambda audio, sample_rate:
                    None,

            max_sentences=
                2,

            max_characters=
                260,
        )
    )


    pipeline.start()


    assert pipeline.submit_sentence(
        "First."
    )


    assert not generation_started.is_set()


    assert pipeline.submit_sentence(
        "Second."
    )


    assert generation_started.wait(
        1.0
    )


    pipeline.finish_input()


    assert pipeline.wait(
        1.0
    )


    assert generated == [
        "First. Second."
    ]