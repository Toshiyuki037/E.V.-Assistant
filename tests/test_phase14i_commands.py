from assistant.voice.commands import (
    classify_live_voice_command,
)


def test_live_commands():

    assert (
        classify_live_voice_command(
            "Stop."
        )
        == "stop"
    )

    assert (
        classify_live_voice_command(
            "Wait."
        )
        == "wait"
    )

    assert (
        classify_live_voice_command(
            "Never mind."
        )
        == "never_mind"
    )

    assert (
        classify_live_voice_command(
            "Continue."
        )
        == "continue"
    )

    assert (
        classify_live_voice_command(
            "Go back."
        )
        == "go_back"
    )

    assert (
        classify_live_voice_command(
            "Actually just tell me the morning."
        )
        == "revision"
    )
