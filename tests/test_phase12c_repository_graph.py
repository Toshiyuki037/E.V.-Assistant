"""
Phase 12C repository graph tests.
"""

from assistant.workspace.repository.graph import (
    build_repository_graph,
)

from assistant.workspace.repository.models import (
    EDGE_IMPORTS,
    NODE_FILE,
    NODE_FUNCTION,
)


def test_repository_graph_builds_import_edges(
    tmp_path,
):
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
        / "a.py"
    ).write_text(
        (
            "from assistant import b\n\n"
            "def alpha():\n"
            "    return b.beta()\n"
        ),
        encoding="utf-8",
    )

    (
        package
        / "b.py"
    ).write_text(
        (
            "def beta():\n"
            "    return 1\n"
        ),
        encoding="utf-8",
    )

    graph = build_repository_graph(
        str(
            tmp_path
        ),
        repository="test",
    )

    files = [
        node
        for node
        in graph.nodes
        if node.node_type
        == NODE_FILE
    ]

    functions = [
        node
        for node
        in graph.nodes
        if node.node_type
        == NODE_FUNCTION
    ]

    import_edges = [
        edge
        for edge
        in graph.edges
        if edge.edge_type
        == EDGE_IMPORTS
    ]

    assert len(files) >= 2
    assert any(
        node.name == "alpha"
        for node
        in functions
    )
    assert len(import_edges) >= 1


def test_repository_graph_records_syntax_error(
    tmp_path,
):
    (
        tmp_path
        / "broken.py"
    ).write_text(
        "def broken(:\n",
        encoding="utf-8",
    )

    graph = build_repository_graph(
        str(
            tmp_path
        ),
        repository="test",
    )

    broken = next(
        node
        for node
        in graph.nodes
        if node.path
        == "broken.py"
    )

    assert broken.metadata[
        "syntax_error"
    ]
