"""
E.V.I.E. - Research Evidence Ingestion

Phase 12G

Purpose:
Connect the structured Phase 12F research model to the Phase 12 unified
workspace. Research projects can now collect cross-source evidence,
persist it, and attach that evidence to hypotheses and project history.

This module does not bypass any existing integration/tool permissions.
It only consumes evidence returned by the unified workspace layer.
"""

from __future__ import annotations

from pathlib import Path

from assistant.workspace.evidence import (
    save_evidence,
)

from assistant.workspace.query_controller import (
    query_workspace,
)

from .controller import (
    add_paper,
    add_timeline_event,
    get_project,
    link_evidence,
)

from .state import (
    save,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _require_project(
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

    return project


def _project_query(
    project,
    query: str | None,
):
    if query and query.strip():
        return query.strip()

    parts = [
        project.name,
        project.goal,
        project.description,
    ]

    return " ".join(
        part
        for part in parts
        if part
    )


# ---------------------------------------------------------------------------
# Cross-Source Evidence Collection
# ---------------------------------------------------------------------------

def collect_project_evidence(
    project_id: str,
    *,
    query: str | None = None,
    sources: list[str] | None = None,
    limit: int = 40,
    minimum_per_source: int = 2,
    workspace_path: str | None = None,
    adapter_arguments: dict | None = None,
    add_timeline: bool = True,
):
    """
    Search the unified workspace for evidence relevant to one research
    project, persist the evidence, and link it to the project.

    Returns the WorkspaceResult with synthesis disabled.
    """

    project = _require_project(
        project_id
    )

    resolved_query = _project_query(
        project,
        query,
    )

    resolved_workspace = (
        workspace_path
        or project.workspace_path
        or "."
    )

    result = query_workspace(
        resolved_query,
        project=project.project_id,
        repository=project.repository,
        workspace_path=resolved_workspace,
        sources=sources,
        limit=limit,
        synthesize=False,
        minimum_per_source=minimum_per_source,
        adapter_arguments=adapter_arguments,
    )

    added_ids = []

    for item in result.evidence:
        save_evidence(
            item
        )

        if (
            item.evidence_id
            not in project.evidence_ids
        ):
            project.evidence_ids.append(
                item.evidence_id
            )
            added_ids.append(
                item.evidence_id
            )

    save(
        "projects",
        project,
    )

    if (
        add_timeline
        and added_ids
    ):
        add_timeline_event(
            project_id,
            "Workspace evidence collected",
            description=(
                f"Collected {len(added_ids)} new evidence item(s) "
                f"for query: {resolved_query}"
            ),
            evidence_ids=added_ids,
        )

    result.metadata[
        "research_project_id"
    ] = project_id

    result.metadata[
        "new_project_evidence_ids"
    ] = added_ids

    return result


# ---------------------------------------------------------------------------
# Hypothesis Evidence Linking
# ---------------------------------------------------------------------------

def collect_hypothesis_evidence(
    project_id: str,
    hypothesis_id: str,
    *,
    query: str,
    relationship: str = "supporting",
    sources: list[str] | None = None,
    limit: int = 20,
    workspace_path: str | None = None,
    adapter_arguments: dict | None = None,
):
    """
    Collect workspace evidence and attach it to a hypothesis as either
    supporting or contradicting evidence.
    """

    result = collect_project_evidence(
        project_id,
        query=query,
        sources=sources,
        limit=limit,
        workspace_path=workspace_path,
        adapter_arguments=adapter_arguments,
        add_timeline=False,
    )

    linked = []

    for item in result.evidence:
        link_evidence(
            project_id,
            "hypothesis",
            hypothesis_id,
            item.evidence_id,
            relationship=relationship,
        )

        linked.append(
            item.evidence_id
        )

    add_timeline_event(
        project_id,
        (
            "Hypothesis evidence updated"
        ),
        description=(
            f"Linked {len(linked)} {relationship} evidence item(s) "
            f"to hypothesis {hypothesis_id}."
        ),
        related_ids=[
            hypothesis_id
        ],
        evidence_ids=linked,
    )

    result.metadata[
        "hypothesis_id"
    ] = hypothesis_id

    result.metadata[
        "relationship"
    ] = relationship

    return result


# ---------------------------------------------------------------------------
# Local Paper / Note Registration
# ---------------------------------------------------------------------------

def register_local_research_document(
    project_id: str,
    path: str,
    *,
    title: str | None = None,
    authors: list[str] | None = None,
    year: int | None = None,
    doi: str = "",
    url: str = "",
    citation: str = "",
    notes: str = "",
    tags: list[str] | None = None,
):
    """
    Register a local research artifact as a paper record.

    The actual document content remains part of the unified workspace
    document adapter. This function records the bibliographic/project
    relationship cleanly without duplicating the entire file.
    """

    project = _require_project(
        project_id
    )

    document_path = Path(
        path
    )

    paper_title = (
        title
        or document_path.stem
        or "Research Document"
    )

    paper = add_paper(
        project_id,
        paper_title,
        authors=authors or [],
        year=year,
        doi=doi,
        url=url,
        local_path=str(
            document_path
        ),
        citation=citation,
        notes=notes,
        tags=tags or [],
        metadata={
            "registered_from":
                "local_research_document",
        },
    )

    add_timeline_event(
        project_id,
        "Research document registered",
        description=(
            f"Registered {paper_title} in project {project.name}."
        ),
        related_ids=[
            paper.paper_id
        ],
    )

    return paper
