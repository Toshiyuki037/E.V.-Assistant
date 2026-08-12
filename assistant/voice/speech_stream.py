"""
E.V.I.E. - Streaming Speech Pipeline

Created: August 12, 2026
Author: Max Maehara

Phase 14E5

Purpose:
    Sentence-by-sentence provisional TTS pipeline.

Phase 14E5 fixes final-handoff behavior:

    When final transcription arrives:
        - stop accepting additional provisional sentences
        - discard queued provisional text/audio
        - if one sentence is already PLAYING, let it finish
        - if nothing is playing but one sentence is already SYNTHESIZING,
          allow only that one sentence to finish and play
        - discard all later provisional work

This creates a clean handoff from speculative voice to the authoritative
final response without loading a second F5 model or changing Phase 1-13.
"""

from __future__ import annotations

import queue
import threading
from dataclasses import dataclass
from typing import Callable, Any


@dataclass(frozen=True)
class SpeechSentence:
    version: int
    index: int
    text: str


@dataclass(frozen=True)
class SynthesizedSpeech:
    version: int
    index: int
    text: str
    audio: Any
    sample_rate: int


@dataclass(frozen=True)
class SpeechStreamEvent:
    kind: str
    version: int
    index: int
    text: str


class StreamingSpeechPipeline:
    """
    Two-stage speech pipeline:

        text queue
            ↓
        one synthesis worker
            ↓
        audio queue
            ↓
        one playback worker

    Phase 14E5 adds a "seal" state used when the final transcript arrives.
    """

    def __init__(
        self,
        *,
        synthesize_fn: Callable,
        play_fn: Callable,
        emit_fn: Callable[[SpeechStreamEvent], None] | None = None,
        text_queue_size: int = 8,
        audio_queue_size: int = 4,
    ):

        self.synthesize_fn = synthesize_fn
        self.play_fn = play_fn
        self.emit_fn = emit_fn

        self._text_queue = queue.Queue(
            maxsize=max(1, int(text_queue_size))
        )

        self._audio_queue = queue.Queue(
            maxsize=max(1, int(audio_queue_size))
        )

        self._lock = threading.Lock()

        self._current_version = 0
        self._next_index = 0

        self._started = False
        self._closed = False

        self._sealed = False

        self._active_synthesis = None
        self._active_playback = None

        # When finalization occurs while synthesis is in flight and
        # nothing is already playing, exactly this item may still finish.
        self._allowed_inflight_synthesis = None

        self._synthesis_thread = None
        self._playback_thread = None

        self._stop_token = object()


    @property
    def current_version(self) -> int:

        with self._lock:
            return self._current_version


    def is_current(self, version: int) -> bool:

        with self._lock:
            return int(version) == self._current_version


    def _emit(
        self,
        *,
        kind: str,
        version: int,
        index: int,
        text: str,
    ):

        if self.emit_fn is None:
            return

        self.emit_fn(
            SpeechStreamEvent(
                kind=kind,
                version=version,
                index=index,
                text=text,
            )
        )


    def start(self):

        with self._lock:

            if self._closed:
                raise RuntimeError(
                    "StreamingSpeechPipeline is closed."
                )

            if self._started:
                return

            self._started = True

            self._synthesis_thread = threading.Thread(
                target=self._synthesis_loop,
                daemon=True,
                name="evie-tts-synthesis",
            )

            self._playback_thread = threading.Thread(
                target=self._playback_loop,
                daemon=True,
                name="evie-tts-playback",
            )

            synthesis_thread = self._synthesis_thread
            playback_thread = self._playback_thread

        synthesis_thread.start()
        playback_thread.start()


    @staticmethod
    def _drain(q: queue.Queue):

        while True:

            try:
                q.get_nowait()

            except queue.Empty:
                return


    def begin_version(
        self,
        version: int,
    ):
        """
        Begins/replaces a provisional speech version.
        """

        version = int(version)

        with self._lock:

            if self._closed:
                return False

            if version < self._current_version:
                return False

            changed = (
                version != self._current_version
            )

            self._current_version = version

            if changed:

                self._next_index = 0
                self._sealed = False
                self._allowed_inflight_synthesis = None

        if changed:

            self._drain(
                self._text_queue
            )

            self._drain(
                self._audio_queue
            )

            self._emit(
                kind="version",
                version=version,
                index=-1,
                text="",
            )

        return True


    def submit_sentence(
        self,
        *,
        version: int,
        text: str,
    ) -> bool:

        text = str(
            text
            or ""
        ).strip()

        if not text:
            return False

        if not self._started:
            self.start()

        version = int(version)

        with self._lock:

            if self._closed:
                return False

            if self._sealed:
                return False

            if version != self._current_version:
                return False

            index = self._next_index
            self._next_index += 1

        item = SpeechSentence(
            version=version,
            index=index,
            text=text,
        )

        try:

            self._text_queue.put(
                item,
                timeout=0.25,
            )

        except queue.Full:

            self._emit(
                kind="dropped",
                version=version,
                index=index,
                text=text,
            )

            return False

        self._emit(
            kind="queued",
            version=version,
            index=index,
            text=text,
        )

        return True


    def seal_current(
        self,
    ):
        """
        Final-transcript handoff.

        Stop future provisional speech without interrupting one sentence
        the user is already hearing.

        Rules:
            1. If playback is active:
                   let that playback finish
                   discard synthesis/queues

            2. If playback is NOT active but synthesis is active:
                   allow exactly that synthesis item to finish and play

            3. Discard every queued later sentence.
        """

        with self._lock:

            if self._closed:
                return

            self._sealed = True

            if self._active_playback is not None:

                self._allowed_inflight_synthesis = None

            elif self._active_synthesis is not None:

                self._allowed_inflight_synthesis = (
                    self._active_synthesis
                )

            else:

                self._allowed_inflight_synthesis = None


        self._drain(
            self._text_queue
        )

        self._drain(
            self._audio_queue
        )


        self._emit(
            kind="sealed",
            version=self.current_version,
            index=-1,
            text="",
        )


    def cancel(
        self,
        version: int | None = None,
    ):
        """
        Full cancellation used for session/application shutdown.

        Current physical playback still cannot be forcibly interrupted
        until Phase 14F.
        """

        with self._lock:

            if version is None:
                self._current_version += 1

            elif int(version) >= self._current_version:
                self._current_version = int(version) + 1

            current = self._current_version

            self._next_index = 0
            self._sealed = True
            self._allowed_inflight_synthesis = None

        self._drain(
            self._text_queue
        )

        self._drain(
            self._audio_queue
        )

        self._emit(
            kind="cancelled",
            version=current,
            index=-1,
            text="",
        )


    def _synthesis_loop(self):

        while True:

            item = self._text_queue.get()

            if item is self._stop_token:
                return


            with self._lock:

                if (
                    item.version
                    != self._current_version
                ):

                    continue

                if self._sealed:
                    continue

                self._active_synthesis = (
                    item
                )


            self._emit(
                kind="synthesis_started",
                version=item.version,
                index=item.index,
                text=item.text,
            )


            try:

                audio, sample_rate = (
                    self.synthesize_fn(
                        item.text
                    )
                )

            except Exception as error:

                with self._lock:

                    if (
                        self._active_synthesis
                        == item
                    ):

                        self._active_synthesis = None


                if self.is_current(
                    item.version
                ):

                    self._emit(
                        kind="error",
                        version=item.version,
                        index=item.index,
                        text=str(error),
                    )

                continue


            with self._lock:

                if (
                    self._active_synthesis
                    == item
                ):

                    self._active_synthesis = None


                current = (
                    item.version
                    == self._current_version
                )


                if not current:

                    allowed = False


                elif not self._sealed:

                    allowed = True


                else:

                    allowed = (
                        self._allowed_inflight_synthesis
                        == item
                    )


                    if allowed:

                        # One-shot allowance.
                        self._allowed_inflight_synthesis = None


            if not allowed:
                continue


            synthesized = SynthesizedSpeech(
                version=item.version,
                index=item.index,
                text=item.text,
                audio=audio,
                sample_rate=int(sample_rate),
            )


            try:

                self._audio_queue.put(
                    synthesized,
                    timeout=0.25,
                )

            except queue.Full:

                self._emit(
                    kind="dropped",
                    version=item.version,
                    index=item.index,
                    text=item.text,
                )

                continue


            self._emit(
                kind="synthesis_finished",
                version=item.version,
                index=item.index,
                text=item.text,
            )


    def _playback_loop(self):

        while True:

            item = self._audio_queue.get()

            if item is self._stop_token:
                return


            with self._lock:

                if (
                    item.version
                    != self._current_version
                ):

                    continue


                # A sealed version may still play the one in-flight
                # synthesis item that was explicitly allowed above.
                self._active_playback = (
                    item
                )


            self._emit(
                kind="playback_started",
                version=item.version,
                index=item.index,
                text=item.text,
            )


            try:

                self.play_fn(
                    item.audio,
                    item.sample_rate,
                )

            except Exception as error:

                if self.is_current(
                    item.version
                ):

                    self._emit(
                        kind="error",
                        version=item.version,
                        index=item.index,
                        text=str(error),
                    )

            else:

                if self.is_current(
                    item.version
                ):

                    self._emit(
                        kind="playback_finished",
                        version=item.version,
                        index=item.index,
                        text=item.text,
                    )


            finally:

                with self._lock:

                    if (
                        self._active_playback
                        == item
                    ):

                        self._active_playback = None


    def close(
        self,
        *,
        wait: bool = True,
    ):

        with self._lock:

            if self._closed:
                return

            self._closed = True


        self._drain(
            self._text_queue
        )

        self._drain(
            self._audio_queue
        )


        if self._started:

            self._text_queue.put(
                self._stop_token
            )

            self._audio_queue.put(
                self._stop_token
            )


        if wait:

            if (
                self._synthesis_thread
                is not None
                and self._synthesis_thread.is_alive()
            ):

                self._synthesis_thread.join(
                    timeout=2.0
                )


            if (
                self._playback_thread
                is not None
                and self._playback_thread.is_alive()
            ):

                self._playback_thread.join(
                    timeout=2.0
                )
