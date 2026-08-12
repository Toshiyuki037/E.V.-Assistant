from assistant.voice.commands import (
    classify_live_voice_command,
)


def test_phase14j_contextual_commands():

    expected = {
        "Stop.": "stop",
        "Wait.": "wait",
        "Never mind.": "never_mind",
        "Continue.": "continue",
        "Go back.": "go_back",
        "Actually just tell me the morning.": "revision",
    }


    for text, command in expected.items():

        assert (
            classify_live_voice_command(
                text
            )
            == command
        )
