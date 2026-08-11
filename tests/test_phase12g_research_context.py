"""
Phase 12G research synthesis-context tests.
"""

import assistant.research.state as research_state
import assistant.workspace.evidence as evidence_store

from assistant.research.controller import (
    create_project,
)
from assistant.research.synthesis import (
    build_research_context,
)
from assistant.workspace.controller import (
    create_evidence,
)


def test_build_context_contains_workspace_evidence(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(
        research_state,
        "ROOT",
        tmp_path
        / "research",
    )

    monkeypatch.setattr(
        evidence_store,
        "WORKSPACE_RUNTIME",
        tmp_path
        / "workspace",
    )

    monkeypatch.setattr(
        evidence_store,
        "EVIDENCE_DIRECTORY",
        tmp_path
        / "workspace"
        / "evidence",
    )

    monkeypatch.setattr(
        evidence_store,
        "ENTITY_DIRECTORY",
        tmp_path
        / "workspace"
        / "entities",
    )

    monkeypatch.setattr(
        evidence_store,
        "RELATIONSHIP_DIRECTORY",
        tmp_path
        / "workspace"
        / "relationships",
    )

    project = create_project(
        "Evidence Project",
        "Test research context.",
        project_id="evidence-project",
    )

    item = create_evidence(
        source_type="research_note",
        source_id="note-1",
        title="Research Note",
        content="Temperature may influence calibration drift.",
    )

    project.evidence_ids.append(
        item.evidence_id
    )

    research_state.save(
        "projects",
        project,
    )

    context = build_research_context(
        project.project_id
    )

    assert len(
        context[
            "evidence"
        ]
    ) == 1

    assert (
        context[
            "evidence"
        ][
            0
        ][
            "evidence_id"
        ]
        == item.evidence_id
    )
