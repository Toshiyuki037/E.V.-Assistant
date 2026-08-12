import numpy as np

from assistant.voice.voiceprint import (
    _feature_vector,
    verify_voiceprint_audio,
)


def test_verify_voiceprint_audio_matches_saved_vector(
    tmp_path,
):

    sample_rate = 16000

    t = (
        np.arange(
            sample_rate,
            dtype=np.float32,
        )
        / sample_rate
    )

    audio = (
        0.4
        * np.sin(
            2.0
            * np.pi
            * 180.0
            * t
        )
    )

    enrolled = (
        _feature_vector(
            audio,
            sample_rate,
        )
    )

    enrolled_path = (
        tmp_path
        / "voice.npy"
    )

    np.save(
        enrolled_path,
        enrolled,
    )

    result = (
        verify_voiceprint_audio(
            audio,
            sample_rate,
            enrolled_path,
        )
    )

    assert result.matched
    assert result.similarity > 0.99
