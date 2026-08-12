from assistant.voice.session import (
    run_voice_session,
)


def test_wait_pauses_and_continue_resumes():

    paused = []

    resumed = []

    stopped = []

    calls = 0


    def fake_listen(
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

            on_speech_started()

            return (
                "Wait."
            )


        if calls == 3:

            on_speech_started()

            return (
                "Continue."
            )


        return (
            "stop listening"
        )


    result = (
        run_voice_session(
            listen_fn=
                fake_listen,

            process_prompt_fn=
                lambda text:
                    None,

            interrupt_speech_fn=
                lambda:
                    stopped.append(
                        True
                    ),

            pause_speech_fn=
                lambda:
                    paused.append(
                        True
                    ),

            resume_speech_fn=
                lambda:
                    resumed.append(
                        True
                    ),

            speech_started_fn=
                lambda:
                    paused.append(
                        "vad",
                    ),
        )
    )


    assert (
        "vad"
        in paused
    )

    assert (
        True
        in paused
    )

    assert resumed == [
        True
    ]

    assert (
        result.reason
        == "return_to_mode"
    )
