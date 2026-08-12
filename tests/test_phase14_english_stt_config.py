"""
Phase 14 English-only STT configuration tests.

No model is loaded.
"""

from assistant.voice.stt_config import (
    FINAL_BEAM_SIZE,
    PARTIAL_BEAM_SIZE,
    WHISPER_HOTWORDS,
    WHISPER_LANGUAGE,
    WHISPER_MODEL_NAME,
)


def test_stt_is_english_only():

    assert (
        WHISPER_LANGUAGE
        == "en"
    )


def test_final_decode_is_stronger_than_partial():

    assert (
        FINAL_BEAM_SIZE
        > PARTIAL_BEAM_SIZE
    )


def test_large_distilled_english_model_is_configured():

    assert (
        "distil-large-v3.5"
        in WHISPER_MODEL_NAME
    )


def test_project_vocabulary_is_present():

    lowered = (
        WHISPER_HOTWORDS.lower()
    )

    for phrase in (
        "e.v.i.e.",
        "transistor",
        "logic gates",
        "fpga",
        "embedded systems",
    ):

        assert (
            phrase
            in lowered
        )
