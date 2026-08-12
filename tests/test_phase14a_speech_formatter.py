from assistant.speech_formatter import (
    MAX_SENTENCES,
    MAX_SPEECH_CHARACTERS,
    prepare_spoken_text,
)


def test_short_response_preserved():
    result = prepare_spoken_text(
        "4"
    )

    assert result == "4"


def test_long_response_is_shortened():
    text = (
        "A transistor controls electrical current. "
        "It can behave as a switch. "
        "It can also behave as an amplifier. "
        "Modern processors contain billions of transistors. "
        "They are usually fabricated from semiconductor materials."
    )

    result = prepare_spoken_text(
        text
    )

    assert (
        len(
            result
        )
        <= MAX_SPEECH_CHARACTERS
    )


def test_long_response_sentence_limit():
    text = (
        "Sentence one. "
        "Sentence two. "
        "Sentence three. "
        "Sentence four."
    )

    result = prepare_spoken_text(
        text
    )

    sentence_count = (
        result.count(
            "."
        )
    )

    assert (
        sentence_count
        <= MAX_SENTENCES
    )


def test_markdown_removed():
    result = prepare_spoken_text(
        (
            "**E.V.I.E.** uses "
            "`computer_control`."
        )
    )

    assert "**" not in result
    assert "`" not in result


def test_numbered_list_formatting_removed():
    result = prepare_spoken_text(
        (
            "Two uses are:\n"
            "1. Switching current.\n"
            "2. Amplifying signals."
        )
    )

    assert "1." not in result
    assert "2." not in result