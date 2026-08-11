"""
Phase 12N candidate discovery v2 regressions.
"""

import assistant.workspace.repository.store as repo_store

from assistant.workspace.repository.controller import index_repository
from assistant.coding.discovery import discover_candidate_paths


def _base_repo(tmp_path):
    assistant = tmp_path / "assistant"
    workflows = assistant / "workflows"
    coding = assistant / "coding"
    tests = tmp_path / "tests"

    workflows.mkdir(parents=True)
    coding.mkdir(parents=True)
    tests.mkdir(parents=True)

    (assistant / "__init__.py").write_text("", encoding="utf-8")
    (workflows / "__init__.py").write_text("", encoding="utf-8")
    (coding / "__init__.py").write_text("", encoding="utf-8")

    return workflows, coding, tests


def test_long_self_engineering_prompt_prefers_schedule_subsystem(tmp_path, monkeypatch):
    monkeypatch.setattr(
        repo_store,
        "REPOSITORY_RUNTIME",
        tmp_path / "runtime",
    )

    workflows, coding, tests = _base_repo(tmp_path)

    (workflows / "integration.py").write_text(
        "def _format_schedule_next_run(schedule):\n"
        "    timezone = schedule['timezone']\n"
        "    next_run = schedule['next_run_at']\n"
        "    return f'{next_run} {timezone}'\n",
        encoding="utf-8",
    )

    (workflows / "schedules.py").write_text(
        "def create_schedule(timezone, next_run_at):\n"
        "    return {'timezone': timezone, 'next_run_at': next_run_at}\n",
        encoding="utf-8",
    )

    (coding / "controller.py").write_text(
        "def execute_engineering_plan(plan):\n"
        "    return plan\n",
        encoding="utf-8",
    )

    (tests / "test_schedule.py").write_text(
        "def test_schedule_timezone_display():\n"
        "    assert True\n",
        encoding="utf-8",
    )

    index_repository(str(tmp_path), repository="discovery-v2-test")

    paths = discover_candidate_paths(
        "discovery-v2-test",
        (
            "In your own E.V.I.E. repository, prepare an executable "
            "self-engineering plan for a display-only improvement to the "
            "workflow schedule timezone output. Keep schedule storage and "
            "execution semantics unchanged. Modify only the minimum necessary "
            "source and regression-test files."
        ),
        max_candidates=4,
    )

    assert "assistant/workflows/integration.py" in paths
    assert "assistant/workflows/schedules.py" in paths


def test_focused_content_beats_generic_planner(tmp_path, monkeypatch):
    monkeypatch.setattr(
        repo_store,
        "REPOSITORY_RUNTIME",
        tmp_path / "runtime",
    )

    workflows, coding, _ = _base_repo(tmp_path)

    (workflows / "presentation.py").write_text(
        "def show_schedule(schedule):\n"
        "    return schedule['timezone']\n",
        encoding="utf-8",
    )

    (coding / "planner.py").write_text(
        "def plan_repository_change():\n"
        "    return None\n",
        encoding="utf-8",
    )

    index_repository(str(tmp_path), repository="focused-token-test")

    paths = discover_candidate_paths(
        "focused-token-test",
        (
            "Prepare a safe executable repository engineering plan "
            "to improve workflow schedule timezone presentation."
        ),
        max_candidates=2,
    )

    assert "assistant/workflows/presentation.py" in paths
