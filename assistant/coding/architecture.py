"""
E.V.I.E. - Repository Architecture Summary

Phase 12H
"""

from collections import Counter

from assistant.workspace.repository.controller import get_repository_graph
from assistant.workspace.repository.models import EDGE_IMPORTS, NODE_FILE, NODE_TEST


def summarize_repository_architecture(repository):
    graph = get_repository_graph(repository)
    if graph is None:
        raise RuntimeError(f"Repository graph does not exist: {repository}")

    package_counts = Counter()
    file_count = 0
    test_count = 0

    for node in graph.nodes:
        if node.node_type == NODE_FILE:
            file_count += 1
            package_counts[node.package or "(root)"] += 1
        elif node.node_type == NODE_TEST:
            test_count += 1

    import_edges = [
        edge
        for edge in graph.edges
        if edge.edge_type == EDGE_IMPORTS
    ]

    importers = Counter(
        edge.target_node_id
        for edge in import_edges
    )

    node_map = {
        node.node_id: node
        for node in graph.nodes
    }

    central_modules = []
    for node_id, count in importers.most_common(20):
        node = node_map.get(node_id)
        if node is None:
            continue
        central_modules.append(
            {
                "path": node.path,
                "module": node.module,
                "imported_by_count": count,
            }
        )

    return {
        "repository": repository,
        "root_path": graph.root_path,
        "python_files": graph.metadata.get("python_files", file_count),
        "source_files": file_count,
        "test_files": test_count,
        "import_edges": len(import_edges),
        "packages": dict(package_counts.most_common()),
        "central_modules": central_modules,
    }
