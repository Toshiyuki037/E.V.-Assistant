"""
Phase 12B source adapter tests.
"""

from pathlib import Path

from assistant.workspace.adapters.base import AdapterContext
from assistant.workspace.adapters.local import LocalWorkspaceAdapter
from assistant.workspace.adapters.registry import (
    load_default_adapters,
)


def test_default_adapter_registry():
    adapters = load_default_adapters()

    assert "local" in adapters
    assert "github" in adapters
    assert "notion" in adapters


def test_local_adapter_finds_matching_code(
    tmp_path,
):
    project = (
        tmp_path
        / "assistant"
    )

    project.mkdir()

    target = (
        project
        / "engine.py"
    )

    target.write_text(
        (
            "def run_workflow_engine():\n"
            "    return 'phase12-adapter-test'\n"
        ),
        encoding="utf-8",
    )

    adapter = LocalWorkspaceAdapter()

    results = adapter.search(
        "phase12-adapter-test",
        AdapterContext(
            repository="E.V.-Assistant",
            workspace_path=str(
                tmp_path
            ),
        ),
    )

    assert len(results) == 1
    assert results[0].path == "assistant/engine.py"
    assert results[0].repository == "E.V.-Assistant"


def test_local_adapter_ignores_venv(
    tmp_path,
):
    venv = (
        tmp_path
        / "venv"
    )

    venv.mkdir()

    (
        venv
        / "ignored.py"
    ).write_text(
        "UNIQUE_IGNORED_VALUE",
        encoding="utf-8",
    )

    adapter = LocalWorkspaceAdapter()

    results = adapter.search(
        "UNIQUE_IGNORED_VALUE",
        AdapterContext(
            workspace_path=str(
                tmp_path
            ),
        ),
    )

    assert results == []
