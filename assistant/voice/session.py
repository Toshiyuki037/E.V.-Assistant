"""
E.V.I.E. - Phase 14 Final Voice Session Runtime

Design goals:
    - preserve frozen Phase 1-13 request routing
    - stable speaker-safe mode by default
    - optional headset duplex barge-in mode
    - wake / standby / timeout
    - contextual commands
    - temporary conversational state
    - voice authentication as one wake-time trust signal

Important:
    The default production mode remains speaker-safe.

    Voice authentication NEVER bypasses frozen Phase 1-13 authorization.
"""

from __future__ import annotations

import os
import threading

from dataclasses import (
    dataclass,
)

from typing import (
    Callable,
)

from .commands import (
    classify_live_voice_command,
)

from .conversation_state import (
    VoiceConversationState,
)

from .runtime_state import (
    VoiceRuntimeMode,
    VoiceRuntimeState,
)

from .wake import (
    extract_wake_request,
    is_sleep_command,
)


def safe_go_back_prompt(
    prompt_history: list[str],
) -> str:

    state = (
        VoiceConversationState()
    )

    for prompt in prompt_history:

        state.remember_prompt(
            prompt
        )

    return (
        state.safe_go_back_prompt()
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


class PromptWorker:

    def __init__(
        self,
        process_prompt_fn,
    ):

        self.process_prompt_fn = (
            process_prompt_fn
        )

        self._thread = None

        self._lock = (
            threading.Lock()
        )


    @property
    def active(
        self,
    ) -> bool:

        with self._lock:

            return (
                self._thread is not None
                and self._thread.is_alive()
            )


    def start(
        self,
        text: str,
    ) -> bool:

        with self._lock:

            if (
                self._thread is not None
                and self._thread.is_alive()
            ):

                return False

            thread = (
                threading.Thread(
                    target=
                        self.process_prompt_fn,
                    args=(
                        text,
                    ),
                    daemon=True,
                    name=
                        "evie-voice-turn",
                )
            )

            self._thread = (
                thread
            )

        thread.start()

        return True


    def wait(
        self,
    ):

        with self._lock:

            thread = (
                self._thread
            )

        if thread is not None:

            thread.join()


def _authenticate_wake(
    *,
    wake_authenticate_fn,
    wake_authenticated_fn,
    wake_unrecognized_fn,
):
    """
    Performs optional wake-time voice verification.

    Returns:
        True  -> verified
        False -> not verified / unavailable

    The session still wakes on a failed voice signal because voice identity
    is intentionally NOT the sole authorization mechanism.
    """

    if wake_authenticate_fn is None:

        return False


    try:

        result = (
            wake_authenticate_fn()
        )

    except Exception as error:

        print(
            (
                "[Voice authentication warning] "
                f"{error}"
            )
        )

        return False


    matched = bool(
        getattr(
            result,
            "matched",
            result,
        )
    )


    similarity = getattr(
        result,
        "similarity",
        None,
    )


    if similarity is not None:

        print(
            (
                "[Voice identity] "
                f"similarity={float(similarity):.4f}"
            )
        )


    if matched:

        if wake_authenticated_fn is not None:

            wake_authenticated_fn()

        return True


    if wake_unrecognized_fn is not None:

        wake_unrecognized_fn()


    return False


def _run_safe_session(
    *,
    listen_fn,
    process_prompt_fn,
    runtime: VoiceRuntimeState,
    conversation: VoiceConversationState,
    active_timeout_seconds: float,
    wake_authenticate_fn=None,
    wake_authenticated_fn=None,
    wake_unrecognized_fn=None,
):

    while True:

        user_text = (
            str(
                listen_fn()
                or ""
            )
            .strip()
        )


        if not user_text:

            if (
                runtime.mode
                == VoiceRuntimeMode.ACTIVE
                and runtime.idle_seconds()
                >= active_timeout_seconds
            ):

                runtime.set_mode(
                    VoiceRuntimeMode.STANDBY
                )

                print(
                    "E.V.I.E.: Standing by."
                )

            continue


        runtime.touch()


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


        if runtime.mode in {
            VoiceRuntimeMode.STANDBY,
            VoiceRuntimeMode.SLEEPING,
        }:

            woke, wake_request = (
                extract_wake_request(
                    user_text
                )
            )

            if not woke:

                continue


            print(
                "[Voice authentication...]"
            )


            _authenticate_wake(
                wake_authenticate_fn=
                    wake_authenticate_fn,
                wake_authenticated_fn=
                    wake_authenticated_fn,
                wake_unrecognized_fn=
                    wake_unrecognized_fn,
            )


            runtime.set_mode(
                VoiceRuntimeMode.ACTIVE
            )


            if not wake_request:

                continue


            user_text = (
                wake_request
            )


        if is_sleep_command(
            user_text
        ):

            runtime.set_mode(
                VoiceRuntimeMode.STANDBY
            )

            print(
                "E.V.I.E.: Standing by."
            )

            continue


        live_command = (
            classify_live_voice_command(
                user_text
            )
        )


        if live_command == "go_back":

            user_text = (
                conversation.safe_go_back_prompt()
            )


        elif live_command in {
            "stop",
            "wait",
            "continue",
            "never_mind",
        }:

            if live_command == "never_mind":

                print(
                    "E.V.I.E.: Okay."
                )

            continue


        conversation.remember_prompt(
            user_text
        )

        process_prompt_fn(
            user_text
        )


def _run_headset_duplex_session(
    *,
    listen_fn,
    process_prompt_fn,
    stop_speech_fn,
    pause_speech_fn,
    resume_speech_fn,
    speech_started_fn,
    runtime: VoiceRuntimeState,
    conversation: VoiceConversationState,
    active_timeout_seconds: float,
    wake_authenticate_fn=None,
    wake_authenticated_fn=None,
    wake_unrecognized_fn=None,
):

    worker = (
        PromptWorker(
            process_prompt_fn
        )
    )

    pending_prompt = None


    onset_callback = (
        speech_started_fn
        or pause_speech_fn
        or stop_speech_fn
    )


    onset_is_stop = (
        speech_started_fn is None
        and pause_speech_fn is None
        and stop_speech_fn is not None
    )


    def stop_after_transcription():

        if (
            not onset_is_stop
            and stop_speech_fn
            is not None
        ):

            stop_speech_fn()


    def launch_pending_if_ready():

        nonlocal pending_prompt

        if (
            pending_prompt
            and not worker.active
        ):

            next_prompt = (
                pending_prompt
            )

            pending_prompt = None

            conversation.remember_prompt(
                next_prompt
            )

            worker.start(
                next_prompt
            )

            return True

        return False


    def drain_pending_before_exit():

        nonlocal pending_prompt

        worker.wait()

        if pending_prompt:

            next_prompt = (
                pending_prompt
            )

            pending_prompt = None

            conversation.remember_prompt(
                next_prompt
            )

            worker.start(
                next_prompt
            )

            worker.wait()


    while True:

        launch_pending_if_ready()


        if (
            runtime.mode
            in {
                VoiceRuntimeMode.ACTIVE,
                VoiceRuntimeMode.PAUSED,
            }
            and onset_callback
            is not None
        ):

            user_text = (
                str(
                    listen_fn(
                        on_speech_started=
                            onset_callback,
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


        if not user_text:

            if (
                runtime.mode
                == VoiceRuntimeMode.ACTIVE
                and runtime.idle_seconds()
                >= active_timeout_seconds
                and not worker.active
            ):

                runtime.set_mode(
                    VoiceRuntimeMode.STANDBY
                )

                print(
                    "E.V.I.E.: Standing by."
                )

            continue


        runtime.touch()


        command = (
            classify_voice_session_command(
                user_text
            )
        )


        if command == "return_to_mode":

            stop_after_transcription()

            drain_pending_before_exit()

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

            stop_after_transcription()

            worker.wait()

            pending_prompt = None

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


        if runtime.mode in {
            VoiceRuntimeMode.STANDBY,
            VoiceRuntimeMode.SLEEPING,
        }:

            woke, wake_request = (
                extract_wake_request(
                    user_text
                )
            )

            if not woke:

                continue


            print(
                "[Voice authentication...]"
            )


            _authenticate_wake(
                wake_authenticate_fn=
                    wake_authenticate_fn,
                wake_authenticated_fn=
                    wake_authenticated_fn,
                wake_unrecognized_fn=
                    wake_unrecognized_fn,
            )


            runtime.set_mode(
                VoiceRuntimeMode.ACTIVE
            )


            if not wake_request:

                continue


            user_text = (
                wake_request
            )


        if is_sleep_command(
            user_text
        ):

            stop_after_transcription()

            runtime.set_mode(
                VoiceRuntimeMode.STANDBY
            )

            pending_prompt = None

            print(
                "E.V.I.E.: Standing by."
            )

            continue


        live_command = (
            classify_live_voice_command(
                user_text
            )
        )


        if live_command == "wait":

            if pause_speech_fn is not None:

                pause_speech_fn()

            runtime.set_mode(
                VoiceRuntimeMode.PAUSED
            )

            print(
                "E.V.I.E.: Paused."
            )

            continue


        if live_command == "continue":

            if resume_speech_fn is not None:

                resume_speech_fn()

            runtime.set_mode(
                VoiceRuntimeMode.ACTIVE
            )

            print(
                "E.V.I.E.: Continuing."
            )

            continue


        if live_command == "stop":

            stop_after_transcription()

            runtime.set_mode(
                VoiceRuntimeMode.ACTIVE
            )

            print(
                "E.V.I.E.: Stopped."
            )

            continue


        if live_command == "never_mind":

            stop_after_transcription()

            pending_prompt = None

            conversation.pending_revision = (
                None
            )

            runtime.set_mode(
                VoiceRuntimeMode.ACTIVE
            )

            print(
                "E.V.I.E.: Okay."
            )

            continue


        if live_command == "go_back":

            stop_after_transcription()

            user_text = (
                conversation.safe_go_back_prompt()
            )

        else:

            if worker.active:

                stop_after_transcription()


        if worker.active:

            conversation.last_interrupted_prompt = (
                conversation.history[
                    -1
                ]
                if conversation.history
                else None
            )

            pending_prompt = (
                user_text
            )

        else:

            conversation.remember_prompt(
                user_text
            )

            worker.start(
                user_text
            )


        runtime.set_mode(
            VoiceRuntimeMode.ACTIVE
        )


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
    pause_speech_fn: Callable[
        [],
        None,
    ]
    | None = None,
    resume_speech_fn: Callable[
        [],
        None,
    ]
    | None = None,
    speech_started_fn: Callable[
        [],
        None,
    ]
    | None = None,
    active_timeout_seconds: float
    | None = None,
    require_wake: bool = False,
    wake_authenticate_fn=None,
    wake_authenticated_fn=None,
    wake_unrecognized_fn=None,
) -> VoiceSessionResult:

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


    runtime = (
        VoiceRuntimeState()
    )

    conversation = (
        VoiceConversationState()
    )


    if require_wake:

        runtime.set_mode(
            VoiceRuntimeMode.STANDBY
        )

        print(
            (
                "E.V.I.E.: Standing by. "
                "Say \"Evie\" to wake me."
            )
        )


    timeout = (
        float(
            active_timeout_seconds
        )
        if active_timeout_seconds
        is not None
        else float(
            os.getenv(
                "EVIE_VOICE_SESSION_TIMEOUT",
                "60",
            )
        )
    )


    duplex_mode = (
        os.getenv(
            "EVIE_DUPLEX_MODE",
            "safe",
        )
        .strip()
        .lower()
    )


    if duplex_mode == "headset":

        print(
            "E.V.I.E.: Headset duplex enabled."
        )

        return (
            _run_headset_duplex_session(
                listen_fn=
                    listen_fn,
                process_prompt_fn=
                    process_prompt_fn,
                stop_speech_fn=
                    interrupt_speech_fn,
                pause_speech_fn=
                    pause_speech_fn,
                resume_speech_fn=
                    resume_speech_fn,
                speech_started_fn=
                    speech_started_fn,
                runtime=
                    runtime,
                conversation=
                    conversation,
                active_timeout_seconds=
                    timeout,
                wake_authenticate_fn=
                    wake_authenticate_fn,
                wake_authenticated_fn=
                    wake_authenticated_fn,
                wake_unrecognized_fn=
                    wake_unrecognized_fn,
            )
        )


    return (
        _run_safe_session(
            listen_fn=
                listen_fn,
            process_prompt_fn=
                process_prompt_fn,
            runtime=
                runtime,
            conversation=
                conversation,
            active_timeout_seconds=
                timeout,
            wake_authenticate_fn=
                wake_authenticate_fn,
            wake_authenticated_fn=
                wake_authenticated_fn,
            wake_unrecognized_fn=
                wake_unrecognized_fn,
        )
    )
