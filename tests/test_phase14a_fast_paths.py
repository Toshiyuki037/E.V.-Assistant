from assistant.agent.integration import (
    should_consider_agent,
)

from assistant.memory.manager import (
    should_consider_memory,
)


def test_simple_arithmetic_skips_agent():
    assert (
        should_consider_agent(
            "What's 2 + 2?"
        )
        is False
    )


def test_simple_question_skips_memory():
    assert (
        should_consider_memory(
            "What's 2 + 2?"
        )
        is False
    )


def test_multistep_request_uses_agent():
    assert (
        should_consider_agent(
            (
                "Open VS Code and then "
                "open Canvas."
            )
        )
        is True
    )


def test_adaptive_debug_request_uses_agent():
    assert (
        should_consider_agent(
            (
                "Run the tests and fix it "
                "if it fails."
            )
        )
        is True
    )


def test_durable_preference_considers_memory():
    assert (
        should_consider_memory(
            "I prefer dark mode."
        )
        is True
    )


def test_durable_project_fact_considers_memory():
    assert (
        should_consider_memory(
            (
                "My project uses an FPGA "
                "for neural-network inference."
            )
        )
        is True
    )


def test_explicit_forget_considers_memory():
    assert (
        should_consider_memory(
            "Forget which GPU I use."
        )
        is True
    )


def test_simple_command_skips_memory():
    assert (
        should_consider_memory(
            "Open Chrome."
        )
        is False
    )