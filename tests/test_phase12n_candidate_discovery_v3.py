"""
Phase 12N candidate discovery v3 regressions.
"""

import assistant.workspace.repository.store as repo_store

from assistant.workspace.repository.controller import index_repository
from assistant.coding.discovery import discover_candidate_paths


def _build_repo(tmp_path):
    assistant = tmp_path / "assistant"
    workflows = assistant / "workflows"
    coding = assistant / "coding"
    agent = assistant / "agent"
    tests = tmp_path / "tests"

    workflows.mkdir(parents=True)
    coding.mkdir(parents=True)
    agent.mkdir(parents=True)
    tests.mkdir(parents=True)

    for directory in (
        assistant,
        workflows,
        coding,
        agent,
    ):
        (directory / "__init__.py").write_text(
            "",
            encoding="utf-8",
        )

    (workflows / "integration.py").write_text(
        """
def _format_schedule_next_run(schedule):
    next_run_at = schedule["next_run_at"]
    timezone = schedule["timezone"]
    return f"{next_run_at} {timezone}"
""",
        encoding="utf-8",
    )

    (workflows / "schedules.py").write_text(
        """
def create_schedule(timezone, next_run_at):
    return {
        "timezone": timezone,
        "next_run_at": next_run_at,
    }
""",
        encoding="utf-8",
    )

    (workflows / "scheduler.py").write_text(
        """
def scheduler_tick(schedule):
    return schedule["next_run_at"]
""",
        encoding="utf-8",
    )

    (coding / "presentation.py").write_text(
        """
def format_engineering_plan(plan):
    return "engineering plan validation"
""",
        encoding="utf-8",
    )

    (agent / "verifier.py").write_text(
        """
def verify_plan():
    return "execution validation workflow"
""",
        encoding="utf-8",
    )

    (assistant / "brain.py").write_text(
        """
def reason():
    return "repository workflow plan execution"
""",
        encoding="utf-8",
    )

    (tests / "test_schedule.py").write_text(
        """
def test_schedule_timezone_output():
    assert True
""",
        encoding="utf-8",
    )

    return workflows, tests


def test_long_prompt_puts_integration_in_candidate_set(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(
        repo_store,
        "REPOSITORY_RUNTIME",
        tmp_path / "runtime",
    )

    _build_repo(tmp_path)

    index_repository(
        str(tmp_path),
        repository="candidate-v3-test",
    )

    prompt = (
        "In your own E.V.I.E. repository, prepare an executable "
        "self-engineering plan for a display-only improvement to the "
        "workflow schedule timezone output. Keep schedule storage and "
        "execution semantics unchanged. Modify only the minimum necessary "
        "source and regression-test files, run targeted validation and "
        "the full regression suite after execution, and stop before commit."
    )

    paths = discover_candidate_paths(
        "candidate-v3-test",
        prompt,
        max_candidates=8,
    )

    assert "assistant/workflows/integration.py" in paths
    assert "assistant/workflows/schedules.py" in paths

    assert (
        paths.index(
            "assistant/workflows/integration.py"
        )
        < (
            paths.index(
                "assistant/agent/verifier.py"
            )
            if "assistant/agent/verifier.py" in paths
            else 99
        )
    )


def test_relevant_schedule_test_is_retained(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(
        repo_store,
        "REPOSITORY_RUNTIME",
        tmp_path / "runtime",
    )

    _build_repo(tmp_path)

    index_repository(
        str(tmp_path),
        repository="candidate-v3-tests",
    )

    paths = discover_candidate_paths(
        "candidate-v3-tests",
        "Improve workflow schedule timezone output.",
        max_candidates=8,
    )

    assert "tests/test_schedule.py" in paths
