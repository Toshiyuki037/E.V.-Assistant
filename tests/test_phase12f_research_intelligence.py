from pathlib import Path

import assistant.research.state as state
from assistant.research.controller import (
    create_project,
    add_paper,
    add_hypothesis,
    add_experiment,
    record_result,
    record_decision,
    add_timeline_event,
    link_evidence,
    summarize_project,
)


def test_research_lifecycle(tmp_path, monkeypatch):
    monkeypatch.setattr(state, "ROOT", tmp_path / "research")

    project = create_project(
        "BP Calibration Drift",
        "Study calibration stability.",
        project_id="bp-drift",
    )

    paper = add_paper(
        project.project_id,
        "Example Paper",
        authors=["A. Researcher"],
        year=2026,
        evidence_ids=["ev:paper:1"],
    )

    hypothesis = add_hypothesis(
        project.project_id,
        "Temperature contributes to calibration drift.",
        supporting_evidence_ids=["ev:paper:1"],
    )

    experiment = add_experiment(
        project.project_id,
        "Temperature perturbation",
        objective="Measure drift under temperature change.",
        hypothesis_ids=[hypothesis.hypothesis_id],
        independent_variables=["temperature"],
        dependent_variables=["prediction error"],
    )

    result = record_result(
        project.project_id,
        experiment.experiment_id,
        "Prediction error increased after perturbation.",
        outcome="supports",
        metrics={"delta_mae": 3.2},
    )

    decision = record_decision(
        project.project_id,
        "Include temperature compensation.",
        rationale="Observed error increased with temperature perturbation.",
    )

    event = add_timeline_event(
        project.project_id,
        "First perturbation result",
        related_ids=[experiment.experiment_id, result.result_id],
    )

    summary = summarize_project(project.project_id)

    assert summary["counts"]["papers"] == 1
    assert summary["counts"]["hypotheses"] == 1
    assert summary["counts"]["experiments"] == 1
    assert summary["counts"]["results"] == 1
    assert summary["counts"]["decisions"] == 1
    assert summary["counts"]["timeline_events"] == 1
    assert paper.paper_id
    assert decision.decision_id
    assert event.event_id


def test_hypothesis_experiment_link(tmp_path, monkeypatch):
    monkeypatch.setattr(state, "ROOT", tmp_path / "research")

    project = create_project("FPGA Research", "Test FPGA design.", project_id="fpga")
    hypothesis = add_hypothesis(project.project_id, "Pipelining improves timing.")
    experiment = add_experiment(
        project.project_id,
        "Pipeline test",
        hypothesis_ids=[hypothesis.hypothesis_id],
    )

    loaded = state.load("hypotheses", hypothesis.hypothesis_id)
    assert experiment.experiment_id in loaded.experiment_ids


def test_evidence_linking(tmp_path, monkeypatch):
    monkeypatch.setattr(state, "ROOT", tmp_path / "research")

    project = create_project("Evidence Test", "Test evidence.", project_id="evidence-test")
    hypothesis = add_hypothesis(project.project_id, "Test hypothesis.")

    updated = link_evidence(
        project.project_id,
        "hypothesis",
        hypothesis.hypothesis_id,
        "ev:test:123",
        relationship="contradicting",
    )

    assert "ev:test:123" in updated.contradicting_evidence_ids
    loaded_project = state.load("projects", project.project_id)
    assert "ev:test:123" in loaded_project.evidence_ids
