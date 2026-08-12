"""
E.V.I.E. - Speech Recognition Module

Phase 14B - Voice Input 2.0

Purpose:
Provides natural-length microphone listening for E.V.I.E.

Features:
- GPU Faster-Whisper transcription
- voice activity detection
- automatic speech start detection
- automatic end-of-speech detection
- no fixed six-second recording window
- maximum recording safety timeout
- local microphone processing
- temporary audio cleanup

This is the foundation for:
- partial transcription
- streaming transcription
- interruption
- barge-in
- wake-word operation
"""

from __future__ import annotations

import os
import tempfile
import time
import wave
from collections import deque

import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel


# ---------------------------------------------------------------------------
# Audio Configuration
# ---------------------------------------------------------------------------

SAMPLE_RATE = 16000
CHANNELS = 1

BLOCK_DURATION = 0.10

BLOCK_SIZE = int(
    SAMPLE_RATE
    * BLOCK_DURATION
)


# ---------------------------------------------------------------------------
# Voice Activity Detection
# ---------------------------------------------------------------------------

# RMS threshold for considering a block speech.
#
# This intentionally starts conservative. It can later be calibrated
# automatically for the user's microphone/environment.

VOICE_THRESHOLD = 350.0


# Amount of speech required before recording officially begins.

SPEECH_START_SECONDS = 0.20


# Silence required after speech before the utterance is considered finished.

SILENCE_END_SECONDS = 0.85


# Keep a small amount of audio before speech detection so the beginning
# of the first word is not clipped.

PRE_ROLL_SECONDS = 0.40


# Stop waiting if nobody speaks.

LISTEN_TIMEOUT_SECONDS = 12.0


# Safety limit for one utterance.

MAX_UTTERANCE_SECONDS = 45.0


# ---------------------------------------------------------------------------
# Derived Block Counts
# ---------------------------------------------------------------------------

SPEECH_START_BLOCKS = max(
    1,
    int(
        SPEECH_START_SECONDS
        / BLOCK_DURATION
    ),
)

SILENCE_END_BLOCKS = max(
    1,
    int(
        SILENCE_END_SECONDS
        / BLOCK_DURATION
    ),
)

PRE_ROLL_BLOCKS = max(
    1,
    int(
        PRE_ROLL_SECONDS
        / BLOCK_DURATION
    ),
)


# ---------------------------------------------------------------------------
# Whisper
# ---------------------------------------------------------------------------

print(
    "Loading speech recognition..."
)

whisper = WhisperModel(
    "small.en",
    device="cuda",
    compute_type="float16",
)

print(
    "Speech recognition ready."
)


# ---------------------------------------------------------------------------
# Audio Helpers
# ---------------------------------------------------------------------------

def audio_level(
    audio: np.ndarray,
) -> float:
    """
    Returns the RMS amplitude of an int16 audio block.
    """

    if audio.size == 0:
        return 0.0

    samples = (
        audio
        .astype(
            np.float32
        )
    )

    rms = np.sqrt(
        np.mean(
            samples * samples
        )
    )

    return float(
        rms
    )


def contains_voice(
    audio: np.ndarray,
) -> bool:
    """
    Lightweight local voice activity detector.

    Phase 14B intentionally uses amplitude-based VAD so no additional
    model dependency is required.

    A neural VAD can replace this later without changing listen().
    """

    return (
        audio_level(
            audio
        )
        >= VOICE_THRESHOLD
    )


# ---------------------------------------------------------------------------
# Recording
# ---------------------------------------------------------------------------

def record_utterance():
    """
    Record one natural-length spoken utterance.

    Recording begins only after speech is detected and ends after
    sustained silence.

    Returns:
        numpy.ndarray | None
    """

    print(
        "\nListening..."
    )

    pre_roll = deque(
        maxlen=PRE_ROLL_BLOCKS
    )

    recorded_blocks = []

    speech_started = False

    consecutive_voice = 0
    consecutive_silence = 0

    listen_started = (
        time.monotonic()
    )

    speech_started_at = None


    # -----------------------------------------------------------------------
    # Audio Callback
    # -----------------------------------------------------------------------

    with sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype="int16",
        blocksize=BLOCK_SIZE,
    ) as stream:

        while True:

            block, overflowed = (
                stream.read(
                    BLOCK_SIZE
                )
            )


            if overflowed:

                # Overflow should not terminate the session.
                # The following blocks are still usable.

                pass


            block = (
                np.asarray(
                    block,
                    dtype=np.int16,
                )
                .copy()
            )


            voice = (
                contains_voice(
                    block
                )
            )


            # ---------------------------------------------------------------
            # Waiting for Speech
            # ---------------------------------------------------------------

            if not speech_started:

                pre_roll.append(
                    block
                )


                if voice:

                    consecutive_voice += 1

                else:

                    consecutive_voice = 0


                if (
                    consecutive_voice
                    >= SPEECH_START_BLOCKS
                ):

                    speech_started = True

                    speech_started_at = (
                        time.monotonic()
                    )

                    recorded_blocks.extend(
                        list(
                            pre_roll
                        )
                    )

                    pre_roll.clear()

                    consecutive_silence = 0

                    print(
                        "Speech detected."
                    )

                    continue


                # No speech within timeout.

                if (
                    time.monotonic()
                    - listen_started
                    >= LISTEN_TIMEOUT_SECONDS
                ):

                    print(
                        "Listening timed out."
                    )

                    return None


                continue


            # ---------------------------------------------------------------
            # Speech Active
            # ---------------------------------------------------------------

            recorded_blocks.append(
                block
            )


            if voice:

                consecutive_silence = 0

            else:

                consecutive_silence += 1


            # ---------------------------------------------------------------
            # End-of-Speech Detection
            # ---------------------------------------------------------------

            if (
                consecutive_silence
                >= SILENCE_END_BLOCKS
            ):

                print(
                    "Speech complete."
                )

                break


            # ---------------------------------------------------------------
            # Maximum Utterance Safety Limit
            # ---------------------------------------------------------------

            if (
                speech_started_at
                is not None
                and (
                    time.monotonic()
                    - speech_started_at
                )
                >= MAX_UTTERANCE_SECONDS
            ):

                print(
                    "Maximum utterance length reached."
                )

                break


    if not recorded_blocks:

        return None


    return np.concatenate(
        recorded_blocks,
        axis=0,
    )


# ---------------------------------------------------------------------------
# Temporary WAV
# ---------------------------------------------------------------------------

def write_temporary_wav(
    audio: np.ndarray,
) -> str:
    """
    Writes microphone audio to a temporary WAV for Faster-Whisper.
    """

    with tempfile.NamedTemporaryFile(
        suffix=".wav",
        delete=False,
    ) as temp:

        filename = (
            temp.name
        )


    with wave.open(
        filename,
        "wb",
    ) as wav:

        wav.setnchannels(
            CHANNELS
        )

        wav.setsampwidth(
            2
        )

        wav.setframerate(
            SAMPLE_RATE
        )

        wav.writeframes(
            audio.tobytes()
        )


    return filename


# ---------------------------------------------------------------------------
# Transcription
# ---------------------------------------------------------------------------

def transcribe_audio(
    audio: np.ndarray,
) -> str:
    """
    Transcribe captured speech with the resident Faster-Whisper model.
    """

    filename = None


    try:

        filename = (
            write_temporary_wav(
                audio
            )
        )


        print(
            "Transcribing..."
        )


        segments, _ = (
            whisper.transcribe(
                filename,
                language="en",

                # Faster than the old beam_size=5 while still giving
                # strong command transcription quality.
                beam_size=1,

                vad_filter=False,

                condition_on_previous_text=False,
            )
        )


        text = " ".join(
            segment.text.strip()

            for segment
            in segments

            if segment.text.strip()
        ).strip()


        return text


    finally:

        if (
            filename
            and os.path.exists(
                filename
            )
        ):

            try:

                os.remove(
                    filename
                )

            except OSError:

                pass


# ---------------------------------------------------------------------------
# Public Listening API
# ---------------------------------------------------------------------------

def listen():
    """
    Listen for one natural spoken utterance and return its transcription.

    Maintains compatibility with main.py's existing:

        user_text = listen()

    interface.
    """

    audio = (
        record_utterance()
    )


    if audio is None:

        return ""


    text = (
        transcribe_audio(
            audio
        )
    )


    if text:

        print(
            f"You: {text}"
        )


    return text


# ---------------------------------------------------------------------------
# Standalone Test
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    result = listen()

    print(
        "\nTranscription:"
    )

    print(
        result
        or "<nothing>"
    )