"""
E.V.I.E. - Existing Knowledge Index Adapter

Phase 12E

Bridges the Phase 4 project/file knowledge system into the unified
workspace model.
"""

from __future__ import annotations

from assistant.workspace.controller import (
    new_evidence_id,
)
from assistant.workspace.models import (
    EvidenceItem,
    SOURCE_KNOWLEDGE,
)

from .base import AdapterContext
from .bridge import (
    call_first_available,
    extract_text,
    flatten_records,
)


class KnowledgeWorkspaceAdapter:
    name = "knowledge"

    MODULES = [
        "assistant.knowledge.retriever",
        "assistant.knowledge.search",
        "assistant.knowledge.indexer",
    ]

    FUNCTIONS = [
        "search_knowledge",
        "search",
        "retrieve",
        "retrieve_knowledge",
        "semantic_search",
        "query_knowledge",
    ]

    def search(
        self,
        query: str,
        context: AdapterContext,
    ) -> list[EvidenceItem]:
        raw = None

        for module_name in self.MODULES:
            raw = call_first_available(
                module_name,
                self.FUNCTIONS,
                query,
                limit=int(
                    context.arguments.get(
                        "limit",
                        20,
                    )
                    or 20
                ),
            )

            if raw is not None:
                break

        results = []

        for index, record in enumerate(
            flatten_records(
                raw
            ),
            start=1,
        ):
            content = extract_text(
                record
            )

            path = (
                str(
                    record.get(
                        "path",
                        "",
                    )
                    or record.get(
                        "file_path",
                        "",
                    )
                )
                if isinstance(
                    record,
                    dict,
                )
                else ""
            )

            source_id = (
                path
                or (
                    str(
                        record.get(
                            "id",
                            "",
                        )
                    )
                    if isinstance(
                        record,
                        dict,
                    )
                    else ""
                )
                or f"knowledge:{index}"
            )

            results.append(
                EvidenceItem(
                    evidence_id=new_evidence_id(
                        SOURCE_KNOWLEDGE,
                        source_id,
                        content,
                    ),
                    source_type=SOURCE_KNOWLEDGE,
                    source_name="phase4_knowledge",
                    source_id=source_id,
                    title=(
                        (
                            record.get(
                                "title"
                            )
                            or record.get(
                                "filename"
                            )
                            or path
                            or "Knowledge"
                        )
                        if isinstance(
                            record,
                            dict,
                        )
                        else "Knowledge"
                    ),
                    content=content,
                    project=context.project,
                    repository=context.repository,
                    path=path,
                    relevance=float(
                        (
                            record.get(
                                "score",
                                1.0,
                            )
                            if isinstance(
                                record,
                                dict,
                            )
                            else 1.0
                        )
                        or 1.0
                    ),
                    confidence=1.0,
                    metadata={
                        "raw": record,
                    },
                )
            )

        return results
