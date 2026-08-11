"""
E.V.I.E. - Workspace Provenance

Phase 12D

Purpose:
Track which normalized evidence items support each synthesized claim.
"""

from __future__ import annotations

from assistant.workspace.models import (
    WorkspaceClaim,
)


def build_claim(
    *,
    claim_id: str,
    text: str,
    evidence_ids: list[str],
    confidence: float = 0.0,
    entity_ids: list[str] | None = None,
    metadata: dict | None = None,
):
    return WorkspaceClaim(
        claim_id=claim_id,
        text=text,
        evidence_ids=list(
            evidence_ids
        ),
        confidence=float(
            confidence
            or 0.0
        ),
        entity_ids=list(
            entity_ids
            or []
        ),
        metadata=(
            metadata
            if isinstance(
                metadata,
                dict,
            )
            else {}
        ),
    )


def claim_sources(
    claim: WorkspaceClaim,
    evidence_by_id: dict,
):
    return [
        evidence_by_id[
            evidence_id
        ]
        for evidence_id
        in claim.evidence_ids
        if evidence_id
        in evidence_by_id
    ]
