"""
Phase 12N hybrid candidate discovery regression.
"""

import assistant.workspace.repository.store as repo_store

from assistant.workspace.repository.controller import (
    index_repository,
)

from assistant.coding.discovery import (
    discover_candidate_paths,
)


def test_content_relevance_finds_presentation_module(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(
        repo_store,
        "REPOSITORY_RUNTIME",
        tmp_path
        / "runtime",
    )

    package = (
        tmp_path
        / "assistant"
        / "workflows"
    )

    package.mkdir(
        parents=True,
    )

    (
        tmp_path
        / "assistant"
        / "__init__.py"
    ).write_text(
        "",
        encoding="utf-8",
    )

    (
        package
        / "__init__.py"
    ).write_text(
        "",
        encoding="utf-8",
    )

    (
        package
        / "presentation.py"
    ).write_text(
        (
            "def format_schedule(schedule):\n"
            "    return f\"Next run: {schedule['next_run_at']}\"\n"
        ),
        encoding="utf-8",
    )

    (
        package
        / "protocols.py"
    ).write_text(
        (
            "def run_protocol():\n"
            "    return True\n"
        ),
        encoding="utf-8",
    )

    index_repository(
        str(
            tmp_path
        ),
        repository=
            "discovery-test",
    )

    paths = discover_candidate_paths(
        "discovery-test",
        (
            "Diagnose and fix the protocol schedule "
            "time display in your own code."
        ),
        max_candidates=4,
    )

    assert (
        "assistant/workflows/presentation.py"
        in paths
    )


def test_tests_do_not_automatically_outrank_source(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(
        repo_store,
        "REPOSITORY_RUNTIME",
        tmp_path
        / "runtime",
    )

    package = (
        tmp_path
        / "assistant"
    )

    package.mkdir()

    (
        package
        / "__init__.py"
    ).write_text(
        "",
        encoding="utf-8",
    )

    (
        package
        / "formatter.py"
    ).write_text(
        (
            "def format_timezone():\n"
            "    return 'timezone schedule display'\n"
        ),
        encoding="utf-8",
    )

    tests = (
        tmp_path
        / "tests"
    )

    tests.mkdir()

    (
        tests
        / "test_formatter.py"
    ).write_text(
        (
            "def test_timezone_schedule_display():\n"
            "    assert True\n"
        ),
        encoding="utf-8",
    )

    index_repository(
        str(
            tmp_path
        ),
        repository=
            "source-preference-test",
    )

    paths = discover_candidate_paths(
        "source-preference-test",
        (
            "Fix timezone schedule display "
            "in the source code."
        ),
        max_candidates=2,
    )

    assert (
        paths[
            0
        ]
        == "assistant/formatter.py"
    )