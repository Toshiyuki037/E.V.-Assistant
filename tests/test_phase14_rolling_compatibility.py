from assistant.voice.authoritative_speech import (
    AuthoritativeSpeechPipeline,
)


def test_default_mode_preserves_legacy_total_budget():
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
                    None,

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


def test_rolling_mode_accepts_later_sentences():
    synthesized = []

    pipeline = (
        AuthoritativeSpeechPipeline(
            synthesize_fn=
                lambda text:
                    (
                        synthesized.append(
                            text
                        )
                        or text,
                        24000,
                    ),

            play_fn=
                lambda audio, sample_rate:
                    None,

            max_sentences=
                2,

            max_characters=
                500,

            rolling=
                True,
        )
    )

    pipeline.start()

    assert pipeline.submit_sentence(
        "Sentence one."
    )

    assert pipeline.submit_sentence(
        "Sentence two."
    )

    assert pipeline.submit_sentence(
        "Sentence three."
    )

    assert pipeline.submit_sentence(
        "Sentence four."
    )

    pipeline.finish_input()

    assert pipeline.wait(
        timeout=
            2.0
    )

    assert synthesized == [
        "Sentence one. Sentence two.",
        "Sentence three. Sentence four.",
    ]
