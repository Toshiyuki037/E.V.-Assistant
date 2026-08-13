import threading
import time

from assistant.speech_formatter import (
    prepare_spoken_chunks,
    prepare_spoken_text,
)

from assistant.voice.authoritative_speech import (
    AuthoritativeSpeechPipeline,
)


def test_old_formatter_compatibility_is_preserved():
    response = (
        "One. Two. Three. Four."
    )

    concise = (
        prepare_spoken_text(
            response
        )
    )

    assert concise == "One. Two."


def test_full_response_chunks_preserve_all_sentences():
    response = (
        "One. Two. Three. Four. Five."
    )

    chunks = (
        prepare_spoken_chunks(
            response,
            sentences_per_chunk=
                2,
        )
    )

    assert chunks == [
        "One. Two.",
        "Three. Four.",
        "Five.",
    ]


def test_authoritative_pipeline_speaks_all_chunks():
    synthesized = []

    played = []

    def synthesize(
        text,
    ):
        synthesized.append(
            text
        )

        return (
            [1, 2, 3],
            24000,
        )

    def play(
        audio,
        sample_rate,
    ):
        played.append(
            (
                audio,
                sample_rate,
            )
        )

    pipeline = (
        AuthoritativeSpeechPipeline(
            synthesize_fn=
                synthesize,
            play_fn=
                play,
            max_sentences=
                2,
            max_characters=
                340,
            rolling=
                True,
        )
    )

    pipeline.start()

    for sentence in [
        "One.",
        "Two.",
        "Three.",
        "Four.",
        "Five.",
    ]:
        assert (
            pipeline.submit_sentence(
                sentence
            )
            is True
        )

    pipeline.finish_input()

    assert pipeline.wait(
        timeout=
            2.0
    )

    assert synthesized == [
        "One. Two.",
        "Three. Four.",
        "Five.",
    ]

    assert len(
        played
    ) == 3


def test_pipeline_overlaps_synthesis_with_playback():
    events = []

    first_play_started = (
        threading.Event()
    )

    second_synthesis_started = (
        threading.Event()
    )

    def synthesize(
        text,
    ):
        events.append(
            (
                "synth",
                text,
            )
        )

        if text == "Three. Four.":
            second_synthesis_started.set()

        time.sleep(
            0.03
        )

        return (
            [1, 2, 3],
            24000,
        )

    def play(
        audio,
        sample_rate,
    ):
        first_play_started.set()

        # Give synthesis worker enough time to begin next chunk while
        # playback is still active.
        time.sleep(
            0.12
        )

    pipeline = (
        AuthoritativeSpeechPipeline(
            synthesize_fn=
                synthesize,
            play_fn=
                play,
            max_sentences=
                2,
            rolling=
                True,
        )
    )

    pipeline.start()

    for sentence in [
        "One.",
        "Two.",
        "Three.",
        "Four.",
    ]:
        pipeline.submit_sentence(
            sentence
        )

    pipeline.finish_input()

    assert first_play_started.wait(
        1.0
    )

    assert second_synthesis_started.wait(
        1.0
    )

    assert pipeline.wait(
        2.0
    )
