"""
E.V.I.E. - Wake Voice Authentication

Phase 14

Authenticates the SAME utterance that triggered the wake word.

This module only produces a voice-identity signal and a short user-facing
wake response. It does NOT own authorization for sensitive actions.
"""

from __future__ import annotations

import random

from pathlib import (
    Path,
)

from .audio_state import (
    get_last_utterance_audio,
)

from .voiceprint import (
    VoiceIdentityResult,
    verify_voiceprint_audio,
)


DEFAULT_VOICEPRINT = (
    Path(
        "runtime"
    )
    / "voice_identity"
    / "max.npy"
)


AUTHENTICATED_LINES = (
    "Voice authenticated. Welcome home, Max.",
    "Identity confirmed. Welcome back, Max.",
    "Voice verified. Good to have you back, Max.",
    "Authenticated. Welcome back, Max.",
    "Voice confirmed. E.V.I.E. online.",
)


NOT_RECOGNIZED_LINE = (
    "Voice not recognized."
)


def authenticate_last_wake_utterance(
    *,
    enrolled_path: str
    | Path = DEFAULT_VOICEPRINT,
    threshold: float = 0.85,
) -> VoiceIdentityResult:

    audio, sample_rate = (
        get_last_utterance_audio()
    )


    if audio is None:

        return (
            VoiceIdentityResult(
                matched=False,
                similarity=0.0,
                threshold=float(
                    threshold
                ),
            )
        )


    enrolled_path = (
        Path(
            enrolled_path
        )
    )


    if not enrolled_path.exists():

        return (
            VoiceIdentityResult(
                matched=False,
                similarity=0.0,
                threshold=float(
                    threshold
                ),
            )
        )


    return (
        verify_voiceprint_audio(
            audio,
            sample_rate,
            enrolled_path,
            threshold=
                threshold,
        )
    )


def authenticated_wake_line() -> str:

    return (
        random.choice(
            AUTHENTICATED_LINES
        )
    )
