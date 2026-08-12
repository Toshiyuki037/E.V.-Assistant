"""
E.V.I.E. - Persistent Voice Session

Phase 14 Recovery Baseline

Purpose:
    Restores the last stable one-turn-at-a-time voice session while keeping:
        - English-only high-accuracy STT
        - VAD / 2 second endpoint
        - partial transcription
        - authoritative response streaming
        - concise spoken response
        - persistent playback
        - interruptible playback primitive

Important:
    This intentionally disables experimental full-duplex listening while
    E.V.I.E. is speaking.

Reason:
    Without acoustic echo cancellation, opening the microphone while the
    speaker is active allows E.V.I.E.'s own audio to trigger VAD and become
    a new user turn.

Architecture:
    listen()
        ↓
    finalized user utterance
        ↓
    process_prompt()
        ↓
    response / TTS completes
        ↓
    listen again

This is the safe baseline from which full-duplex barge-in can be rebuilt
with explicit echo-control / duplex state later.
"""

from __future__ import annotations

from dataclasses import (
    dataclass,
)

from typing import (
    Callable,
)


RETURN_TO_MODE_COMMANDS = {
    "stop listening",
    "exit voice mode",
    "leave voice mode",
    "terminal mode",
    "go to terminal",
    "return to terminal",
}


QUIT_APPLICATION_COMMANDS = {
    "quit",
    "exit",
    "goodbye",
    "shut down",
    "shutdown",
}


@dataclass(
    frozen=True
)
class VoiceSessionResult:

    reason: str

    quit_application: bool = False


def normalize_voice_command(
    text: str,
) -> str:

    return (
        " ".join(
            str(
                text
                or ""
            )
            .strip()
            .lower()
            .split()
        )
        .rstrip(
            ".!?"
        )
    )


def classify_voice_session_command(
    text: str,
):

    normalized = (
        normalize_voice_command(
            text
        )
    )


    if normalized in RETURN_TO_MODE_COMMANDS:

        return "return_to_mode"


    if normalized in QUIT_APPLICATION_COMMANDS:

        return "quit_application"


    return None


def run_voice_session(
    *,
    listen_fn: Callable,
    process_prompt_fn: Callable[
        [str],
        None,
    ],
    interrupt_speech_fn: Callable[
        [],
        None,
    ]
    | None = None,
    **_ignored_phase14_experimental_hooks,
) -> VoiceSessionResult:
    """
    Runs the stable persistent voice session.

    Compatibility:
        Extra Phase 14J keyword hooks are accepted and ignored so main.py
        does not have to be changed immediately during recovery.

    The microphone is NOT reopened until process_prompt_fn returns.
    """

    print()

    print(
        "E.V.I.E.: Voice session active."
    )

    print(
        (
            "Say \"stop listening\" "
            "to return to mode selection."
        )
    )


    while True:

        # ---------------------------------------------------------------
        # Capture One Finalized Utterance
        # ---------------------------------------------------------------

        if interrupt_speech_fn is not None:

            user_text = (
                str(
                    listen_fn(
                        on_speech_started=
                            interrupt_speech_fn,
                    )
                    or ""
                )
                .strip()
            )

        else:

            user_text = (
                str(
                    listen_fn()
                    or ""
                )
                .strip()
            )


        # ---------------------------------------------------------------
        # No Usable Speech
        # ---------------------------------------------------------------

        if not user_text:

            continue


        # ---------------------------------------------------------------
        # Session-Level Command
        # ---------------------------------------------------------------

        command = (
            classify_voice_session_command(
                user_text
            )
        )


        if command == "return_to_mode":

            print()

            print(
                "E.V.I.E.: Voice session ended."
            )


            return (
                VoiceSessionResult(
                    reason=
                        "return_to_mode",

                    quit_application=
                        False,
                )
            )


        if command == "quit_application":

            print()

            print(
                "E.V.I.E. Offline"
            )


            return (
                VoiceSessionResult(
                    reason=
                        "quit_application",

                    quit_application=
                        True,
                )
            )


        # ---------------------------------------------------------------
        # One Authoritative E.V.I.E. Turn
        # ---------------------------------------------------------------
        #
        # CRITICAL RECOVERY RULE:
        #
        # Do not call listen_fn() again until this returns.
        # This prevents E.V.I.E.'s own speaker audio from being captured as
        # user speech on machines without acoustic echo cancellation.
        # ---------------------------------------------------------------

        process_prompt_fn(
            user_text
        )
