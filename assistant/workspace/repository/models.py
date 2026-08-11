"""
E.V.I.E. - Repository Graph Models

Phase 12C
"""

from __future__ import annotations

from dataclasses import (
    asdict,
    dataclass,
    field,
)

from typing import Any


NODE_REPOSITORY = "repository"
NODE_PACKAGE = "package"
NODE_MODULE = "module"
NODE_FILE = "file"
NODE_CLASS = "class"
NODE_FUNCTION = "function"
NODE_TEST = "test"

EDGE_CONTAINS = "contains"
EDGE_IMPORTS = "imports"
EDGE_DEFINES = "defines"
EDGE_TESTS = "tests"


@dataclass
class RepositoryNode:
    node_id: str
    node_type: str
    name: str
    path: str = ""
    module: str = ""
    package: str = ""
    language: str = ""
    metadata: dict[str, Any] = field(
        default_factory=dict
    )


@dataclass
class RepositoryEdge:
    edge_id: str
    source_node_id: str
    target_node_id: str
    edge_type: str
    metadata: dict[str, Any] = field(
        default_factory=dict
    )


@dataclass
class RepositoryGraph:
    repository: str
    root_path: str
    nodes: list[RepositoryNode] = field(
        default_factory=list
    )
    edges: list[RepositoryEdge] = field(
        default_factory=list
    )
    metadata: dict[str, Any] = field(
        default_factory=dict
    )


def node_to_dict(
    node: RepositoryNode,
):
    return asdict(
        node
    )


def edge_to_dict(
    edge: RepositoryEdge,
):
    return asdict(
        edge
    )


def graph_to_dict(
    graph: RepositoryGraph,
):
    return asdict(
        graph
    )
