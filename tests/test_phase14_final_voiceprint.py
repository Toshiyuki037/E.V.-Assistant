
import numpy as np
import soundfile as sf

from assistant.voice.voiceprint import (
    save_voiceprint,
    verify_voiceprint,
)


def test_voiceprint_is_only_a_signal(tmp_path):
    sample_rate = 16000
    t = np.arange(sample_rate, dtype=np.float32) / sample_rate
    audio = 0.4 * np.sin(2.0 * np.pi * 180.0 * t)

    wav = tmp_path / "voice.wav"
    enrolled = tmp_path / "voice.npy"

    sf.write(wav, audio, sample_rate)

    save_voiceprint(
        wav,
        enrolled,
    )

    result = verify_voiceprint(
        wav,
        enrolled,
    )

    assert result.matched
    assert result.similarity > 0.99
