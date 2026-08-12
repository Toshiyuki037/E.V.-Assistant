from dataclasses import dataclass

from assistant.voice.session import (
    run_voice_session,
)


@dataclass(
    frozen=True
)
class FakeResult:

    matched: bool

    similarity: float


def test_wake_auth_runs_before_inline_prompt():

    events = []

    calls = 0


    def listen_fn():

        nonlocal calls

        calls += 1

        if calls == 1:

            return (
                "Evie, good morning."
            )

        return (
            "stop listening"
        )


    result = (
        run_voice_session(
            listen_fn=
                listen_fn,

            process_prompt_fn=
                lambda text:
                    events.append(
                        (
                            "prompt",
                            text,
                        )
                    ),

            require_wake=
                True,

            wake_authenticate_fn=
                lambda:
                    FakeResult(
                        matched=True,
                        similarity=0.99,
                    ),

            wake_authenticated_fn=
                lambda:
                    events.append(
                        (
                            "auth",
                            None,
                        )
                    ),
        )
    )


    assert events[
        0
    ][
        0
    ] == "auth"

    assert events[
        1
    ][
        0
    ] == "prompt"

    assert (
        result.reason
        == "return_to_mode"
    )
