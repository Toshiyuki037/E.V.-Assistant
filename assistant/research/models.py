"""
E.V.I.E. - Research Intelligence Models

Phase 12F:
Structured research projects, papers, hypotheses, experiments,
results, decisions, timelines, and workspace evidence links.
"""

from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass
class ResearchPaper:
    paper_id: str
    title: str
    authors: list[str] = field(default_factory=list)
    year: int | None = None
    doi: str = ""
    url: str = ""
    local_path: str = ""
    citation: str = ""
    notes: str = ""
    tags: list[str] = field(default_factory=list)
    evidence_ids: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ResearchHypothesis:
    hypothesis_id: str
    statement: str
    status: str = "open"
    rationale: str = ""
    supporting_evidence_ids: list[str] = field(default_factory=list)
    contradicting_evidence_ids: list[str] = field(default_factory=list)
    experiment_ids: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ExperimentResult:
    result_id: str
    experiment_id: str
    summary: str
    outcome: str = "unknown"
    metrics: dict[str, Any] = field(default_factory=dict)
    artifact_paths: list[str] = field(default_factory=list)
    evidence_ids: list[str] = field(default_factory=list)
    created_at: str = ""


@dataclass
class ResearchExperiment:
    experiment_id: str
    title: str
    objective: str = ""
    hypothesis_ids: list[str] = field(default_factory=list)
    independent_variables: list[str] = field(default_factory=list)
    dependent_variables: list[str] = field(default_factory=list)
    controls: list[str] = field(default_factory=list)
    procedure: str = ""
    code_paths: list[str] = field(default_factory=list)
    dataset_paths: list[str] = field(default_factory=list)
    status: str = "planned"
    result_ids: list[str] = field(default_factory=list)
    evidence_ids: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ResearchDecision:
    decision_id: str
    decision: str
    rationale: str = ""
    alternatives: list[str] = field(default_factory=list)
    evidence_ids: list[str] = field(default_factory=list)
    created_at: str = ""


@dataclass
class ResearchTimelineEvent:
    event_id: str
    title: str
    description: str = ""
    event_at: str = ""
    related_ids: list[str] = field(default_factory=list)
    evidence_ids: list[str] = field(default_factory=list)


@dataclass
class ResearchProject:
    project_id: str
    name: str
    goal: str
    description: str = ""
    status: str = "active"
    repository: str = ""
    workspace_path: str = ""
    paper_ids: list[str] = field(default_factory=list)
    hypothesis_ids: list[str] = field(default_factory=list)
    experiment_ids: list[str] = field(default_factory=list)
    result_ids: list[str] = field(default_factory=list)
    decision_ids: list[str] = field(default_factory=list)
    timeline_event_ids: list[str] = field(default_factory=list)
    evidence_ids: list[str] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


def to_dict(value):
    return asdict(value)
