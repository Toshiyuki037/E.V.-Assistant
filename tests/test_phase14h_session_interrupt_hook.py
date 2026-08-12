from assistant.voice.session import (
    run_voice_session,
)


def test_session_passes_speech_start_interrupt_callback(
    monkeypatch,
):

    monkeypatch.setenv(
        "EVIE_DUPLEX_MODE",
        "headset",
    )

    interrupted = []

    prompts = []

    calls = 0


    def fake_listen(
        *,
        on_speech_started=None,
    ):

        nonlocal calls

        calls += 1

        if calls == 1:

            assert (
                on_speech_started
                is not None
            )

            on_speech_started()

            return (
                "What is a transistor?"
            )

        return (
            "stop listening"
        )


    result = (
        run_voice_session(
            listen_fn=
                fake_listen,

            process_prompt_fn=
                prompts.append,

            interrupt_speech_fn=
                lambda:
                    interrupted.append(
                        True
                    ),
        )
    )


    assert interrupted == [
        True
    ]

    assert prompts == [
        "What is a transistor?"
    ]

    assert (
        result.reason
        == "return_to_mode"
    )
