"""
Phase 14B VAD regression tests.
"""

import numpy as np

from assistant.voice.vad import (
    VoiceActivityDetector,
    frame_samples,
)


def _silence(
    samples=480,
):
    return np.zeros(
        samples,
        dtype=np.float32,
    )


def _speech(
    samples=480,
    amplitude=0.1,
):
    return np.full(
        samples,
        amplitude,
        dtype=np.float32,
    )


def test_frame_samples():

    assert (
        frame_samples(
            sample_rate=16000,
            frame_duration_ms=30,
        )
        == 480
    )


def test_silence_does_not_start_speech():

    detector = (
        VoiceActivityDetector(
            speech_threshold=0.02,
            start_frames=2,
        )
    )


    first = detector.process_frame(
        _silence()
    )


    second = detector.process_frame(
        _silence()
    )


    assert first.is_speech is False

    assert second.is_speech is False

    assert detector.in_speech is False


def test_consecutive_voice_frames_start_utterance():

    detector = (
        VoiceActivityDetector(
            speech_threshold=0.02,
            start_frames=2,
        )
    )


    first = detector.process_frame(
        _speech()
    )


    second = detector.process_frame(
        _speech()
    )


    assert first.speech_started is False

    assert second.speech_started is True

    assert second.in_speech is True


def test_single_noise_frame_does_not_start_utterance():

    detector = (
        VoiceActivityDetector(
            speech_threshold=0.02,
            start_frames=2,
        )
    )


    detector.process_frame(
        _speech()
    )


    result = detector.process_frame(
        _silence()
    )


    assert result.speech_started is False

    assert detector.in_speech is False


def test_short_pause_does_not_end_utterance():

    detector = (
        VoiceActivityDetector(
            speech_threshold=0.02,
            start_frames=2,
            end_silence_ms=120,
            frame_duration_ms=30,
        )
    )


    detector.process_frame(
        _speech()
    )


    detector.process_frame(
        _speech()
    )


    result = detector.process_frame(
        _silence()
    )


    assert result.speech_ended is False

    assert detector.in_speech is True


def test_sustained_silence_ends_utterance():

    detector = (
        VoiceActivityDetector(
            speech_threshold=0.02,
            start_frames=2,
            end_silence_ms=90,
            frame_duration_ms=30,
            minimum_utterance_ms=30,
        )
    )


    detector.process_frame(
        _speech()
    )


    detector.process_frame(
        _speech()
    )


    detector.process_frame(
        _silence()
    )


    detector.process_frame(
        _silence()
    )


    result = detector.process_frame(
        _silence()
    )


    assert result.speech_ended is True

    assert result.in_speech is False


def test_reset_returns_detector_to_idle():

    detector = (
        VoiceActivityDetector(
            speech_threshold=0.02,
            start_frames=1,
        )
    )


    detector.process_frame(
        _speech()
    )


    assert detector.in_speech is True


    detector.reset()


    assert detector.in_speech is False


def test_int16_pcm_is_normalized():

    detector = (
        VoiceActivityDetector(
            speech_threshold=0.02,
            start_frames=1,
        )
    )


    audio = np.full(
        480,
        5000,
        dtype=np.int16,
    )


    result = detector.process_frame(
        audio
    )


    assert result.is_speech is True

    assert result.level > 0.02