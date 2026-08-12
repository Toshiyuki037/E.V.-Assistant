"""
Phase 14C partial transcription tests.

No microphone, Whisper model, CUDA, or network access is required.
"""

import threading
import time

import numpy as np

from assistant.voice.transcription import (
    PartialTranscriber,
    TranscriptionResult,
    normalize_transcript,
)


def _audio(
    seconds: float,
    sample_rate: int = 16000,
):
    return np.zeros(
        int(
            seconds
            * sample_rate
        ),
        dtype=np.int16,
    )


def test_transcript_whitespace_normalization():

    assert (
        normalize_transcript(
            "  hello    there \n world "
        )
        == "hello there world"
    )


def test_partial_event_is_emitted():

    events = []


    def transcribe(
        audio,
    ):

        return (
            TranscriptionResult(
                text=
                    "hello world",

                language=
                    "en",

                language_probability=
                    0.99,
            )
        )


    worker = (
        PartialTranscriber(
            transcribe_fn=
                transcribe,

            emit_fn=
                events.append,
        )
    )


    worker.submit(
        _audio(
            1.0
        )
    )


    time.sleep(
        0.05
    )


    worker.stop(
        wait=True
    )


    assert len(
        events
    ) == 1


    assert (
        events[0].kind
        == "partial"
    )


    assert (
        events[0].text
        == "hello world"
    )


    assert (
        events[0].language
        == "en"
    )


def test_duplicate_partial_text_is_suppressed():

    events = []


    def transcribe(
        audio,
    ):

        return (
            TranscriptionResult(
                text=
                    "same text"
            )
        )


    worker = (
        PartialTranscriber(
            transcribe_fn=
                transcribe,

            emit_fn=
                events.append,
        )
    )


    worker.submit(
        _audio(
            1.0
        )
    )


    time.sleep(
        0.05
    )


    worker.submit(
        _audio(
            2.0
        )
    )


    time.sleep(
        0.05
    )


    worker.stop(
        wait=True
    )


    assert len(
        events
    ) == 1


def test_empty_partial_is_not_emitted():

    events = []


    worker = (
        PartialTranscriber(
            transcribe_fn=
                lambda audio:
                    TranscriptionResult(
                        text=""
                    ),

            emit_fn=
                events.append,
        )
    )


    worker.submit(
        _audio(
            1.0
        )
    )


    time.sleep(
        0.05
    )


    worker.stop(
        wait=True
    )


    assert events == []


def test_latest_snapshot_replaces_stale_pending_snapshot():

    events = []

    first_started = (
        threading.Event()
    )

    release_first = (
        threading.Event()
    )


    call_lengths = []


    def transcribe(
        audio,
    ):

        call_lengths.append(
            len(
                audio
            )
        )


        if len(
            call_lengths
        ) == 1:

            first_started.set()

            release_first.wait(
                timeout=1.0
            )


        return (
            TranscriptionResult(
                text=
                    str(
                        len(
                            audio
                        )
                    )
            )
        )


    worker = (
        PartialTranscriber(
            transcribe_fn=
                transcribe,

            emit_fn=
                events.append,
        )
    )


    worker.submit(
        _audio(
            1.0
        )
    )


    assert first_started.wait(
        timeout=1.0
    )


    # While snapshot 1 is being processed, submit two newer states.
    # The 2-second snapshot should be discarded in favor of 3 seconds.

    worker.submit(
        _audio(
            2.0
        )
    )


    worker.submit(
        _audio(
            3.0
        )
    )


    release_first.set()


    time.sleep(
        0.10
    )


    worker.stop(
        wait=True
    )


    assert (
        int(
            call_lengths[-1]
        )
        == 48000
    )


    assert len(
        call_lengths
    ) <= 2


def test_audio_duration_is_reported():

    events = []


    worker = (
        PartialTranscriber(
            transcribe_fn=
                lambda audio:
                    TranscriptionResult(
                        text="hello"
                    ),

            emit_fn=
                events.append,

            sample_rate=
                16000,
        )
    )


    worker.submit(
        _audio(
            2.0
        )
    )


    time.sleep(
        0.05
    )


    worker.stop(
        wait=True
    )


    assert len(
        events
    ) == 1


    assert abs(
        events[0].audio_seconds
        - 2.0
    ) < 0.01