from assistant.voice.session import (
    safe_go_back_prompt,
)


def test_go_back_does_not_blindly_reexecute_previous_prompt():

    text = (
        safe_go_back_prompt(
            [
                "Show me the calendar.",
                "Send the email.",
            ]
        )
    )


    assert (
        "Show me the calendar."
        in text
    )


    assert (
        "do not repeat or re-execute"
        in text.lower()
    )
