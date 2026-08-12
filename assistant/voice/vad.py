"""
E.V.I.E. - Voice Activity Detection

Created: August 12, 2026
Author: Max Maehara

Phase 14B

Purpose:
    Detects speech activity and utterance boundaries from microphone
    audio frames.

Architecture:
    This module does NOT:
        - access the microphone
        - run Whisper
        - control the voice session
        - perform reasoning

    It only classifies audio frames and tracks deterministic
    speech/silence state.

This separation keeps the VAD logic testable without requiring
live microphone hardware.
"""

from __future__ import annotations

from dataclasses import (
    dataclass,
)

import numpy as np


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DEFAULT_SAMPLE_RATE = 16000

DEFAULT_FRAME_DURATION_MS = 30

DEFAULT_START_FRAMES = 2

DEFAULT_END_SILENCE_MS = 650

DEFAULT_MINIMUM_UTTERANCE_MS = 180


# ---------------------------------------------------------------------------
# VAD State
# ---------------------------------------------------------------------------

@dataclass(
    frozen=True
)
class VADResult:
    """
    Result produced after processing one audio frame.
    """

    is_speech: bool

    speech_started: bool

    speech_ended: bool

    in_speech: bool

    level: float

    threshold: float


# ---------------------------------------------------------------------------
# Voice Activity Detector
# ---------------------------------------------------------------------------

class VoiceActivityDetector:
    """
    Lightweight deterministic voice-activity detector.

    Speech detection uses frame RMS energy.

    The detector intentionally separates:

        raw frame classification

    from:

        utterance state

    so isolated noise does not immediately begin an utterance and
    short pauses do not immediately end one.
    """

    def __init__(
        self,
        *,
        sample_rate: int = DEFAULT_SAMPLE_RATE,
        frame_duration_ms: int = DEFAULT_FRAME_DURATION_MS,
        speech_threshold: float = 0.015,
        start_frames: int = DEFAULT_START_FRAMES,
        end_silence_ms: int = DEFAULT_END_SILENCE_MS,
        minimum_utterance_ms: int = DEFAULT_MINIMUM_UTTERANCE_MS,
    ):

        self.sample_rate = int(
            sample_rate
        )

        self.frame_duration_ms = int(
            frame_duration_ms
        )

        self.speech_threshold = float(
            speech_threshold
        )

        self.start_frames = max(
            1,
            int(
                start_frames
            ),
        )

        self.end_silence_ms = max(
            0,
            int(
                end_silence_ms
            ),
        )

        self.minimum_utterance_ms = max(
            0,
            int(
                minimum_utterance_ms
            ),
        )


        if self.sample_rate <= 0:

            raise ValueError(
                "sample_rate must be positive."
            )


        if self.frame_duration_ms <= 0:

            raise ValueError(
                "frame_duration_ms must be positive."
            )


        if self.speech_threshold < 0:

            raise ValueError(
                "speech_threshold cannot be negative."
            )


        self.end_silence_frames = max(
            1,
            int(
                round(
                    self.end_silence_ms
                    / self.frame_duration_ms
                )
            ),
        )


        self.minimum_utterance_frames = max(
            1,
            int(
                round(
                    self.minimum_utterance_ms
                    / self.frame_duration_ms
                )
            ),
        )


        self.reset()


    # -----------------------------------------------------------------------
    # Reset
    # -----------------------------------------------------------------------

    def reset(
        self,
    ):
        """
        Returns the detector to its idle state.
        """

        self.in_speech = False

        self._speech_run = 0

        self._silence_run = 0

        self._utterance_frames = 0


    # -----------------------------------------------------------------------
    # Frame Level
    # -----------------------------------------------------------------------

    @staticmethod
    def frame_level(
        audio,
    ) -> float:
        """
        Calculates normalized RMS energy for one audio frame.

        Supports common microphone representations:
            - int16 PCM
            - float32 / float64 normalized audio
        """

        frame = np.asarray(
            audio
        )


        if frame.size == 0:

            return 0.0


        # ---------------------------------------------------------------
        # Convert integer PCM into normalized floating point.
        # ---------------------------------------------------------------

        if np.issubdtype(
            frame.dtype,
            np.integer,
        ):

            info = np.iinfo(
                frame.dtype
            )


            scale = float(
                max(
                    abs(
                        info.min
                    ),
                    abs(
                        info.max
                    ),
                )
            )


            if scale <= 0:

                return 0.0


            values = (
                frame.astype(
                    np.float32
                )
                / scale
            )


        else:

            values = frame.astype(
                np.float32,
                copy=False,
            )


        # ---------------------------------------------------------------
        # Flatten channels/samples.
        # ---------------------------------------------------------------

        values = values.reshape(
            -1
        )


        if values.size == 0:

            return 0.0


        # ---------------------------------------------------------------
        # RMS
        # ---------------------------------------------------------------

        level = float(
            np.sqrt(
                np.mean(
                    np.square(
                        values,
                        dtype=np.float32,
                    )
                )
            )
        )


        if not np.isfinite(
            level
        ):

            return 0.0


        return level


    # -----------------------------------------------------------------------
    # Classification
    # -----------------------------------------------------------------------

    def classify_frame(
        self,
        audio,
    ):
        """
        Returns:

            is_speech
            level
        """

        level = (
            self.frame_level(
                audio
            )
        )


        is_speech = (
            level
            >= self.speech_threshold
        )


        return (
            is_speech,
            level,
        )


    # -----------------------------------------------------------------------
    # Process Frame
    # -----------------------------------------------------------------------

    def process_frame(
        self,
        audio,
    ) -> VADResult:
        """
        Processes one audio frame and updates utterance state.

        Speech begins only after several consecutive speech frames.

        Speech ends only after:
            - minimum utterance duration has been reached
            - enough consecutive silence has occurred
        """

        is_speech, level = (
            self.classify_frame(
                audio
            )
        )


        speech_started = False

        speech_ended = False


        # -------------------------------------------------------------------
        # Idle
        # -------------------------------------------------------------------

        if not self.in_speech:

            if is_speech:

                self._speech_run += 1


                if (
                    self._speech_run
                    >= self.start_frames
                ):

                    self.in_speech = True

                    speech_started = True

                    self._utterance_frames = (
                        self._speech_run
                    )

                    self._silence_run = 0


            else:

                self._speech_run = 0


        # -------------------------------------------------------------------
        # Active Utterance
        # -------------------------------------------------------------------

        else:

            self._utterance_frames += 1


            if is_speech:

                self._silence_run = 0


            else:

                self._silence_run += 1


                long_enough = (
                    self._utterance_frames
                    >= self.minimum_utterance_frames
                )


                silence_complete = (
                    self._silence_run
                    >= self.end_silence_frames
                )


                if (
                    long_enough
                    and silence_complete
                ):

                    self.in_speech = False

                    speech_ended = True

                    self._speech_run = 0

                    self._silence_run = 0

                    self._utterance_frames = 0


        return VADResult(
            is_speech=
                is_speech,

            speech_started=
                speech_started,

            speech_ended=
                speech_ended,

            in_speech=
                self.in_speech,

            level=
                level,

            threshold=
                self.speech_threshold,
        )


# ---------------------------------------------------------------------------
# Frame Size Helper
# ---------------------------------------------------------------------------

def frame_samples(
    *,
    sample_rate: int = DEFAULT_SAMPLE_RATE,
    frame_duration_ms: int = DEFAULT_FRAME_DURATION_MS,
):
    """
    Returns the number of samples required for one VAD frame.
    """

    if sample_rate <= 0:

        raise ValueError(
            "sample_rate must be positive."
        )


    if frame_duration_ms <= 0:

        raise ValueError(
            "frame_duration_ms must be positive."
        )


    return int(
        sample_rate
        * (
            frame_duration_ms
            / 1000.0
        )
    )


# ---------------------------------------------------------------------------
# Standalone Diagnostic
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    detector = (
        VoiceActivityDetector()
    )


    print(
        "E.V.I.E. Phase 14B VAD"
    )


    print(
        "----------------------"
    )


    print(
        "Sample rate:",
        detector.sample_rate,
    )


    print(
        "Frame duration:",
        f"{detector.frame_duration_ms} ms",
    )


    print(
        "Frame samples:",
        frame_samples(
            sample_rate=
                detector.sample_rate,

            frame_duration_ms=
                detector.frame_duration_ms,
        ),
    )


    print(
        "Speech threshold:",
        detector.speech_threshold,
    )


    print(
        "Endpoint silence:",
        f"{detector.end_silence_ms} ms",
    )