from assistant.voice.presentation import (
    build_contextual_expansion_prompt,
    is_contextual_expansion_request,
    prepare_voice_presentation,
    remember_authoritative_response,
)


def test_capability_inventory_gets_natural_summary():
    full = '''
My currently supported core capabilities include:
- agent: Multi-step planning.
- browser: Structured browser interaction.
- coding: Repository-level coding.
- memory: Persistent selective memory.
- vision: Screen interpretation.
- workflows: Persistent workflows.
'''
    result = prepare_voice_presentation("What can you do?", full)
    assert result.mode == "concise"
    assert "conversation" in result.text.lower()
    assert "break down any capability" in result.text.lower()
    assert result.was_condensed is True


def test_health_gets_natural_summary_with_caveat():
    full = '''
Yes, Max — based on the latest diagnostic evidence I have, I’m healthy.
Known healthy areas include memory, tools, integrations, voice, vision, GPU,
and runtime directories.
Important caveat: I have not run a fresh deep diagnostic in this exact turn.
'''
    result = prepare_voice_presentation("Are you healthy?", full)
    assert "latest health state is healthy" in result.text.lower()
    assert "fresh deep diagnostic" in result.text.lower()


def test_detail_request_keeps_full_response():
    full = "One. Two. Three. Four. Five. Six."
    result = prepare_voice_presentation("Go into detail.", full)
    assert result.mode == "detailed"
    assert "Six." in result.text
    assert result.was_condensed is False


def test_expansion_request_detection():
    assert is_contextual_expansion_request("Okay, tell me more.")
    assert is_contextual_expansion_request("What exactly is wrong?")
    assert not is_contextual_expansion_request("What can you do?")


def test_contextual_expansion_receives_previous_full_answer():
    remember_authoritative_response(
        "Are you healthy?",
        "Full previous health answer with component details.",
        "Short health answer.",
    )
    prompt = build_contextual_expansion_prompt("Elaborate.")
    assert "Full previous health answer" in prompt
    assert "same topic" in prompt


def test_generic_condense_preserves_failure_sentence():
    full = (
        "The request completed partially. "
        "Most supporting services responded normally. "
        "Calendar failed because the account is not provisioned. "
        "The next action is to use the personal Google account."
    )
    result = prepare_voice_presentation("What happened?", full)
    lower = result.text.lower()
    assert "calendar failed" in lower
    assert "next action" in lower
