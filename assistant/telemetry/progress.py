"""
E.V.I.E. - Phase 14 Progress System

Created: August 12, 2026
Author: Max Maehara

Purpose:
    Provides throttled progress events for long-running E.V.I.E. tasks.

Compatibility:
    Preserves the original Phase 14A emit_progress() API while adding
    the Phase 14A.5 ProgressReporter architecture.

Goals:
    - no progress spam
    - no expensive reasoning calls for progress messages
    - deterministic progress wording
    - thread-safe operation
    - reusable later by streaming voice/UI systems
"""

from __future__ import annotations

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

MIN_PROGRESS_INTERVAL = 8.0


# ---------------------------------------------------------------------------
# Progress Event
# ---------------------------------------------------------------------------

@dataclass(
    frozen=True
)
class ProgressEvent:
    message: str
    kind: str
    timestamp: float


# ---------------------------------------------------------------------------
# Legacy Phase 14A State
# ---------------------------------------------------------------------------

_LAST_EVENT_AT = 0.0
_LAST_KEY = ""

_LEGACY_LOCK = (
    threading.Lock()
)


# ---------------------------------------------------------------------------
# Legacy emit_progress()
# ---------------------------------------------------------------------------

def emit_progress(
    key: str,
    message: str,
    *,
    force: bool = False,
):
    """
    Backward-compatible Phase 14A progress function.

    Existing code may continue calling:

        emit_progress(
            "planning",
            "Planning..."
        )

    New Phase 14A.5 code should generally prefer ProgressReporter.
    """

    global _LAST_EVENT_AT
    global _LAST_KEY


    key = (
        str(
            key
            or ""
        )
        .strip()
    )


    message = (
        str(
            message
            or ""
        )
        .strip()
    )


    if not message:

        return False


    now = (
        time.monotonic()
    )


    with _LEGACY_LOCK:

        if not force:

            if (
                key
                and key == _LAST_KEY
            ):

                return False


            if (
                _LAST_EVENT_AT
                and (
                    now
                    - _LAST_EVENT_AT
                    < MIN_PROGRESS_INTERVAL
                )
            ):

                return False


        _LAST_EVENT_AT = now

        _LAST_KEY = key


    print(
        (
            "\n[E.V.I.E. Progress] "
            f"{message}"
        )
    )


    return True


# ---------------------------------------------------------------------------
# Phase 14A.5 Progress Reporter
# ---------------------------------------------------------------------------

class ProgressReporter:
    """
    Stateful throttled progress reporter.

    Each task/request can own an independent reporter rather than
    relying on global progress state.
    """

    def __init__(
        self,
        *,
        emit: Callable[
            [ProgressEvent],
            None,
        ]
        | None = None,
        minimum_interval: float = MIN_PROGRESS_INTERVAL,
    ):

        self.emit = (
            emit
            or self._default_emit
        )


        self.minimum_interval = max(
            0.0,
            float(
                minimum_interval
            ),
        )


        self._lock = (
            threading.Lock()
        )


        self._last_emit = (
            0.0
        )


        self._last_message = (
            ""
        )


        self._closed = (
            False
        )


    # -----------------------------------------------------------------------
    # Default Output
    # -----------------------------------------------------------------------

    @staticmethod
    def _default_emit(
        event: ProgressEvent,
    ):
        print(
            (
                "\n[E.V.I.E. Progress] "
                f"{event.message}"
            )
        )


    # -----------------------------------------------------------------------
    # Report
    # -----------------------------------------------------------------------

    def report(
        self,
        message: str,
        *,
        kind: str = "progress",
        force: bool = False,
    ):
        """
        Emits one progress event when allowed by throttling rules.
        """

        message = (
            str(
                message
                or ""
            )
            .strip()
        )


        if not message:

            return False


        now = (
            time.monotonic()
        )


        with self._lock:

            if self._closed:

                return False


            if not force:

                # -----------------------------------------------------------
                # Duplicate Suppression
                # -----------------------------------------------------------

                if (
                    message
                    == self._last_message
                ):

                    return False


                # -----------------------------------------------------------
                # Time Throttling
                # -----------------------------------------------------------

                if (
                    self._last_emit

                    and (
                        now
                        - self._last_emit
                        < self.minimum_interval
                    )
                ):

                    return False


            self._last_emit = (
                now
            )


            self._last_message = (
                message
            )


        event = (
            ProgressEvent(
                message=
                    message,

                kind=
                    str(
                        kind
                        or "progress"
                    ),

                timestamp=
                    time.time(),
            )
        )


        self.emit(
            event
        )


        return True


    # -----------------------------------------------------------------------
    # Close
    # -----------------------------------------------------------------------

    def close(
        self,
    ):
        """
        Prevents future progress emission.
        """

        with self._lock:

            self._closed = (
                True
            )


# ---------------------------------------------------------------------------
# Step → User-Friendly Progress Message
# ---------------------------------------------------------------------------

def progress_message_for_step(
    description: str,
    tool_name: str = "",
):
    """
    Converts an internal Phase 7 step into a concise user-facing
    progress message.

    This function is deterministic and does NOT invoke a model.
    """

    description = (
        " ".join(
            str(
                description
                or ""
            ).split()
        )
        .strip()
    )


    tool_name = (
        str(
            tool_name
            or ""
        )
        .strip()
        .lower()
    )


    # -----------------------------------------------------------------------
    # Execution
    # -----------------------------------------------------------------------

    if tool_name in {
        "run_python",
        "run_command",
    }:

        return (
            "I'm running that now."
        )


    # -----------------------------------------------------------------------
    # Filesystem Discovery
    # -----------------------------------------------------------------------

    if tool_name in {
        "read_file",
        "list_directory",
        "search_filesystem",
    }:

        return (
            "I'm checking the files now."
        )


    # -----------------------------------------------------------------------
    # File Changes
    # -----------------------------------------------------------------------

    if tool_name in {
        "write_file",
        "create_file",
    }:

        return (
            "I found what needs changing. "
            "I'm applying it now."
        )


    # -----------------------------------------------------------------------
    # Computer Control
    # -----------------------------------------------------------------------

    if (
        tool_name
        == "computer_control"
    ):

        return (
            "I'm handling the computer "
            "actions now."
        )


    # -----------------------------------------------------------------------
    # Browser
    # -----------------------------------------------------------------------

    if (
        tool_name.startswith(
            "browser_"
        )
    ):

        return (
            "I'm checking that in the "
            "browser now."
        )


    # -----------------------------------------------------------------------
    # Connected Services
    # -----------------------------------------------------------------------

    if (
        tool_name
        == "integration_execute"
    ):

        return (
            "I'm checking the connected "
            "service now."
        )


    # -----------------------------------------------------------------------
    # Description-Based Fallbacks
    # -----------------------------------------------------------------------

    lowered = (
        description.lower()
    )


    if "test" in lowered:

        return (
            "I'm running the tests now."
        )


    if (
        "search" in lowered
        or "locate" in lowered
        or "find" in lowered
    ):

        return (
            "I'm locating that now."
        )


    if "verify" in lowered:

        return (
            "I'm verifying the result now."
        )


    if (
        "commit" in lowered
        or "git" in lowered
    ):

        return (
            "I'm checking the repository now."
        )


    # -----------------------------------------------------------------------
    # Generic Fallback
    # -----------------------------------------------------------------------

    return (
        "I'm still working on it."
    )


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def make_progress_reporter(
    *,
    minimum_interval: float = MIN_PROGRESS_INTERVAL,
):
    return (
        ProgressReporter(
            minimum_interval=
                minimum_interval,
        )
    )