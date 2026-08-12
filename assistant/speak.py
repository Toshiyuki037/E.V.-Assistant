"""
E.V.I.E. - Voice Synthesis Module

Created: August 7, 2026
Last Edited: August 12, 2026
Author: Max Maehara

Purpose:
    Converts E.V.I.E.'s spoken-response text into local speech.

How It Works:
    Uses the local F5-TTS model with an authorized reference voice.

    The model remains loaded on the NVIDIA GPU.

    Generated speech is:
        - written temporarily
        - loaded into memory
        - played through the speaker
        - deleted afterward

Phase 14A:
    Added separate telemetry for:
        - TTS generation
        - WAV loading
        - audio playback

    This allows E.V.I.E. to distinguish model latency from actual
    speech duration before Phase 14 streaming TTS is implemented.
"""

from __future__ import annotations

import os
import tempfile

from pathlib import (
    Path,
)

import sounddevice as sd
import soundfile as sf

from f5_tts.api import (
    F5TTS,
)

from .telemetry import (
    mark,
    span,
)


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

ROOT = (
    Path(
        __file__
    )
    .resolve()
    .parent
    .parent
)


REF_AUDIO = (
    ROOT
    / "evie-voice"
    / "references"
    / "evie-neutral.wav"
)


REF_TEXT_FILE = (
    ROOT
    / "evie-voice"
    / "references"
    / "evie-neutral.txt"
)


REF_TEXT = (
    REF_TEXT_FILE
    .read_text(
        encoding="utf-8"
    )
    .strip()
)


# ---------------------------------------------------------------------------
# Model Initialization
# ---------------------------------------------------------------------------

print(
    "Loading E.V. voice model..."
)


tts = F5TTS(
    model=
        "F5TTS_v1_Base"
)


print(
    "E.V. voice ready."
)


# ---------------------------------------------------------------------------
# Speech
# ---------------------------------------------------------------------------

def speak(
    text: str,
):
    """
    Generates and plays one spoken E.V.I.E. response.
    """

    text = (
        str(
            text
            or ""
        )
        .strip()
    )


    if not text:

        return


    temp_path = None


    try:

        # -------------------------------------------------------------------
        # Temporary Output File
        # -------------------------------------------------------------------

        with tempfile.NamedTemporaryFile(
            suffix=
                ".wav",

            delete=
                False,
        ) as temp:

            temp_path = (
                temp.name
            )


        # -------------------------------------------------------------------
        # F5-TTS Generation
        # -------------------------------------------------------------------

        mark(
            "tts_generation_started"
        )


        with span(
            "tts_generation",
            characters=
                len(
                    text
                ),
        ):

            tts.infer(
                ref_file=
                    str(
                        REF_AUDIO
                    ),

                ref_text=
                    REF_TEXT,

                gen_text=
                    text,

                file_wave=
                    temp_path,
            )


        mark(
            "tts_generation_finished"
        )


        # -------------------------------------------------------------------
        # Read Generated Audio
        # -------------------------------------------------------------------

        with span(
            "tts_audio_load"
        ):

            audio, sample_rate = (
                sf.read(
                    temp_path
                )
            )


        # -------------------------------------------------------------------
        # Audio Duration
        # -------------------------------------------------------------------

        try:

            audio_duration = (
                len(
                    audio
                )
                / float(
                    sample_rate
                )
            )

        except Exception:

            audio_duration = (
                0.0
            )


        # -------------------------------------------------------------------
        # Playback
        # -------------------------------------------------------------------

        mark(
            "audio_playback_started"
        )


        with span(
            "tts_playback",
            audio_seconds=
                round(
                    audio_duration,
                    3,
                ),
        ):

            sd.play(
                audio,
                sample_rate,
            )

            sd.wait()


        mark(
            "audio_playback_finished"
        )


    finally:

        # -------------------------------------------------------------------
        # Temporary Audio Cleanup
        # -------------------------------------------------------------------

        if (
            temp_path
            and os.path.exists(
                temp_path
            )
        ):

            os.remove(
                temp_path
            )


# ---------------------------------------------------------------------------
# Standalone Test
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    speak(
        (
            "Good evening, Max. "
            "E.V. voice systems are "
            "operating normally."
        )
    )