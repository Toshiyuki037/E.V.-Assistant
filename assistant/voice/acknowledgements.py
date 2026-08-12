"""
E.V.I.E. - Cached Voice Acknowledgements

Phase 14A.5

Purpose:
    Plays pre-generated acknowledgement lines immediately while
    E.V.I.E. continues processing the user's request.

Examples:
    "On it."
    "Got it."
    "Checking."
    "Yes, boss."
    "Got it, boss."

Phase 14 voice-auth integration:
    A wake authentication greeting already serves as the immediate
    spoken acknowledgement for that request.

    Example:

        User:
            "Evie, open my VS Code workspace."

        E.V.I.E.:
            "Voice authenticated. Welcome home, Max."

        processing begins...

    E.V.I.E. must NOT immediately follow that with:
        "Got it, boss."

    suppress_next_acknowledgement() provides this one-shot behavior.
"""

from __future__ import annotations

import random
import threading

from pathlib import (
    Path,
)

import sounddevice as sd
import soundfile as sf


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

ROOT = (
    Path(
        __file__
    )
    .resolve()
    .parents[
        2
    ]
)


CACHE_DIR = (
    ROOT
    / "runtime"
    / "voice_cache"
)


# ---------------------------------------------------------------------------
# Cached Files
# ---------------------------------------------------------------------------

ACK_FILES = {
    "on_it":
        "on_it.wav",

    "got_it":
        "got_it.wav",

    "checking":
        "checking.wav",

    "working":
        "working_on_it.wav",

    "one_moment":
        "one_moment.wav",

    "yes_boss":
        "yes_boss.wav",

    "got_it_boss":
        "got_it_boss.wav",
}


DEFAULT_ACKS = (
    "on_it",
    "got_it",
    "checking",
    "yes_boss",
)


# ---------------------------------------------------------------------------
# Playback / State Locks
# ---------------------------------------------------------------------------

_play_lock = (
    threading.Lock()
)


_state_lock = (
    threading.Lock()
)


_skip_next_acknowledgement = (
    False
)


# ---------------------------------------------------------------------------
# One-Shot Suppression
# ---------------------------------------------------------------------------

def suppress_next_acknowledgement():
    """
    Suppresses exactly one future acknowledgement.

    Used when E.V.I.E. has already spoken a wake-authentication line.
    """

    global _skip_next_acknowledgement


    with _state_lock:

        _skip_next_acknowledgement = (
            True
        )


def _consume_acknowledgement_suppression() -> bool:
    """
    Returns True once when acknowledgement playback should be skipped.
    """

    global _skip_next_acknowledgement


    with _state_lock:

        if not _skip_next_acknowledgement:

            return False


        _skip_next_acknowledgement = (
            False
        )


        return True


# ---------------------------------------------------------------------------
# Cache Inspection
# ---------------------------------------------------------------------------

def acknowledgement_path(
    name: str,
) -> Path:

    return (
        CACHE_DIR
        / ACK_FILES.get(
            name,
            name,
        )
    )


def acknowledgement_available(
    name: str,
) -> bool:

    return (
        acknowledgement_path(
            name
        )
        .is_file()
    )


def available_acknowledgements() -> list[
    str
]:

    return [
        name

        for name
        in ACK_FILES

        if acknowledgement_available(
            name
        )
    ]


# ---------------------------------------------------------------------------
# Playback
# ---------------------------------------------------------------------------

def _play_wav(
    path: Path,
) -> None:

    try:

        audio, sample_rate = (
            sf.read(
                str(
                    path
                )
            )
        )


        with _play_lock:

            sd.play(
                audio,
                sample_rate,
            )

            sd.wait()


    except Exception as exc:

        print(
            (
                "[Voice acknowledgement warning] "
                f"{exc}"
            )
        )


def play_acknowledgement(
    name: str
    | None = None,
    *,
    asynchronous: bool = True,
) -> bool:
    """
    Plays one cached acknowledgement.

    Returns:
        True:
            acknowledgement playback was started

        False:
            acknowledgement was suppressed or unavailable
    """

    # -----------------------------------------------------------------------
    # Wake Authentication Already Spoke
    # -----------------------------------------------------------------------

    if _consume_acknowledgement_suppression():

        return False


    # -----------------------------------------------------------------------
    # Automatic Selection
    # -----------------------------------------------------------------------

    if name is None:

        choices = [
            candidate

            for candidate
            in DEFAULT_ACKS

            if acknowledgement_available(
                candidate
            )
        ]


        if not choices:

            return False


        name = (
            random.choice(
                choices
            )
        )


    # -----------------------------------------------------------------------
    # Resolve Cache File
    # -----------------------------------------------------------------------

    path = (
        acknowledgement_path(
            name
        )
    )


    if not path.is_file():

        return False


    # -----------------------------------------------------------------------
    # Play
    # -----------------------------------------------------------------------

    if asynchronous:

        threading.Thread(
            target=
                _play_wav,

            args=(
                path,
            ),

            daemon=
                True,

            name=
                "evie-acknowledgement",
        ).start()


    else:

        _play_wav(
            path
        )


    return True


# ---------------------------------------------------------------------------
# Contextual Selection
# ---------------------------------------------------------------------------

def choose_acknowledgement(
    *,
    long_task: bool = False,
    checking: bool = False,
) -> str | None:

    if checking:

        preferred = (
            "checking",
            "on_it",
            "got_it",
        )


    elif long_task:

        preferred = (
            "on_it",
            "working",
            "got_it",
        )


    else:

        preferred = (
            DEFAULT_ACKS
        )


    choices = [
        candidate

        for candidate
        in preferred

        if acknowledgement_available(
            candidate
        )
    ]


    if not choices:

        return None


    return (
        random.choice(
            choices
        )
    )