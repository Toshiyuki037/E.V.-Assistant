"""
E.V.I.E. - Streaming Transcription Runtime

Created: August 12, 2026
Author: Max Maehara

Phase 14C

Purpose:
    Provides model-independent transcript result/event models and a
    latest-only background partial-transcription worker.

Architecture:
    This module does NOT:
        - access the microphone
        - load Whisper
        - perform reasoning
        - finalize user requests

    It receives audio snapshots and a supplied transcription callable.

Design:
    Only the newest pending audio snapshot matters. Older partial
    snapshots are discarded rather than building an inference backlog.
"""

from __future__ import annotations

import queue
import threading
import time

from dataclasses import (
    dataclass,
)

from typing import (
    Callable,
)

import numpy as np


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

@dataclass(
    frozen=True
)
class TranscriptionResult:
    text: str

    language: str | None = None

    language_probability: float | None = None


@dataclass(
    frozen=True
)
class TranscriptEvent:
    kind: str

    text: str

    language: str | None

    language_probability: float | None

    timestamp: float

    audio_seconds: float


# ---------------------------------------------------------------------------
# Normalization
# ---------------------------------------------------------------------------

def normalize_transcript(
    text: str,
) -> str:
    """
    Normalizes whitespace without changing transcript meaning.
    """

    return (
        " ".join(
            str(
                text
                or ""
            ).split()
        )
        .strip()
    )


# ---------------------------------------------------------------------------
# Partial Transcription Worker
# ---------------------------------------------------------------------------

class PartialTranscriber:
    """
    Runs partial transcription away from the microphone capture loop.

    The microphone thread may continue collecting audio while the
    recognizer processes the most recent snapshot.

    Queue policy:
        latest snapshot wins

    This prevents Whisper from processing stale partial snapshots
    after the user has already spoken additional words.
    """

    def __init__(
        self,
        *,
        transcribe_fn: Callable[
            [np.ndarray],
            TranscriptionResult,
        ],
        emit_fn: Callable[
            [TranscriptEvent],
            None,
        ]
        | None = None,
        sample_rate: int = 16000,
    ):

        self.transcribe_fn = (
            transcribe_fn
        )

        self.emit_fn = (
            emit_fn
        )

        self.sample_rate = int(
            sample_rate
        )


        if self.sample_rate <= 0:

            raise ValueError(
                "sample_rate must be positive."
            )


        self._queue: queue.Queue = (
            queue.Queue(
                maxsize=1
            )
        )


        self._thread = (
            threading.Thread(
                target=
                    self._run,

                daemon=
                    True,

                name=
                    "evie-partial-transcriber",
            )
        )


        self._started = False

        self._closed = False

        self._lock = (
            threading.Lock()
        )

        self._last_text = ""


    # -----------------------------------------------------------------------
    # Start
    # -----------------------------------------------------------------------

    def start(
        self,
    ):
        with self._lock:

            if self._closed:

                raise RuntimeError(
                    "PartialTranscriber is closed."
                )


            if self._started:

                return


            self._started = True


        self._thread.start()


    # -----------------------------------------------------------------------
    # Replace Pending Snapshot
    # -----------------------------------------------------------------------

    def _replace_pending(
        self,
        item,
    ):
        try:

            self._queue.put_nowait(
                item
            )


            return


        except queue.Full:

            pass


        try:

            self._queue.get_nowait()


        except queue.Empty:

            pass


        try:

            self._queue.put_nowait(
                item
            )


        except queue.Full:

            # Another producer replaced the item first.
            pass


    # -----------------------------------------------------------------------
    # Submit
    # -----------------------------------------------------------------------

    def submit(
        self,
        audio: np.ndarray,
    ):
        """
        Submits the newest accumulated utterance snapshot.
        """

        with self._lock:

            if self._closed:

                return False


        if not self._started:

            self.start()


        snapshot = (
            np.asarray(
                audio,
                dtype=np.int16,
            )
            .copy()
        )


        if snapshot.size == 0:

            return False


        self._replace_pending(
            snapshot
        )


        return True


    # -----------------------------------------------------------------------
    # Worker
    # -----------------------------------------------------------------------

    def _run(
        self,
    ):
        while True:

            item = (
                self._queue.get()
            )


            if item is None:

                return


            try:

                result = (
                    self.transcribe_fn(
                        item
                    )
                )


            except Exception as error:

                print(
                    (
                        "\n[Partial transcription warning] "
                        f"{error}"
                    )
                )


                continue


            text = (
                normalize_transcript(
                    result.text
                )
            )


            if not text:

                continue


            # ---------------------------------------------------------------
            # Duplicate Suppression
            # ---------------------------------------------------------------

            if text == self._last_text:

                continue


            self._last_text = text


            audio_seconds = (
                len(
                    item
                )
                / float(
                    self.sample_rate
                )
            )


            event = (
                TranscriptEvent(
                    kind=
                        "partial",

                    text=
                        text,

                    language=
                        result.language,

                    language_probability=
                        result.language_probability,

                    timestamp=
                        time.time(),

                    audio_seconds=
                        audio_seconds,
                )
            )


            if self.emit_fn is not None:

                self.emit_fn(
                    event
                )


    # -----------------------------------------------------------------------
    # Stop
    # -----------------------------------------------------------------------

    def stop(
        self,
        *,
        wait: bool = True,
    ):
        """
        Stops future partial transcription.

        wait=True guarantees the worker has stopped before the final
        transcription pass begins.
        """

        with self._lock:

            if self._closed:

                return


            self._closed = True


        self._replace_pending(
            None
        )


        if (
            wait
            and self._started
            and self._thread.is_alive()
        ):

            self._thread.join()


    # -----------------------------------------------------------------------
    # State
    # -----------------------------------------------------------------------

    @property
    def last_text(
        self,
    ):
        return self._last_text