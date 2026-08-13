"""
E.V.I.E. - Authoritative Speech Pipeline

Phase 14 Rolling Speech Compatibility Fix

Two operating modes are intentionally supported:

rolling=False (default)
    Preserves the original Phase 14 contract:
    - max_sentences/max_characters are TOTAL voice budgets
    - later sentences are rejected
    - legacy Phase 14 regression tests remain valid

rolling=True
    New rolling full-response mode:
    - max_sentences/max_characters are PER-CHUNK budgets
    - accepted sentences continue into later chunks
    - while chunk N is playing, chunk N+1 may synthesize
    - the full authoritative response can be spoken
"""

from __future__ import annotations

import queue
import threading

from dataclasses import dataclass
from typing import Callable


DEFAULT_MAX_SPOKEN_SENTENCES = 2
DEFAULT_MAX_SPOKEN_CHARACTERS = 260


@dataclass(frozen=True)
class AuthoritativeSpeechEvent:
    kind: str
    index: int
    text: str


class AuthoritativeSpeechPipeline:

    def __init__(
        self,
        *,
        synthesize_fn: Callable,
        play_fn: Callable,
        prepare_fn: Callable[[str], str] | None = None,
        emit_fn: Callable[[AuthoritativeSpeechEvent], None] | None = None,
        max_sentences: int = DEFAULT_MAX_SPOKEN_SENTENCES,
        max_characters: int = DEFAULT_MAX_SPOKEN_CHARACTERS,
        rolling: bool = False,
    ):
        self.synthesize_fn = synthesize_fn
        self.play_fn = play_fn
        self.prepare_fn = prepare_fn
        self.emit_fn = emit_fn

        self.max_sentences = max(1, int(max_sentences))
        self.max_characters = max(40, int(max_characters))
        self.rolling = bool(rolling)

        self._lock = threading.RLock()
        self._started = False
        self._input_closed = False
        self._cancelled = False
        self._done = threading.Event()

        # Legacy / total-budget state.
        self._sentences = []
        self._characters = 0
        self._budget_exhausted = False
        self._generation_started = False
        self._worker = None

        # Rolling state.
        self._pending_sentences = []
        self._pending_characters = 0
        self._chunk_index = 0
        self._text_queue = queue.Queue(maxsize=3)
        self._audio_queue = queue.Queue(maxsize=2)
        self._text_sentinel = object()
        self._audio_sentinel = object()
        self._synthesis_worker = None
        self._playback_worker = None


    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------

    def _emit(
        self,
        *,
        kind: str,
        text: str,
        index: int = 0,
    ):
        if self.emit_fn is None:
            return

        self.emit_fn(
            AuthoritativeSpeechEvent(
                kind=kind,
                index=index,
                text=text,
            )
        )


    # ------------------------------------------------------------------
    # Start
    # ------------------------------------------------------------------

    def start(self):
        with self._lock:
            if self._cancelled or self._started:
                return

            self._started = True

        if not self.rolling:
            return

        self._synthesis_worker = threading.Thread(
            target=self._rolling_synthesis_loop,
            daemon=True,
            name="evie-authoritative-synthesis",
        )

        self._playback_worker = threading.Thread(
            target=self._rolling_playback_loop,
            daemon=True,
            name="evie-authoritative-playback",
        )

        self._synthesis_worker.start()
        self._playback_worker.start()


    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _clip_to_characters(
        text: str,
        maximum: int,
    ) -> str:
        text = str(text or "").strip()

        if not text or maximum <= 0:
            return ""

        if len(text) <= maximum:
            return text

        shortened = text[:maximum]

        if " " in shortened:
            shortened = shortened.rsplit(" ", 1)[0]

        shortened = shortened.rstrip(" ,;:-")

        if shortened and shortened[-1] not in ".!?":
            shortened += "."

        return shortened


    def _prepare(
        self,
        text: str,
    ) -> str:
        text = str(text or "").strip()

        if not text:
            return ""

        if self.prepare_fn is not None:
            text = str(
                self.prepare_fn(text)
                or ""
            ).strip()

        return text


    # ==================================================================
    # LEGACY TOTAL-BUDGET MODE
    # ==================================================================

    def _legacy_spoken_text_locked(self) -> str:
        return " ".join(
            self._sentences
        ).strip()


    def _legacy_submit_sentence(
        self,
        text: str,
    ) -> bool:
        if not self._started:
            self.start()

        should_launch = False

        with self._lock:
            if (
                self._cancelled
                or self._input_closed
                or self._budget_exhausted
                or self._generation_started
            ):
                return False

            if len(self._sentences) >= self.max_sentences:
                self._budget_exhausted = True
                return False

            separator_cost = 1 if self._sentences else 0

            remaining = (
                self.max_characters
                - self._characters
                - separator_cost
            )

            if remaining <= 0:
                self._budget_exhausted = True
                return False

            original_text = text
            was_clipped = len(original_text) > remaining

            text = self._clip_to_characters(
                original_text,
                remaining,
            )

            if not text:
                self._budget_exhausted = True
                return False

            if self._sentences:
                self._characters += 1

            self._sentences.append(text)
            self._characters += len(text)

            if (
                was_clipped
                or len(self._sentences) >= self.max_sentences
                or self._characters >= self.max_characters
            ):
                self._budget_exhausted = True
                should_launch = True

        self._emit(
            kind="sentence_accepted",
            text=text,
            index=0,
        )

        if should_launch:
            self._legacy_launch_generation()

        return True


    def _legacy_launch_generation(self):
        with self._lock:
            if self._cancelled or self._generation_started:
                return

            text = self._legacy_spoken_text_locked()

            if not text:
                self._done.set()
                return

            self._generation_started = True

        self._worker = threading.Thread(
            target=self._legacy_generate_and_play,
            args=(text,),
            daemon=True,
            name="evie-authoritative-spoken-chunk",
        )

        self._worker.start()


    def _legacy_generate_and_play(
        self,
        text: str,
    ):
        self._emit(
            kind="synthesis_started",
            text=text,
            index=0,
        )

        try:
            audio, sample_rate = self.synthesize_fn(text)

            with self._lock:
                if self._cancelled:
                    return

            if audio is None or int(sample_rate) <= 0:
                return

            self._emit(
                kind="synthesis_finished",
                text=text,
                index=0,
            )

            self._emit(
                kind="playback_started",
                text=text,
                index=0,
            )

            self.play_fn(
                audio,
                int(sample_rate),
            )

            self._emit(
                kind="playback_finished",
                text=text,
                index=0,
            )

        except Exception as error:
            print("\n[Authoritative Speech Warning]")
            print(error)

        finally:
            self._done.set()


    # ==================================================================
    # ROLLING PER-CHUNK MODE
    # ==================================================================

    def _rolling_flush_pending_locked(self):
        if not self._pending_sentences:
            return None

        text = " ".join(
            self._pending_sentences
        ).strip()

        index = self._chunk_index
        self._chunk_index += 1

        self._pending_sentences = []
        self._pending_characters = 0

        return (
            index,
            text,
        )


    def _rolling_queue_pending_chunk(self):
        with self._lock:
            item = self._rolling_flush_pending_locked()

        if item is None:
            return

        index, text = item

        self._emit(
            kind="chunk_queued",
            text=text,
            index=index,
        )

        self._text_queue.put(item)


    def _rolling_submit_sentence(
        self,
        text: str,
    ) -> bool:
        if not self._started:
            self.start()

        with self._lock:
            if self._cancelled or self._input_closed:
                return False

            separator = (
                1
                if self._pending_sentences
                else 0
            )

            would_exceed_characters = (
                bool(self._pending_sentences)
                and (
                    self._pending_characters
                    + separator
                    + len(text)
                    > self.max_characters
                )
            )

            would_exceed_sentences = (
                len(self._pending_sentences)
                >= self.max_sentences
            )

            if (
                would_exceed_characters
                or would_exceed_sentences
            ):
                item = self._rolling_flush_pending_locked()
            else:
                item = None

        if item is not None:
            index, old_text = item

            self._emit(
                kind="chunk_queued",
                text=old_text,
                index=index,
            )

            self._text_queue.put(item)

        with self._lock:
            if self._cancelled or self._input_closed:
                return False

            # A single very long authoritative sentence must not be
            # silently discarded. Clip this chunk only; later sentences
            # remain eligible for later rolling chunks.
            text = self._clip_to_characters(
                text,
                self.max_characters,
            )

            if not text:
                return False

            if self._pending_sentences:
                self._pending_characters += 1

            self._pending_sentences.append(text)
            self._pending_characters += len(text)

            queue_now = (
                len(self._pending_sentences)
                >= self.max_sentences
                or self._pending_characters
                >= self.max_characters
            )

            index = self._chunk_index

        self._emit(
            kind="sentence_accepted",
            text=text,
            index=index,
        )

        if queue_now:
            self._rolling_queue_pending_chunk()

        return True


    def _rolling_synthesis_loop(self):
        try:
            while True:
                item = self._text_queue.get()

                if item is self._text_sentinel:
                    break

                index, text = item

                if self._cancelled:
                    break

                self._emit(
                    kind="synthesis_started",
                    text=text,
                    index=index,
                )

                try:
                    audio, sample_rate = self.synthesize_fn(text)

                except Exception as error:
                    print("\n[Authoritative Speech Warning]")
                    print(error)
                    continue

                if self._cancelled:
                    break

                if audio is None or int(sample_rate) <= 0:
                    continue

                self._emit(
                    kind="synthesis_finished",
                    text=text,
                    index=index,
                )

                self._audio_queue.put(
                    (
                        index,
                        text,
                        audio,
                        int(sample_rate),
                    )
                )

        finally:
            self._audio_queue.put(
                self._audio_sentinel
            )


    def _rolling_playback_loop(self):
        try:
            while True:
                item = self._audio_queue.get()

                if item is self._audio_sentinel:
                    break

                (
                    index,
                    text,
                    audio,
                    sample_rate,
                ) = item

                if self._cancelled:
                    break

                self._emit(
                    kind="playback_started",
                    text=text,
                    index=index,
                )

                try:
                    self.play_fn(
                        audio,
                        sample_rate,
                    )

                except Exception as error:
                    print("\n[Authoritative Playback Warning]")
                    print(error)

                self._emit(
                    kind="playback_finished",
                    text=text,
                    index=index,
                )

                if self._cancelled:
                    break

        finally:
            self._done.set()


    # ------------------------------------------------------------------
    # Public submit
    # ------------------------------------------------------------------

    def submit_sentence(
        self,
        text: str,
    ) -> bool:
        text = self._prepare(text)

        if not text:
            return False

        if self.rolling:
            return self._rolling_submit_sentence(text)

        return self._legacy_submit_sentence(text)


    # ------------------------------------------------------------------
    # Input Complete
    # ------------------------------------------------------------------

    def finish_input(self):
        if self.rolling:
            if not self._started:
                self.start()

            with self._lock:
                if self._input_closed:
                    return

                self._input_closed = True
                item = self._rolling_flush_pending_locked()

            if item is not None:
                index, text = item

                self._emit(
                    kind="chunk_queued",
                    text=text,
                    index=index,
                )

                self._text_queue.put(item)

            self._text_queue.put(
                self._text_sentinel
            )

            return

        # Legacy behavior.
        with self._lock:
            if self._input_closed:
                return

            self._input_closed = True

            launch_needed = (
                bool(self._sentences)
                and not self._generation_started
                and not self._cancelled
            )

            nothing_to_speak = (
                not self._sentences
            )

        if nothing_to_speak:
            self._done.set()
            return

        if launch_needed:
            self._legacy_launch_generation()


    # ------------------------------------------------------------------
    # Wait / Cancel
    # ------------------------------------------------------------------

    def wait(
        self,
        timeout: float | None = None,
    ) -> bool:
        return self._done.wait(
            timeout=timeout
        )


    def cancel(self):
        with self._lock:
            self._cancelled = True

        if self.rolling:
            try:
                self._text_queue.put_nowait(
                    self._text_sentinel
                )

            except queue.Full:
                pass

        self._done.set()
