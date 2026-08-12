from assistant.brain import (
    should_retrieve_long_term_memory,
)


def test_simple_arithmetic_skips_memory():
    assert (
        should_retrieve_long_term_memory(
            "What's 2 + 2?"
        )
        is False
    )


def test_general_question_skips_memory():
    assert (
        should_retrieve_long_term_memory(
            "What is a transistor?"
        )
        is False
    )


def test_explicit_memory_reference_uses_memory():
    assert (
        should_retrieve_long_term_memory(
            "Do you remember what we discussed?"
        )
        is True
    )


def test_personal_project_uses_memory():
    assert (
        should_retrieve_long_term_memory(
            "What was my FPGA research idea?"
        )
        is True
    )


def test_personal_goal_uses_memory():
    assert (
        should_retrieve_long_term_memory(
            "What are my transfer goals?"
        )
        is True
    )


def test_previous_conversation_uses_memory():
    assert (
        should_retrieve_long_term_memory(
            "What did we talk about last time?"
        )
        is True
    )