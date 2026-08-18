from assistant.performance.conversation_fastpath import (
    handle_fast_conversation,
)


def test_social_turns_are_fast():
    assert handle_fast_conversation(
        "Thank you."
    ).handled is True

    assert handle_fast_conversation(
        "EV, good afternoon."
    ).handled is True


def test_continuation_words_are_not_intercepted():
    assert handle_fast_conversation(
        "okay"
    ).handled is False

    assert handle_fast_conversation(
        "approved"
    ).handled is False


def test_real_question_falls_through():
    assert handle_fast_conversation(
        "What is a transistor?"
    ).handled is False
