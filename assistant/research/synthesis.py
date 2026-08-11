"""
E.V.I.E. - Research Project Synthesis

Phase 12G

Purpose:
Reason over structured research state plus unified workspace evidence.

The reasoning model is lazy-loaded only when synthesis is requested.
Every substantive research claim must cite provided workspace evidence
IDs when evidence exists.
"""

from __future__ import annotations

import json

from pydantic import (
    BaseModel,
    Field,
)

from assistant.workspace.evidence import (
    load_evidence,
)

from .controller import (
    get_project,
)

from .state import (
    load,
)


SYSTEM_PROMPT = """
You are E.V.I.E.'s research copilot.

You are given:
1. structured research state for one project;
2. source-backed workspace evidence already linked to that project.

Your job is to explain the current research state rigorously.

Rules:
- Do not invent experiments, results, papers, or evidence.
- Distinguish established findings from hypotheses and open questions.
- Every evidence-backed substantive claim must include valid evidence IDs.
- If evidence is weak or incomplete, say so.
- Identify unresolved questions and useful next research steps.
- Prefer project-specific reasoning over generic research advice.
"""


class ResearchClaim(
    BaseModel
):
    text: str

    evidence_ids: list[str] = Field(
        default_factory=list
    )

    confidence: float = 0.0


class ResearchProjectSynthesis(
    BaseModel
):
    summary: str

    strongest_findings: list[str] = Field(
        default_factory=list
    )

    unresolved_questions: list[str] = Field(
        default_factory=list
    )

    next_steps: list[str] = Field(
        default_factory=list
    )

    claims: list[ResearchClaim] = Field(
        default_factory=list
    )

    confidence: float = 0.0


def _client():
    from assistant.brain import (
        client,
    )

    return client


def _record_payload(
    kind: str,
    identifiers: list[str],
):
    results = []

    for ident in identifiers:
        item = load(
            kind,
            ident,
        )

        if item is None:
            continue

        results.append(
            vars(
                item
            )
        )

    return results


def build_research_context(
    project_id: str,
):
    project = get_project(
        project_id
    )

    if project is None:
        raise ValueError(
            (
                "Research project does not exist: "
                f"{project_id}"
            )
        )

    evidence = []

    for evidence_id in project.evidence_ids:
        item = load_evidence(
            evidence_id
        )

        if item is None:
            continue

        evidence.append(
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
                "content":
                    item.content[
                        :12000
                    ],
            }
        )

    return {
        "project":
            vars(
                project
            ),

        "papers":
            _record_payload(
                "papers",
                project.paper_ids,
            ),

        "hypotheses":
            _record_payload(
                "hypotheses",
                project.hypothesis_ids,
            ),

        "experiments":
            _record_payload(
                "experiments",
                project.experiment_ids,
            ),

        "results":
            _record_payload(
                "results",
                project.result_ids,
            ),

        "decisions":
            _record_payload(
                "decisions",
                project.decision_ids,
            ),

        "timeline":
            _record_payload(
                "timeline",
                project.timeline_event_ids,
            ),

        "evidence":
            evidence,
    }


def synthesize_research_project(
    project_id: str,
):
    context = build_research_context(
        project_id
    )

    client = _client()

    response = client.responses.parse(
        model="gpt-5.2",
        instructions=SYSTEM_PROMPT,
        input=(
            "RESEARCH PROJECT STATE:\n"
            + json.dumps(
                context,
                indent=2,
                ensure_ascii=False,
                default=str,
            )
        ),
        text_format=ResearchProjectSynthesis,
    )

    parsed = response.output_parsed

    valid_ids = {
        item[
            "evidence_id"
        ]
        for item in context[
            "evidence"
        ]
    }

    for claim in parsed.claims:
        claim.evidence_ids = [
            evidence_id
            for evidence_id
            in claim.evidence_ids
            if evidence_id
            in valid_ids
        ]

    return parsed
