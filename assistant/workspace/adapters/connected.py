"""
E.V.I.E. - Connected Workspace Adapter

Phase 12E

Generic bridge for connected services already exposed through
integration_execute. Capability names are supplied by adapter context so
this layer does not invent or hard-code unsupported Gmail/Calendar APIs.

Example context arguments:
    {
        "capability": "gmail.search",
        "provider": "google",
        "account_id": "primary",
        "arguments": {"query": "..."}
    }
"""

from __future__ import annotations

from assistant.workspace.controller import (
    new_evidence_id,
)
from assistant.workspace.models import (
    EvidenceItem,
)

from .base import AdapterContext
from .integration_common import (
    execute_integration,
    extract_evidence_data,
    stringify_payload,
)


class ConnectedWorkspaceAdapter:
    name = "connected"

    def search(
        self,
        query: str,
        context: AdapterContext,
    ) -> list[EvidenceItem]:
        capability = (
            context.arguments.get(
                "capability"
            )
            or ""
        )

        provider = (
            context.arguments.get(
                "provider"
            )
            or ""
        )

        if not capability or not provider:
            return []

        arguments = dict(
            context.arguments.get(
                "arguments",
                {}
            )
            or {}
        )

        query_key = (
            context.arguments.get(
                "query_key",
                "query",
            )
        )

        if (
            query_key
            and query_key
            not in arguments
        ):
            arguments[
                query_key
            ] = query

        execution = execute_integration(
            capability=capability,
            provider=provider,
            account_id=context.arguments.get(
                "account_id",
                "primary",
            ),
            arguments=arguments,
        )

        source_type = (
            context.arguments.get(
                "source_type"
            )
            or provider
        )

        results = []

        for index, item in enumerate(
            extract_evidence_data(
                execution
            ),
            start=1,
        ):
            data = item.get(
                "data"
            )

            content = stringify_payload(
                data
            )

            source_id = (
                f"{capability}:{index}"
            )

            results.append(
                EvidenceItem(
                    evidence_id=new_evidence_id(
                        source_type,
                        source_id,
                        content,
                    ),
                    source_type=source_type,
                    source_name=provider,
                    source_id=source_id,
                    title=(
                        f"{provider} {capability}"
                    ),
                    content=content,
                    project=context.project,
                    repository=context.repository,
                    relevance=1.0,
                    confidence=1.0,
                    metadata={
                        "provider":
                            provider,
                        "capability":
                            capability,
                        "raw":
                            data,
                    },
                )
            )

        return results
