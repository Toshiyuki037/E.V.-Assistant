"""
Phase 12N structural test expansion regression.
"""

import assistant.workspace.repository.store as repo_store

from assistant.workspace.repository.controller import (
    index_repository,
)

from assistant.coding.discovery import (
    discover_candidate_paths,
)


def test_relevant_importing_test_is_added_to_candidates(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(
        repo_store,
        "REPOSITORY_RUNTIME",
        tmp_path
        / "runtime",
    )

    assistant = (
        tmp_path
        / "assistant"
    )

    workflows = (
        assistant
        / "workflows"
    )

    tests = (
        tmp_path
        / "tests"
    )

    workflows.mkdir(
        parents=True,
    )

    tests.mkdir(
        parents=True,
    )

    (
        assistant
        / "__init__.py"
    ).write_text(
        "",
        encoding="utf-8",
    )

    (
        workflows
        / "__init__.py"
    ).write_text(
        "",
        encoding="utf-8",
    )

    (
        workflows
        / "integration.py"
    ).write_text(
        (
            "def _format_schedule_next_run(schedule):\n"
            "    timezone = schedule['timezone']\n"
            "    return f\"schedule {timezone}\"\n"
        ),
        encoding="utf-8",
    )

    (
        tests
        / "test_workflow_commands.py"
    ).write_text(
        (
            "from assistant.workflows.integration import (\n"
            "    _format_schedule_next_run,\n"
            ")\n"
            "\n"
            "def test_schedule_display():\n"
            "    result = _format_schedule_next_run(\n"
            "        {'timezone': 'UTC'}\n"
            "    )\n"
            "    assert result\n"
        ),
        encoding="utf-8",
    )

    index_repository(
        str(
            tmp_path
        ),
        repository=
            "structural-test-expansion",
    )

    paths = discover_candidate_paths(
        "structural-test-expansion",
        (
            "Improve workflow schedule timezone "
            "display formatting."
        ),
        max_candidates=8,
    )

    assert (
        "assistant/workflows/integration.py"
        in paths
    )

    assert (
        "tests/test_workflow_commands.py"
        in paths
    )