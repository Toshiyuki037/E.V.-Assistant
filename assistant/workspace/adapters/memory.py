"""
E.V.I.E. - Memory Workspace Adapter

Phase 12E

Bridges the existing Phase 2 semantic memory system into the unified
Phase 12 evidence workspace.
"""

from __future__ import annotations

from assistant.workspace.controller import (
    new_evidence_id,
)
from assistant.workspace.models import (
    EvidenceItem,
    SOURCE_MEMORY,
)

from .base import AdapterContext
from .bridge import (
    call_first_available,
    extract_text,
    flatten_records,
    stringify,
)


class MemoryWorkspaceAdapter:
    name = "memory"

    FUNCTIONS = [
        "retrieve_memories",
        "search_memories",
        "retrieve_relevant_memories",
        "get_relevant_memories",
        "semantic_search",
        "search_memory",
    ]

    MODULES = [
        "assistant.memory.retriever",
        "assistant.memory.manager",
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

        records = flatten_records(
            raw
        )

        results = []

        for index, record in enumerate(
            records,
            start=1,
        ):
            content = extract_text(
                record
            )

            source_id = (
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
            ) or f"memory:{index}"

            evidence_id = new_evidence_id(
                SOURCE_MEMORY,
                source_id,
                content,
            )

            results.append(
                EvidenceItem(
                    evidence_id=evidence_id,
                    source_type=SOURCE_MEMORY,
                    source_name="evie_memory",
                    source_id=source_id,
                    title=(
                        (
                            record.get(
                                "category"
                            )
                            or record.get(
                                "title"
                            )
                            or "Memory"
                        )
                        if isinstance(
                            record,
                            dict,
                        )
                        else "Memory"
                    ),
                    content=content,
                    project=context.project,
                    repository=context.repository,
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
                    confidence=float(
                        (
                            record.get(
                                "confidence",
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
                    metadata={
                        "raw": record,
                    },
                )
            )

        return results
