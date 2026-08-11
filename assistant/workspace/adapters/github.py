"""
E.V.I.E. - GitHub Workspace Adapter

Phase 12D Retrieval Fix

Queries existing GitHub capabilities and uses token overlap rather than
requiring the full user question to appear verbatim in returned JSON.
"""

from __future__ import annotations

from assistant.workspace.controller import new_evidence_id
from assistant.workspace.models import (
    EvidenceItem,
    SOURCE_GITHUB,
)
from assistant.workspace.query_expansion import (
    significant_tokens,
)

from .base import AdapterContext
from .integration_common import (
    execute_integration,
    extract_evidence_data,
    stringify_payload,
)


class GitHubWorkspaceAdapter:
    name = "github"

    CAPABILITIES = (
        "github.commits",
        "github.issues",
        "github.pulls",
        "github.actions",
    )

    def search(
        self,
        query: str,
        context: AdapterContext,
    ) -> list[EvidenceItem]:
        repo = (
            context.repository
            or context.arguments.get(
                "repo",
                "",
            )
        )

        if not repo:
            return []

        tokens = significant_tokens(
            query
        )

        results = []

        for capability in self.CAPABILITIES:
            execution = execute_integration(
                capability=capability,
                provider="github",
                account_id=context.arguments.get(
                    "account_id",
                    "primary",
                ),
                arguments={
                    "repo": repo,
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

                lowered = content.lower()

                overlap = sum(
                    1
                    for token in tokens
                    if token in lowered
                )

                if tokens and overlap == 0:
                    continue

                evidence_id = new_evidence_id(
                    SOURCE_GITHUB,
                    f"{repo}:{capability}",
                    content,
                )

                results.append(
                    EvidenceItem(
                        evidence_id=evidence_id,
                        source_type=SOURCE_GITHUB,
                        source_name="github",
                        source_id=capability,
                        title=(
                            f"{repo} "
                            f"{capability}"
                        ),
                        content=content,
                        repository=repo,
                        relevance=float(
                            max(
                                1,
                                overlap,
                            )
                        ),
                        confidence=1.0,
                        metadata={
                            "capability": capability,
                            "provider": "github",
                            "account_id": item.get(
                                "account_id",
                                "primary",
                            ),
                            "raw": data,
                            "token_overlap": overlap,
                        },
                    )
                )

        return results
