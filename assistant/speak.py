"""
E.V.I.E. - Voice Synthesis Module

Phase 14I

Exposes the resident F5 model and the process-wide controllable playback
controller.
"""

from __future__ import annotations

import os
import tempfile
import threading

from pathlib import (
    Path,
)

import soundfile as sf

from f5_tts.api import (
    F5TTS,
)

from .telemetry import (
    mark,
    span,
)

from .voice.playback import (
    PLAYER,
)


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


print(
    "Loading E.V. voice model..."
)

tts = (
    F5TTS(
        model=
            "F5TTS_v1_Base"
    )
)

_TTS_LOCK = (
    threading.Lock()
)

print(
    "E.V. voice ready."
)


def synthesize_audio(
    text: str,
):

    text = (
        str(
            text
            or ""
        )
        .strip()
    )


    if not text:

        return (
            None,
            0,
        )


    temp_path = None


    try:

        with tempfile.NamedTemporaryFile(
            suffix=".wav",
            delete=False,
        ) as temp:

            temp_path = (
                temp.name
            )


        with _TTS_LOCK:

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


        audio, sample_rate = (
            sf.read(
                temp_path
            )
        )


        return (
            audio,
            int(
                sample_rate
            ),
        )


    finally:

        if (
            temp_path
            and os.path.exists(
                temp_path
            )
        ):

            try:

                os.remove(
                    temp_path
                )

            except OSError:

                pass


def play_audio(
    audio,
    sample_rate: int,
):

    return (
        PLAYER.play(
            audio,
            int(
                sample_rate
            ),
        )
    )


def stop_audio():

    PLAYER.stop_current()


def pause_audio():

    PLAYER.pause_current()


def resume_audio():

    PLAYER.resume_current()


def audio_is_speaking() -> bool:

    return (
        PLAYER.is_speaking
    )


def audio_is_paused() -> bool:

    return (
        PLAYER.is_paused
    )


def close_audio():

    PLAYER.close()


def speak(
    text: str,
):

    text = (
        str(
            text
            or ""
        )
        .strip()
    )


    if not text:

        return


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

        audio, sample_rate = (
            synthesize_audio(
                text
            )
        )


    mark(
        "tts_generation_finished"
    )


    if (
        audio is None
        or sample_rate <= 0
    ):

        return


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

        play_audio(
            audio,
            sample_rate,
        )


    mark(
        "audio_playback_finished"
    )
