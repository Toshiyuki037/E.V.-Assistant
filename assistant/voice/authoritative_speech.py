"""
E.V.I.E. - Authoritative Speech Pipeline

Phase 14 - Smooth Spoken Chunk

Purpose:
    Preserve ONE authoritative response stream while producing ONE concise,
    natural spoken chunk instead of several independent F5 sentence calls.

Why:
    F5 has meaningful per-call startup cost. Generating sentence 1 and
    sentence 2 independently can create an audible gap if sentence 2 is not
    ready before sentence 1 finishes playing.

Production behavior:
    - accept at most 2 authoritative sentences
    - accept at most 260 spoken characters
    - run every sentence through the existing speech formatter
    - combine accepted sentences into ONE F5 generation
    - begin synthesis as soon as the voice budget is full
    - if the model response ends first, flush whatever was accepted
    - full terminal response remains untouched

This remains authoritative streaming:
    the spoken chunk is emitted before the complete model response needs
    to finish whenever the two-sentence voice budget fills early.
"""

from __future__ import annotations

import threading

from dataclasses import (
    dataclass,
)

from typing import (
    Callable,
)


DEFAULT_MAX_SPOKEN_SENTENCES = 2
DEFAULT_MAX_SPOKEN_CHARACTERS = 260


@dataclass(
    frozen=True
)
class AuthoritativeSpeechEvent:
    kind: str
    index: int
    text: str


class AuthoritativeSpeechPipeline:
    """
    Small production speech pipeline optimized for F5-TTS.

    Instead of paying F5 startup overhead once per sentence, this pipeline
    builds one concise spoken chunk from the first useful authoritative
    sentences and synthesizes it exactly once.
    """

    def __init__(
        self,
        *,
        synthesize_fn: Callable,
        play_fn: Callable,
        prepare_fn: Callable[[str], str] | None = None,
        emit_fn: Callable[[AuthoritativeSpeechEvent], None] | None = None,
        max_sentences: int = DEFAULT_MAX_SPOKEN_SENTENCES,
        max_characters: int = DEFAULT_MAX_SPOKEN_CHARACTERS,
    ):

        self.synthesize_fn = synthesize_fn
        self.play_fn = play_fn
        self.prepare_fn = prepare_fn
        self.emit_fn = emit_fn

        self.max_sentences = max(
            1,
            int(
                max_sentences
            ),
        )

        self.max_characters = max(
            40,
            int(
                max_characters
            ),
        )

        self._lock = (
            threading.RLock()
        )

        self._sentences = []

        self._characters = 0

        self._started = False

        self._input_closed = False

        self._budget_exhausted = False

        self._generation_started = False

        self._cancelled = False

        self._done = (
            threading.Event()
        )

        self._worker = None


    # -----------------------------------------------------------------------
    # Events
    # -----------------------------------------------------------------------

    def _emit(
        self,
        *,
        kind: str,
        text: str,
    ):

        if self.emit_fn is None:

            return


        self.emit_fn(
            AuthoritativeSpeechEvent(
                kind=
                    kind,

                index=
                    0,

                text=
                    text,
            )
        )


    # -----------------------------------------------------------------------
    # Start
    # -----------------------------------------------------------------------

    def start(
        self,
    ):

        with self._lock:

            if self._cancelled:

                return


            self._started = (
                True
            )


    # -----------------------------------------------------------------------
    # Text Helpers
    # -----------------------------------------------------------------------

    @staticmethod
    def _clip_to_characters(
        text: str,
        maximum: int,
    ) -> str:

        text = (
            str(
                text
                or ""
            )
            .strip()
        )


        if not text or maximum <= 0:

            return ""


        if len(
            text
        ) <= maximum:

            return text


        shortened = (
            text[
                :maximum
            ]
        )


        if " " in shortened:

            shortened = (
                shortened.rsplit(
                    " ",
                    1,
                )[0]
            )


        shortened = (
            shortened.rstrip(
                " ,;:-"
            )
        )


        if (
            shortened
            and shortened[-1]
            not in ".!?"
        ):

            shortened += "."


        return shortened


    def _spoken_text_locked(
        self,
    ) -> str:

        return (
            " ".join(
                self._sentences
            )
            .strip()
        )


    # -----------------------------------------------------------------------
    # Submit Authoritative Sentence
    # -----------------------------------------------------------------------

    def submit_sentence(
        self,
        text: str,
    ) -> bool:

        text = (
            str(
                text
                or ""
            )
            .strip()
        )


        if not text:

            return False


        if self.prepare_fn is not None:

            text = (
                str(
                    self.prepare_fn(
                        text
                    )
                    or ""
                )
                .strip()
            )


        if not text:

            return False


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


            if (
                len(
                    self._sentences
                )
                >= self.max_sentences
            ):

                self._budget_exhausted = (
                    True
                )

                return False


            separator_cost = (
                1
                if self._sentences
                else 0
            )


            remaining = (
                self.max_characters
                - self._characters
                - separator_cost
            )


            if remaining <= 0:

                self._budget_exhausted = (
                    True
                )

                return False


            original_text = (
                text
            )


            was_clipped = (
                len(
                    original_text
                )
                > remaining
            )


            text = (
                self._clip_to_characters(
                    original_text,
                    remaining,
                )
            )


            if not text:

                self._budget_exhausted = (
                    True
                )

                return False


            if self._sentences:

                self._characters += (
                    1
                )


            self._sentences.append(
                text
            )


            self._characters += len(
                text
            )


            if (
                was_clipped
                or len(
                    self._sentences
                )
                >= self.max_sentences
                or self._characters
                >= self.max_characters
            ):

                self._budget_exhausted = (
                    True
                )

                should_launch = (
                    True
                )


        self._emit(
            kind=
                "sentence_accepted",

            text=
                text,
        )


        if should_launch:

            self._launch_generation()


        return True


    # -----------------------------------------------------------------------
    # Launch One F5 Chunk
    # -----------------------------------------------------------------------

    def _launch_generation(
        self,
    ):

        with self._lock:

            if (
                self._cancelled
                or self._generation_started
            ):

                return


            text = (
                self._spoken_text_locked()
            )


            if not text:

                self._done.set()

                return


            self._generation_started = (
                True
            )


        self._worker = (
            threading.Thread(
                target=
                    self._generate_and_play,

                args=(
                    text,
                ),

                daemon=
                    True,

                name=
                    "evie-authoritative-spoken-chunk",
            )
        )


        self._worker.start()


    def _generate_and_play(
        self,
        text: str,
    ):

        self._emit(
            kind=
                "synthesis_started",

            text=
                text,
        )


        try:

            audio, sample_rate = (
                self.synthesize_fn(
                    text
                )
            )


            with self._lock:

                if self._cancelled:

                    return


            if (
                audio is None
                or int(
                    sample_rate
                )
                <= 0
            ):

                return


            self._emit(
                kind=
                    "synthesis_finished",

                text=
                    text,
            )


            self._emit(
                kind=
                    "playback_started",

                text=
                    text,
            )


            self.play_fn(
                audio,
                int(
                    sample_rate
                ),
            )


            self._emit(
                kind=
                    "playback_finished",

                text=
                    text,
            )


        except Exception as error:

            print(
                "\n[Authoritative Speech Warning]"
            )

            print(
                error
            )


        finally:

            self._done.set()


    # -----------------------------------------------------------------------
    # Input Complete
    # -----------------------------------------------------------------------

    def finish_input(
        self,
    ):

        with self._lock:

            if self._input_closed:

                return


            self._input_closed = (
                True
            )


            launch_needed = (
                bool(
                    self._sentences
                )
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

            self._launch_generation()


    # -----------------------------------------------------------------------
    # Wait
    # -----------------------------------------------------------------------

    def wait(
        self,
        timeout: float | None = None,
    ) -> bool:

        return (
            self._done.wait(
                timeout=
                    timeout
            )
        )


    # -----------------------------------------------------------------------
    # Cancel Foundation
    # -----------------------------------------------------------------------

    def cancel(
        self,
    ):

        with self._lock:

            self._cancelled = (
                True
            )


        self._done.set()
