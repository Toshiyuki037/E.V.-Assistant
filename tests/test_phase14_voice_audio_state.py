import numpy as np

from assistant.voice.audio_state import (
    get_last_utterance_audio,
    set_last_utterance_audio,
)


def test_last_utterance_audio_is_copied():

    original = np.array(
        [
            1,
            2,
            3,
        ],
        dtype=np.int16,
    )

    set_last_utterance_audio(
        original,
        sample_rate=16000,
    )

    stored, rate = (
        get_last_utterance_audio()
    )

    assert rate == 16000
    assert stored.tolist() == [
        1,
        2,
        3,
    ]

    stored[0] = 999

    stored_again, _ = (
        get_last_utterance_audio()
    )

    assert stored_again[0] == 1
