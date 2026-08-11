"""
E.V.I.E. - Source-Backed Workspace Synthesis

Phase 12D

Uses the existing E.V.I.E. reasoning client lazily so repository indexing
and workspace search remain lightweight when synthesis is not requested.
"""

from __future__ import annotations

import json

from pydantic import (
    BaseModel,
    Field,
)

from assistant.workspace.models import (
    WorkspaceClaim,
)

from assistant.workspace.provenance import (
    build_claim,
)


SYSTEM_PROMPT = """
You are E.V.I.E.'s unified workspace reasoning layer.

Answer only from the evidence supplied to you.

You must:
- combine relevant information across sources
- distinguish facts from uncertainty
- never invent a source
- attach evidence IDs to every substantive claim
- prefer multiple supporting sources when available
- explain source disagreement if present
- stay focused on the user's actual question

Return a concise but technically useful answer plus claims.
"""


class SynthesizedClaim(
    BaseModel
):
    text: str

    evidence_ids: list[str] = Field(
        default_factory=list
    )

    confidence: float = 0.0


class WorkspaceSynthesis(
    BaseModel
):
    answer: str

    claims: list[SynthesizedClaim] = Field(
        default_factory=list
    )

    confidence: float = 0.0


def _get_client():
    from assistant.brain import (
        client,
    )

    return client


def synthesize_workspace_result(
    result,
):
    if not result.evidence:
        result.answer = (
            "I could not find workspace evidence "
            "for that question."
        )
        result.confidence = 0.0
        return result

    evidence_payload = []

    for item in result.evidence:
        evidence_payload.append(
            {
                "evidence_id":
                    item.evidence_id,
                "source_type":
                    item.source_type,
                "source_name":
                    item.source_name,
                "title":
                    item.title,
                "path":
                    item.path,
                "repository":
                    item.repository,
                "content":
                    item.content[
                        :12000
                    ],
            }
        )

    prompt = (
        "QUESTION:\n"
        f"{result.query}\n\n"
        "EVIDENCE:\n"
        + json.dumps(
            evidence_payload,
            indent=2,
            ensure_ascii=False,
            default=str,
        )
    )

    client = _get_client()

    response = client.responses.parse(
        model="gpt-5.2",
        instructions=SYSTEM_PROMPT,
        input=prompt,
        text_format=WorkspaceSynthesis,
    )

    parsed = response.output_parsed

    result.answer = (
        parsed.answer
        or ""
    )

    result.confidence = float(
        parsed.confidence
        or 0.0
    )

    valid_ids = {
        item.evidence_id
        for item in result.evidence
    }

    claims = []

    for index, claim in enumerate(
        parsed.claims,
        start=1,
    ):
        evidence_ids = [
            evidence_id
            for evidence_id
            in claim.evidence_ids
            if evidence_id
            in valid_ids
        ]

        claims.append(
            build_claim(
                claim_id=(
                    f"claim:{index}"
                ),
                text=claim.text,
                evidence_ids=evidence_ids,
                confidence=claim.confidence,
            )
        )

    result.claims = claims

    return result
