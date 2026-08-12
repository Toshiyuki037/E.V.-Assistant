"""
E.V.I.E. - Last Utterance Audio State

Phase 14 Voice Authentication

Purpose:
    Stores a thread-safe copy of the most recently finalized microphone
    utterance so wake-word authentication can verify the SAME audio that
    produced the transcript.

This module is intentionally Phase-14-only and does not alter frozen
Phase 1-13 request routing.
"""

from __future__ import annotations

import threading

import numpy as np


_LOCK = threading.Lock()

_LAST_AUDIO = None

_LAST_SAMPLE_RATE = 16000


def set_last_utterance_audio(
    audio,
    *,
    sample_rate: int = 16000,
):
    global _LAST_AUDIO
    global _LAST_SAMPLE_RATE

    if audio is None:

        with _LOCK:

            _LAST_AUDIO = None

            _LAST_SAMPLE_RATE = int(
                sample_rate
            )

        return


    snapshot = (
        np.asarray(
            audio,
            dtype=np.int16,
        )
        .copy()
    )


    with _LOCK:

        _LAST_AUDIO = snapshot

        _LAST_SAMPLE_RATE = int(
            sample_rate
        )


def get_last_utterance_audio():
    """
    Returns:
        (audio_copy, sample_rate)

    The returned audio is always a copy so authentication code cannot mutate
    microphone state.
    """

    with _LOCK:

        if _LAST_AUDIO is None:

            return (
                None,
                int(
                    _LAST_SAMPLE_RATE
                ),
            )


        return (
            _LAST_AUDIO.copy(),
            int(
                _LAST_SAMPLE_RATE
            ),
        )
