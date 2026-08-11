"""
E.V.I.E. - Repository Graph Workspace Adapter

Phase 12D Retrieval Fix

Searches repository graph using query tokens and merges matching nodes.
"""

from __future__ import annotations

from assistant.workspace.controller import (
    new_evidence_id,
)
from assistant.workspace.models import (
    EvidenceItem,
    SOURCE_REPOSITORY,
)
from assistant.workspace.query_expansion import (
    significant_tokens,
)
from assistant.workspace.repository.controller import (
    get_repository_graph,
)
from assistant.workspace.repository.query import (
    find_nodes,
)

from .base import AdapterContext


class RepositoryGraphAdapter:
    name = "repository"

    def search(
        self,
        query: str,
        context: AdapterContext,
    ) -> list[EvidenceItem]:
        repository = (
            context.repository
            or context.arguments.get(
                "repository",
                ""
            )
        )

        if not repository:
            return []

        graph = get_repository_graph(
            repository
        )

        if graph is None:
            return []

        limit = int(
            context.arguments.get(
                "limit",
                50,
            )
            or 50
        )

        tokens = significant_tokens(
            query
        )

        candidates = []
        seen = set()

        search_terms = (
            tokens
            if tokens
            else [query]
        )

        for term in search_terms:
            for node in find_nodes(
                graph,
                term,
                limit=limit,
            ):
                if node.node_id in seen:
                    continue

                seen.add(
                    node.node_id
                )
                candidates.append(
                    node
                )

        results = []

        for node in candidates[
            :limit
        ]:
            content = (
                f"Repository node type: {node.node_type}\n"
                f"Name: {node.name}\n"
                f"Path: {node.path}\n"
                f"Module: {node.module}\n"
                f"Package: {node.package}"
            )

            overlap = sum(
                1
                for token in tokens
                if token in content.lower()
            )

            evidence_id = new_evidence_id(
                SOURCE_REPOSITORY,
                node.node_id,
                content,
            )

            results.append(
                EvidenceItem(
                    evidence_id=evidence_id,
                    source_type=SOURCE_REPOSITORY,
                    source_name="repository_graph",
                    source_id=node.node_id,
                    title=(
                        node.path
                        or node.name
                    ),
                    content=content,
                    repository=repository,
                    path=node.path,
                    relevance=float(
                        max(
                            1,
                            overlap,
                        )
                    ),
                    confidence=1.0,
                    metadata={
                        "node_id": node.node_id,
                        "node_type": node.node_type,
                        "module": node.module,
                        "package": node.package,
                    },
                )
            )

        return results
