"""
Phase 12C import graph regression tests.
"""

from assistant.workspace.repository.graph import (
    build_repository_graph,
)
from assistant.workspace.repository.models import (
    EDGE_IMPORTS,
)


def _import_targets(
    graph,
    source_path,
):
    nodes = {
        node.node_id: node
        for node in graph.nodes
    }

    source = next(
        node
        for node in graph.nodes
        if node.path == source_path
    )

    return {
        nodes[
            edge.target_node_id
        ].path
        for edge in graph.edges
        if (
            edge.edge_type == EDGE_IMPORTS
            and edge.source_node_id
            == source.node_id
        )
    }


def test_resolves_from_dot_module_import(
    tmp_path,
):
    package = tmp_path / "assistant"
    package.mkdir()

    (package / "__init__.py").write_text(
        "",
        encoding="utf-8",
    )
    (package / "brain.py").write_text(
        "x = 1\n",
        encoding="utf-8",
    )
    (package / "main.py").write_text(
        "from .brain import x\n",
        encoding="utf-8",
    )

    graph = build_repository_graph(
        str(tmp_path),
        repository="test",
    )

    assert (
        "assistant/brain.py"
        in _import_targets(
            graph,
            "assistant/main.py",
        )
    )


def test_resolves_from_dot_import_module(
    tmp_path,
):
    package = tmp_path / "assistant"
    package.mkdir()

    (package / "__init__.py").write_text(
        "",
        encoding="utf-8",
    )
    (package / "brain.py").write_text(
        "x = 1\n",
        encoding="utf-8",
    )
    (package / "main.py").write_text(
        "from . import brain\n",
        encoding="utf-8",
    )

    graph = build_repository_graph(
        str(tmp_path),
        repository="test",
    )

    assert (
        "assistant/brain.py"
        in _import_targets(
            graph,
            "assistant/main.py",
        )
    )


def test_resolves_from_package_import_module(
    tmp_path,
):
    package = tmp_path / "assistant"
    package.mkdir()

    (package / "__init__.py").write_text(
        "",
        encoding="utf-8",
    )
    (package / "brain.py").write_text(
        "x = 1\n",
        encoding="utf-8",
    )
    (package / "main.py").write_text(
        "from assistant import brain\n",
        encoding="utf-8",
    )

    graph = build_repository_graph(
        str(tmp_path),
        repository="test",
    )

    assert (
        "assistant/brain.py"
        in _import_targets(
            graph,
            "assistant/main.py",
        )
    )
