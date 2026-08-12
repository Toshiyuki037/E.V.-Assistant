from __future__ import annotations

import threading
import time

from assistant.voice.session import (
    run_voice_session,
)


def test_barge_in_queues_new_turn_without_concurrent_prompt_workers(
    monkeypatch,
):

    monkeypatch.setenv(
        "EVIE_DUPLEX_MODE",
        "headset",
    )

    release_first = (
        threading.Event()
    )

    first_started = (
        threading.Event()
    )

    prompts = []

    active = 0

    max_active = 0

    lock = (
        threading.Lock()
    )


    def process_prompt(
        text,
    ):

        nonlocal active
        nonlocal max_active

        with lock:

            active += 1

            max_active = max(
                max_active,
                active,
            )

        prompts.append(
            text
        )

        if text == "First request.":

            first_started.set()

            release_first.wait(
                1.0
            )

        with lock:

            active -= 1


    calls = 0


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
                    None,
        )
    )


    assert (
        max_active
        == 1
    )

    assert prompts == [
        "First request.",
        "Actually just tell me the morning.",
    ]

    assert (
        result.reason
        == "return_to_mode"
    )
