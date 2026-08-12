"""
Phase 14J production pause-then-stop ownership tests.
"""

from __future__ import annotations

import threading
import time

from assistant.voice.session import (
    run_voice_session,
)


def test_revision_pauses_at_onset_then_stops_after_transcription():

    events = []

    release_first = (
        threading.Event()
    )

    first_started = (
        threading.Event()
    )

    prompts = []

    calls = 0


    def process_prompt(
        text,
    ):

        prompts.append(
            text
        )

        if text == "First request.":

            first_started.set()

            release_first.wait(
                1.0
            )


    def listen_fn(
        *,
        on_speech_started=None,
    ):

        nonlocal calls

        calls += 1

        if calls == 1:

            return (
                "First request."
            )

        if calls == 2:

            assert first_started.wait(
                1.0
            )

            on_speech_started()

            events.append(
                "transcribed_revision"
            )

            release_first.set()

            return (
                "Actually just tell me the morning."
            )

        deadline = (
            time.time()
            + 1.0
        )

        while (
            len(
                prompts
            )
            < 2
            and time.time()
            < deadline
        ):

            time.sleep(
                0.005
            )

        return (
            "stop listening"
        )


    result = (
        run_voice_session(
            listen_fn=
                listen_fn,

            process_prompt_fn=
                process_prompt,

            interrupt_speech_fn=
                lambda:
                    events.append(
                        "stop"
                    ),

            pause_speech_fn=
                lambda:
                    events.append(
                        "pause"
                    ),

            resume_speech_fn=
                lambda:
                    events.append(
                        "resume"
                    ),

            speech_started_fn=
                lambda:
                    events.append(
                        "pause"
                    ),
        )
    )


    assert (
        "pause"
        in events
    )

    assert (
        "stop"
        in events
    )

    assert prompts == [
        "First request.",
        "Actually just tell me the morning.",
    ]

    assert (
        result.reason
        == "return_to_mode"
    )


def test_legacy_interrupt_callback_still_fires_once():

    interrupted = []

    calls = 0


    def listen_fn(
        *,
        on_speech_started=None,
    ):

        nonlocal calls

        calls += 1

        if calls == 1:

            on_speech_started()

            return (
                "Hello."
            )

        return (
            "stop listening"
        )


    run_voice_session(
        listen_fn=
            listen_fn,

        process_prompt_fn=
            lambda text:
                None,

        interrupt_speech_fn=
            lambda:
                interrupted.append(
                    True
                ),
    )


    assert interrupted == [
        True
    ]
