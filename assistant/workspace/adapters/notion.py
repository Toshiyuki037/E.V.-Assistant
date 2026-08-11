"""
E.V.I.E. - Notion Workspace Adapter

Phase 12D - Source Enrichment

Search is used for discovery. When page titles can be extracted safely,
the adapter follows discovery with notion.read_document so synthesis can
use actual page contents rather than search metadata alone.
"""

from __future__ import annotations

from assistant.workspace.controller import new_evidence_id
from assistant.workspace.models import (
    EvidenceItem,
    SOURCE_NOTION,
)
from assistant.workspace.query_expansion import (
    expand_query,
)

from .base import AdapterContext
from .integration_common import (
    execute_integration,
    extract_evidence_data,
    stringify_payload,
)


TITLE_KEYS = {
    "title",
    "page_title",
}


def _collect_page_titles(
    value,
    *,
    limit: int = 5,
):
    """
    Extract likely page titles conservatively from structured Notion
    search payloads.
    """

    titles = []

    def visit(
        item,
    ):
        if len(
            titles
        ) >= limit:
            return

        if isinstance(
            item,
            dict,
        ):
            for key, child in item.items():
                lowered = str(
                    key
                ).lower()

                if (
                    lowered in TITLE_KEYS
                    and isinstance(
                        child,
                        str,
                    )
                    and child.strip()
                ):
                    title = child.strip()

                    if title not in titles:
                        titles.append(
                            title
                        )

                else:
                    visit(
                        child
                    )

        elif isinstance(
            item,
            list,
        ):
            for child in item:
                visit(
                    child
                )

                if len(
                    titles
                ) >= limit:
                    break

    visit(
        value
    )

    return titles[
        :limit
    ]


class NotionWorkspaceAdapter:
    name = "notion"

    def search(
        self,
        query: str,
        context: AdapterContext,
    ) -> list[EvidenceItem]:
        results = []
        seen_payloads = set()
        page_titles = []

        variants = expand_query(
            query
        )[
            :6
        ]

        account_id = context.arguments.get(
            "account_id",
            "primary",
        )

        for search_query in variants:
            execution = execute_integration(
                capability="notion.search",
                provider="notion",
                account_id=account_id,
                arguments={
                    "query": search_query,
                },
            )

            for item in extract_evidence_data(
                execution
            ):
                data = item.get(
                    "data"
                )

                content = stringify_payload(
                    data
                )

                if content not in seen_payloads:
                    seen_payloads.add(
                        content
                    )

                    evidence_id = new_evidence_id(
                        SOURCE_NOTION,
                        (
                            "notion.search:"
                            + search_query
                        ),
                        content,
                    )

                    results.append(
                        EvidenceItem(
                            evidence_id=evidence_id,
                            source_type=SOURCE_NOTION,
                            source_name="notion",
                            source_id=(
                                "notion.search:"
                                + search_query
                            ),
                            title=(
                                f"Notion search: "
                                f"{search_query}"
                            ),
                            content=content,
                            project=context.project,
                            repository=context.repository,
                            relevance=1.0,
                            confidence=1.0,
                            metadata={
                                "provider": "notion",
                                "account_id": account_id,
                                "search_query": search_query,
                                "raw": data,
                                "evidence_kind":
                                    "search_metadata",
                            },
                        )
                    )

                for title in _collect_page_titles(
                    data,
                    limit=5,
                ):
                    if (
                        title
                        not in page_titles
                    ):
                        page_titles.append(
                            title
                        )

        # Follow search discovery with actual document reads.
        for title in page_titles[
            :5
        ]:
            execution = execute_integration(
                capability="notion.read_document",
                provider="notion",
                account_id=account_id,
                arguments={
                    "page_title":
                        title,
                },
            )

            for item in extract_evidence_data(
                execution
            ):
                data = item.get(
                    "data"
                )

                content = stringify_payload(
                    data
                )

                if content in seen_payloads:
                    continue

                seen_payloads.add(
                    content
                )

                evidence_id = new_evidence_id(
                    SOURCE_NOTION,
                    (
                        "notion.read_document:"
                        + title
                    ),
                    content,
                )

                results.append(
                    EvidenceItem(
                        evidence_id=evidence_id,
                        source_type=SOURCE_NOTION,
                        source_name="notion",
                        source_id=(
                            "notion.read_document:"
                            + title
                        ),
                        title=title,
                        content=content,
                        project=context.project,
                        repository=context.repository,
                        relevance=3.0,
                        confidence=1.0,
                        metadata={
                            "provider": "notion",
                            "account_id": account_id,
                            "page_title": title,
                            "raw": data,
                            "evidence_kind":
                                "document_content",
                        },
                    )
                )

        return results
