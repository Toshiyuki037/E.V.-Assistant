"""
E.V.I.E. - Repository Graph Builder

Phase 12C - Import Graph Fix

Builds repository structure plus robust local import relationships.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from .models import (
    EDGE_CONTAINS,
    EDGE_DEFINES,
    EDGE_IMPORTS,
    EDGE_TESTS,
    NODE_CLASS,
    NODE_FILE,
    NODE_FUNCTION,
    NODE_REPOSITORY,
    NODE_TEST,
    RepositoryEdge,
    RepositoryGraph,
    RepositoryNode,
)
from .parser import parse_python_file


DEFAULT_IGNORES = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    "node_modules",
    "runtime",
}


def _hash(*parts):
    value = "\x1f".join(
        str(part or "")
        for part in parts
    )
    return hashlib.sha256(
        value.encode("utf-8")
    ).hexdigest()[:16]


def node_id(
    node_type: str,
    repository: str,
    key: str,
):
    return (
        f"repo-node:{node_type}:"
        + _hash(repository, key)
    )


def edge_id(
    source: str,
    target: str,
    edge_type: str,
):
    return (
        "repo-edge:"
        + _hash(source, target, edge_type)
    )


def _iter_python_files(root: Path):
    for path in root.rglob("*.py"):
        if not path.is_file():
            continue

        if any(
            part in DEFAULT_IGNORES
            for part in path.parts
        ):
            continue

        yield path


def _current_package(current_module: str):
    if not current_module:
        return []

    parts = current_module.split(".")
    return parts[:-1]


def _resolve_from_base(
    current_module: str,
    level: int,
    module: str,
):
    if level <= 0:
        return module

    package_parts = _current_package(
        current_module
    )

    # Python level=1 means current package.
    up = max(
        0,
        level - 1,
    )

    if up:
        if up >= len(package_parts):
            package_parts = []
        else:
            package_parts = package_parts[:-up]

    if module:
        package_parts.extend(
            module.split(".")
        )

    return ".".join(
        part
        for part in package_parts
        if part
    )


def _candidate_modules(
    current_module: str,
    import_spec: dict,
):
    kind = import_spec.get(
        "kind",
        ""
    )

    module = import_spec.get(
        "module",
        ""
    )

    level = int(
        import_spec.get(
            "level",
            0,
        )
        or 0
    )

    names = (
        import_spec.get(
            "names",
            []
        )
        or []
    )

    if kind == "import":
        if module:
            yield module
        return

    base = _resolve_from_base(
        current_module,
        level,
        module,
    )

    # `from x.y import z` always at least references x.y.
    if base:
        yield base

    # If the imported symbol is itself a local module, also connect it.
    # This fixes:
    #   from assistant import brain
    #   from . import controller
    for name in names:
        if name == "*":
            continue

        if base:
            yield f"{base}.{name}"
        else:
            resolved = _resolve_from_base(
                current_module,
                level,
                name,
            )
            if resolved:
                yield resolved


def _nearest_local_module(
    module_nodes: dict,
    candidate: str,
):
    current = candidate

    while current:
        target = module_nodes.get(
            current
        )

        if target is not None:
            return target

        if "." not in current:
            break

        current = current.rsplit(
            ".",
            1,
        )[0]

    return None


def build_repository_graph(
    root_path: str,
    *,
    repository: str,
):
    root = Path(
        root_path
    ).resolve()

    graph = RepositoryGraph(
        repository=repository,
        root_path=str(root),
    )

    repo_node = RepositoryNode(
        node_id=node_id(
            NODE_REPOSITORY,
            repository,
            repository,
        ),
        node_type=NODE_REPOSITORY,
        name=repository,
        path="",
        language="mixed",
    )

    graph.nodes.append(
        repo_node
    )

    parsed_files = [
        parse_python_file(
            path,
            root=root,
        )
        for path in _iter_python_files(root)
    ]

    module_nodes = {}
    path_node_map = {}

    for parsed in parsed_files:
        relative = parsed["path"]
        module = parsed["module"]

        is_test = (
            relative.startswith("tests/")
            or Path(relative).name.startswith("test_")
        )

        file_node = RepositoryNode(
            node_id=node_id(
                NODE_TEST if is_test else NODE_FILE,
                repository,
                relative,
            ),
            node_type=(
                NODE_TEST
                if is_test
                else NODE_FILE
            ),
            name=Path(relative).name,
            path=relative,
            module=module,
            package=(
                module.rsplit(".", 1)[0]
                if "." in module
                else ""
            ),
            language="python",
            metadata={
                "syntax_error":
                    parsed["syntax_error"],
            },
        )

        graph.nodes.append(
            file_node
        )
        path_node_map[
            relative
        ] = file_node

        if module:
            module_nodes[
                module
            ] = file_node

        graph.edges.append(
            RepositoryEdge(
                edge_id=edge_id(
                    repo_node.node_id,
                    file_node.node_id,
                    EDGE_CONTAINS,
                ),
                source_node_id=repo_node.node_id,
                target_node_id=file_node.node_id,
                edge_type=EDGE_CONTAINS,
            )
        )

        for item in parsed["classes"]:
            child = RepositoryNode(
                node_id=node_id(
                    NODE_CLASS,
                    repository,
                    (
                        f"{relative}:class:"
                        f"{item['name']}:{item['lineno']}"
                    ),
                ),
                node_type=NODE_CLASS,
                name=item["name"],
                path=relative,
                module=module,
                language="python",
                metadata={
                    "lineno": item["lineno"]
                },
            )

            graph.nodes.append(
                child
            )
            graph.edges.append(
                RepositoryEdge(
                    edge_id=edge_id(
                        file_node.node_id,
                        child.node_id,
                        EDGE_DEFINES,
                    ),
                    source_node_id=file_node.node_id,
                    target_node_id=child.node_id,
                    edge_type=EDGE_DEFINES,
                )
            )

        for item in parsed["functions"]:
            child = RepositoryNode(
                node_id=node_id(
                    NODE_FUNCTION,
                    repository,
                    (
                        f"{relative}:function:"
                        f"{item['name']}:{item['lineno']}"
                    ),
                ),
                node_type=NODE_FUNCTION,
                name=item["name"],
                path=relative,
                module=module,
                language="python",
                metadata={
                    "lineno": item["lineno"],
                    "async": item["async"],
                },
            )

            graph.nodes.append(
                child
            )
            graph.edges.append(
                RepositoryEdge(
                    edge_id=edge_id(
                        file_node.node_id,
                        child.node_id,
                        EDGE_DEFINES,
                    ),
                    source_node_id=file_node.node_id,
                    target_node_id=child.node_id,
                    edge_type=EDGE_DEFINES,
                )
            )

    # -----------------------------------------------------------------------
    # Import edges
    # -----------------------------------------------------------------------

    seen_import_edges = set()

    for parsed in parsed_files:
        source_node = path_node_map.get(
            parsed["path"]
        )

        if source_node is None:
            continue

        for import_spec in parsed["imports"]:
            for candidate in _candidate_modules(
                parsed["module"],
                import_spec,
            ):
                target = _nearest_local_module(
                    module_nodes,
                    candidate,
                )

                if target is None:
                    continue

                if (
                    target.node_id
                    == source_node.node_id
                ):
                    continue

                key = (
                    source_node.node_id,
                    target.node_id,
                    EDGE_IMPORTS,
                )

                if key in seen_import_edges:
                    continue

                seen_import_edges.add(
                    key
                )

                graph.edges.append(
                    RepositoryEdge(
                        edge_id=edge_id(
                            source_node.node_id,
                            target.node_id,
                            EDGE_IMPORTS,
                        ),
                        source_node_id=source_node.node_id,
                        target_node_id=target.node_id,
                        edge_type=EDGE_IMPORTS,
                        metadata={
                            "candidate":
                                candidate,
                            "import_spec":
                                import_spec,
                        },
                    )
                )

    # -----------------------------------------------------------------------
    # Filename-based test links
    # -----------------------------------------------------------------------

    normal_nodes = [
        node
        for node in graph.nodes
        if node.node_type == NODE_FILE
    ]

    test_nodes = [
        node
        for node in graph.nodes
        if node.node_type == NODE_TEST
    ]

    for test_node in test_nodes:
        stem = Path(
            test_node.path
        ).stem

        target_stem = (
            stem[5:]
            if stem.startswith("test_")
            else ""
        )

        if not target_stem:
            continue

        for target in normal_nodes:
            if (
                Path(target.path).stem
                == target_stem
            ):
                graph.edges.append(
                    RepositoryEdge(
                        edge_id=edge_id(
                            test_node.node_id,
                            target.node_id,
                            EDGE_TESTS,
                        ),
                        source_node_id=test_node.node_id,
                        target_node_id=target.node_id,
                        edge_type=EDGE_TESTS,
                    )
                )

    graph.metadata = {
        "python_files": len(
            parsed_files
        ),
        "node_count": len(
            graph.nodes
        ),
        "edge_count": len(
            graph.edges
        ),
        "import_edge_count": sum(
            1
            for edge in graph.edges
            if edge.edge_type == EDGE_IMPORTS
        ),
    }

    return graph
