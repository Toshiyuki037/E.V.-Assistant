"""
Phase 12H file-node resolution regression.

The repository graph gives function/class nodes the same path as their
containing file. Impact analysis must select the module-level file node.
"""

import assistant.workspace.repository.store as repo_store

from assistant.workspace.repository.controller import (
    index_repository,
)

from assistant.coding.impact import (
    analyze_file_impact,
)


def test_file_path_resolves_module_node_not_function(
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
        / "integration.py"
    ).write_text(
        (
            "def handle():\n"
            "    return True\n"
        ),
        encoding="utf-8",
    )

    (
        package
        / "main.py"
    ).write_text(
        (
            "from .integration import handle\n"
            "handle()\n"
        ),
        encoding="utf-8",
    )

    index_repository(
        str(
            tmp_path
        ),
        repository=
            "file-node-test",
    )

    analysis = (
        analyze_file_impact(
            "file-node-test",
            "assistant/integration.py",
        )
    )

    assert (
        analysis[
            "target"
        ].node_type
        == "file"
    )

    assert any(
        node.path
        == "assistant/main.py"
        for node
        in analysis[
            "direct_importers"
        ]
    )

    assert (
        analysis[
            "impact_count"
        ]
        >= 1
    )
