"""
E.V.I.E. - Provisional Reasoning Stream

Created: August 12, 2026
Author: Max Maehara

Phase 14D4

Purpose:
    Runs lightweight provisional reasoning for streaming speech.

Architecture:
    This module belongs exclusively to the Phase 14 voice runtime.

    It does NOT:
        - execute tools
        - mutate memory
        - route final requests
        - replace process_prompt()
        - replace brain.chat()

    Final authoritative requests continue through the original
    E.V.I.E. pipeline.

Phase 14D4:
    Adds:
        - candidate debounce
        - latest-candidate coalescing
        - single-flight provisional generation
        - stale-output suppression
        - deterministic invalidation

    Rapid Whisper revisions no longer launch one model request per
    partial hypothesis.
"""

from __future__ import annotations

import re
import threading
import time

from dataclasses import (
    dataclass,
)

from typing import (
    Callable,
)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# A provisional hypothesis must remain the newest candidate for this long
# before it is allowed to consume a reasoning generation.
PROVISIONAL_DEBOUNCE_SECONDS = 0.35


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

@dataclass(
    frozen=True
)
class ReasoningStreamEvent:
    kind: str

    version: int

    text: str


@dataclass(
    frozen=True
)
class PendingReasoningCandidate:
    version: int

    text: str

    submitted_at: float


# ---------------------------------------------------------------------------
# Sentence Accumulator
# ---------------------------------------------------------------------------

class ResponseSentenceAccumulator:
    """
    Converts arbitrary streamed model text deltas into complete
    response sentences.

    Incomplete trailing text remains buffered until more deltas arrive.
    """

    def __init__(
        self,
    ):

        self.buffer = ""


    def reset(
        self,
    ):

        self.buffer = ""


    def add(
        self,
        delta: str,
    ):
        """
        Adds one text delta.

        Returns newly completed sentences.
        """

        delta = (
            str(
                delta
                or ""
            )
        )


        if not delta:

            return []


        self.buffer += delta


        sentences = []


        while True:

            match = re.search(
                r"^(.+?[.!?])(?=\s|$)",
                self.buffer,
                flags=re.DOTALL,
            )


            if match is None:

                break


            sentence = (
                " ".join(
                    match.group(
                        1
                    )
                    .split()
                )
                .strip()
            )


            if sentence:

                sentences.append(
                    sentence
                )


            self.buffer = (
                self.buffer[
                    match.end():
                ]
                .lstrip()
            )


        return sentences


    def flush(
        self,
    ):
        """
        Returns any remaining non-empty trailing text.
        """

        trailing = (
            " ".join(
                self.buffer.split()
            )
            .strip()
        )


        self.buffer = ""


        return trailing


# ---------------------------------------------------------------------------
# Provisional Reasoning Worker
# ---------------------------------------------------------------------------

class ProvisionalReasoningWorker:
    """
    Owns provisional reasoning for one voice utterance.

    Phase 14D4 uses two stages:

        candidate submission
            ↓
        debounce / coalescing
            ↓
        one active reasoning generation

    Rapidly changing Whisper hypotheses replace the pending candidate
    instead of spawning a new model request.

    If a newer candidate arrives while reasoning is already active,
    the active generation becomes stale immediately. Its output is
    suppressed.

    A replacement generation is started only after the newest candidate
    survives the debounce window and the previous generation exits.

    This keeps provisional reasoning single-flight.
    """

    def __init__(
        self,
        *,
        stream_fn: Callable,
        emit_fn: Callable[
            [ReasoningStreamEvent],
            None,
        ]
        | None = None,
        debounce_seconds: float = PROVISIONAL_DEBOUNCE_SECONDS,
    ):

        self.stream_fn = (
            stream_fn
        )

        self.emit_fn = (
            emit_fn
        )

        self.debounce_seconds = max(
            0.0,
            float(
                debounce_seconds
            ),
        )


        self._lock = (
            threading.Lock()
        )


        # Newest accepted version from the streaming-input layer.
        self._current_version = 0


        # Latest candidate waiting for debounce.
        self._pending_candidate = None


        # Timer associated with the latest pending candidate.
        self._debounce_timer = None


        # Only one model generation may be active at a time.
        self._active_thread = None

        self._active_version = None


    # -----------------------------------------------------------------------
    # Current Version
    # -----------------------------------------------------------------------

    @property
    def current_version(
        self,
    ):

        with self._lock:

            return (
                self._current_version
            )


    def is_current(
        self,
        version: int,
    ):

        with self._lock:

            return (
                version
                == self._current_version
            )


    # -----------------------------------------------------------------------
    # Active State
    # -----------------------------------------------------------------------

    def _active_locked(
        self,
    ) -> bool:

        return (
            self._active_thread
            is not None

            and self._active_thread.is_alive()
        )


    # -----------------------------------------------------------------------
    # Invalidate
    # -----------------------------------------------------------------------

    def invalidate(
        self,
        version: int | None = None,
    ):
        """
        Invalidates provisional output and cancels pending debounce work.

        Python cannot forcibly terminate a model-stream thread safely.

        Instead:
            - current-version state advances
            - stale callbacks stop publishing immediately
            - pending work is discarded
            - an already-running model stream exits through its existing
              is_current callback when the stream implementation observes it
        """

        timer = None


        with self._lock:

            if version is None:

                self._current_version += 1

            elif (
                version
                >= self._current_version
            ):

                self._current_version = (
                    version
                    + 1
                )


            self._pending_candidate = None


            timer = (
                self._debounce_timer
            )

            self._debounce_timer = None


        if timer is not None:

            timer.cancel()


    # -----------------------------------------------------------------------
    # Emit
    # -----------------------------------------------------------------------

    def _emit(
        self,
        event: ReasoningStreamEvent,
    ):

        if self.emit_fn is None:

            return


        if not self.is_current(
            event.version
        ):

            return


        self.emit_fn(
            event
        )


    # -----------------------------------------------------------------------
    # Start / Submit Candidate
    # -----------------------------------------------------------------------

    def start(
        self,
        *,
        version: int,
        text: str,
    ):
        """
        Submits one provisional reasoning candidate.

        For compatibility with the Phase 14D2/14D3 public interface,
        this method remains named start().

        Phase 14D4 changes its behavior:

            OLD:
                every call immediately created a reasoning thread

            NEW:
                every call replaces the pending candidate and restarts
                a short debounce timer

        Only the latest stable candidate is eventually launched.
        """

        text = (
            str(
                text
                or ""
            )
            .strip()
        )


        if not text:

            return False


        candidate = (
            PendingReasoningCandidate(
                version=
                    int(
                        version
                    ),

                text=
                    text,

                submitted_at=
                    time.monotonic(),
            )
        )


        old_timer = None


        with self._lock:

            if (
                candidate.version
                < self._current_version
            ):

                return False


            # ---------------------------------------------------------------
            # Immediately invalidate output from older generations.
            # ---------------------------------------------------------------

            self._current_version = (
                candidate.version
            )


            # ---------------------------------------------------------------
            # Coalesce to newest Whisper hypothesis.
            # ---------------------------------------------------------------

            self._pending_candidate = (
                candidate
            )


            old_timer = (
                self._debounce_timer
            )


            timer = (
                threading.Timer(
                    self.debounce_seconds,
                    self._debounce_ready,
                    args=(
                        candidate.version,
                    ),
                )
            )


            timer.daemon = True

            timer.name = (
                "evie-provisional-debounce-"
                f"{candidate.version}"
            )


            self._debounce_timer = (
                timer
            )


        if old_timer is not None:

            old_timer.cancel()


        timer.start()


        return True


    # -----------------------------------------------------------------------
    # Debounce Completion
    # -----------------------------------------------------------------------

    def _debounce_ready(
        self,
        version: int,
    ):
        """
        Called after a candidate survives the debounce interval.

        If another candidate replaced it, this call does nothing.

        If reasoning is already running, the candidate remains pending
        until that generation exits.

        Otherwise it becomes the single active generation.
        """

        candidate = None


        with self._lock:

            pending = (
                self._pending_candidate
            )


            if pending is None:

                return


            if (
                pending.version
                != version
            ):

                return


            if (
                version
                != self._current_version
            ):

                return


            self._debounce_timer = None


            # ---------------------------------------------------------------
            # Strict Single Flight
            # ---------------------------------------------------------------

            if self._active_locked():

                return


            candidate = (
                pending
            )

            self._pending_candidate = None


            thread = (
                threading.Thread(
                    target=
                        self._run,

                    kwargs={
                        "version":
                            candidate.version,

                        "text":
                            candidate.text,
                    },

                    daemon=
                        True,

                    name=
                        (
                            "evie-provisional-reasoning-"
                            f"{candidate.version}"
                        ),
                )
            )


            self._active_thread = (
                thread
            )

            self._active_version = (
                candidate.version
            )


        thread.start()


    # -----------------------------------------------------------------------
    # Launch Pending Replacement
    # -----------------------------------------------------------------------

    def _launch_pending_after_active(
        self,
    ):
        """
        Called when an active generation exits.

        A newer candidate may have arrived while the model was busy.

        If so, it is launched only if:
            - it is still current
            - it has already survived the debounce interval

        Otherwise a timer is scheduled for the remaining debounce time.
        """

        timer = None

        launch_now = False

        version = None


        with self._lock:

            pending = (
                self._pending_candidate
            )


            if pending is None:

                return


            if (
                pending.version
                != self._current_version
            ):

                self._pending_candidate = None

                return


            elapsed = (
                time.monotonic()
                - pending.submitted_at
            )


            remaining = (
                self.debounce_seconds
                - elapsed
            )


            version = (
                pending.version
            )


            if remaining <= 0:

                launch_now = True

            else:

                old_timer = (
                    self._debounce_timer
                )


                if old_timer is not None:

                    old_timer.cancel()


                timer = (
                    threading.Timer(
                        remaining,
                        self._debounce_ready,
                        args=(
                            version,
                        ),
                    )
                )


                timer.daemon = True

                timer.name = (
                    "evie-provisional-debounce-"
                    f"{version}"
                )


                self._debounce_timer = (
                    timer
                )


        if timer is not None:

            timer.start()


        if launch_now:

            self._debounce_ready(
                version
            )


    # -----------------------------------------------------------------------
    # Worker
    # -----------------------------------------------------------------------

    def _run(
        self,
        *,
        version: int,
        text: str,
    ):

        accumulator = (
            ResponseSentenceAccumulator()
        )


        self._emit(
            ReasoningStreamEvent(
                kind=
                    "started",

                version=
                    version,

                text=
                    text,
            )
        )


        def current():

            return (
                self.is_current(
                    version
                )
            )


        def on_delta(
            delta: str,
        ):

            if not current():

                return


            self._emit(
                ReasoningStreamEvent(
                    kind=
                        "delta",

                    version=
                        version,

                    text=
                        delta,
                )
            )


            sentences = (
                accumulator.add(
                    delta
                )
            )


            for sentence in sentences:

                if not current():

                    return


                self._emit(
                    ReasoningStreamEvent(
                        kind=
                            "sentence",

                        version=
                            version,

                        text=
                            sentence,
                    )
                )


        try:

            self.stream_fn(
                text,

                on_delta=
                    on_delta,

                is_current=
                    current,
            )


        except Exception as error:

            if current():

                self._emit(
                    ReasoningStreamEvent(
                        kind=
                            "error",

                        version=
                            version,

                        text=
                            str(
                                error
                            ),
                    )
                )


        else:

            if current():

                trailing = (
                    accumulator.flush()
                )


                if trailing:

                    self._emit(
                        ReasoningStreamEvent(
                            kind=
                                "sentence",

                            version=
                                version,

                            text=
                                trailing,
                        )
                    )


                self._emit(
                    ReasoningStreamEvent(
                        kind=
                            "finished",

                    version=
                        version,

                    text=
                        "",
                    )
                )


        finally:

            # ---------------------------------------------------------------
            # Release Active Generation
            # ---------------------------------------------------------------

            with self._lock:

                if (
                    self._active_version
                    == version
                ):

                    self._active_thread = None

                    self._active_version = None


            # ---------------------------------------------------------------
            # If Whisper revised the request while this generation was
            # active, allow the newest stable candidate to start now.
            # ---------------------------------------------------------------

            self._launch_pending_after_active()