"""
Phase 12G research ingestion tests.
"""

import assistant.research.state as research_state
import assistant.workspace.evidence as evidence_store

from assistant.research.controller import (
    create_project,
    add_hypothesis,
)
from assistant.research.ingestion import (
    register_local_research_document,
)
from assistant.research.planning import (
    next_research_actions,
)


def test_register_local_document(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(
        research_state,
        "ROOT",
        tmp_path
        / "research",
    )

    project = create_project(
        "BP Drift",
        "Study calibration drift.",
        project_id="bp-drift",
    )

    paper = register_local_research_document(
        project.project_id,
        "papers/example.pdf",
        title="Example BP Paper",
    )

    loaded = research_state.load(
        "projects",
        project.project_id,
    )

    assert paper.paper_id in loaded.paper_ids


def test_research_planning_open_hypothesis(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(
        research_state,
        "ROOT",
        tmp_path
        / "research",
    )

    project = create_project(
        "FPGA",
        "Study timing.",
        project_id="fpga",
    )

    add_hypothesis(
        project.project_id,
        "Pipelining improves timing.",
    )

    actions = next_research_actions(
        project.project_id
    )

    assert actions
