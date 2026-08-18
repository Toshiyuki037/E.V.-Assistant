from dataclasses import dataclass

from assistant.performance.model_router import (
    should_use_fast_voice_reasoning,
)


@dataclass
class Profile:
    mode: str = "fast"
    allow_long_term_memory: bool = False
    allow_project_knowledge: bool = False


def test_stable_general_question_uses_fast_route():
    assert should_use_fast_voice_reasoning(
        "What is a transistor?",
        Profile(),
    ) is True


def test_project_question_stays_authoritative():
    assert should_use_fast_voice_reasoning(
        "Where is memory retrieval implemented in this project?",
        Profile(
            mode="project",
            allow_project_knowledge=True,
        ),
    ) is False


def test_screen_question_stays_authoritative():
    assert should_use_fast_voice_reasoning(
        "What can you see on my screen?",
        Profile(),
    ) is False


def test_live_question_stays_authoritative():
    assert should_use_fast_voice_reasoning(
        "What is the weather today?",
        Profile(),
    ) is False


def test_personal_question_stays_authoritative():
    assert should_use_fast_voice_reasoning(
        "What is my GPA?",
        Profile(),
    ) is False


def test_debugging_stays_authoritative():
    assert should_use_fast_voice_reasoning(
        "Explain this error and how to fix it.",
        Profile(),
    ) is False


def test_explicit_detail_stays_authoritative():
    assert should_use_fast_voice_reasoning(
        "Explain transistors in detail.",
        Profile(),
    ) is False
