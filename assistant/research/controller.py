"""
E.V.I.E. - Research Intelligence Controller

Phase 12F orchestration layer.
"""

from datetime import datetime, timezone
import hashlib
import re

from .models import (
    ResearchProject,
    ResearchPaper,
    ResearchHypothesis,
    ResearchExperiment,
    ExperimentResult,
    ResearchDecision,
    ResearchTimelineEvent,
)
from .state import save, load, list_all


def _now():
    return datetime.now(timezone.utc).isoformat()


def _slug(text: str):
    value = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return value[:48] or "research"


def _id(prefix: str, seed: str):
    digest = hashlib.sha256(f"{prefix}:{seed}:{_now()}".encode()).hexdigest()[:12]
    return f"{prefix}_{digest}"


def create_project(name, goal, description="", repository="", workspace_path="",
                   project_id=None, metadata=None):
    project_id = project_id or _slug(name)
    existing = load("projects", project_id)
    if existing is not None:
        raise ValueError(f"Research project already exists: {project_id}")
    now = _now()
    project = ResearchProject(
        project_id=project_id,
        name=name,
        goal=goal,
        description=description,
        repository=repository,
        workspace_path=workspace_path,
        created_at=now,
        updated_at=now,
        metadata=metadata or {},
    )
    return save("projects", project)


def get_project(project_id):
    return load("projects", project_id)


def list_projects():
    return list_all("projects")


def _project(project_id):
    project = get_project(project_id)
    if project is None:
        raise ValueError(f"Research project does not exist: {project_id}")
    return project


def _touch(project):
    project.updated_at = _now()
    save("projects", project)


def add_paper(project_id, title, authors=None, year=None, doi="", url="",
              local_path="", citation="", notes="", tags=None,
              evidence_ids=None, metadata=None, paper_id=None):
    project = _project(project_id)
    paper = ResearchPaper(
        paper_id=paper_id or _id("paper", title),
        title=title,
        authors=authors or [],
        year=year,
        doi=doi,
        url=url,
        local_path=local_path,
        citation=citation,
        notes=notes,
        tags=tags or [],
        evidence_ids=evidence_ids or [],
        metadata=metadata or {},
    )
    save("papers", paper)
    if paper.paper_id not in project.paper_ids:
        project.paper_ids.append(paper.paper_id)
    for ev in paper.evidence_ids:
        if ev not in project.evidence_ids:
            project.evidence_ids.append(ev)
    _touch(project)
    return paper


def add_hypothesis(project_id, statement, rationale="", status="open",
                   supporting_evidence_ids=None, contradicting_evidence_ids=None,
                   metadata=None, hypothesis_id=None):
    project = _project(project_id)
    hypothesis = ResearchHypothesis(
        hypothesis_id=hypothesis_id or _id("hyp", statement),
        statement=statement,
        status=status,
        rationale=rationale,
        supporting_evidence_ids=supporting_evidence_ids or [],
        contradicting_evidence_ids=contradicting_evidence_ids or [],
        metadata=metadata or {},
    )
    save("hypotheses", hypothesis)
    if hypothesis.hypothesis_id not in project.hypothesis_ids:
        project.hypothesis_ids.append(hypothesis.hypothesis_id)
    _touch(project)
    return hypothesis


def add_experiment(project_id, title, objective="", hypothesis_ids=None,
                   independent_variables=None, dependent_variables=None,
                   controls=None, procedure="", code_paths=None,
                   dataset_paths=None, status="planned", evidence_ids=None,
                   metadata=None, experiment_id=None):
    project = _project(project_id)
    experiment = ResearchExperiment(
        experiment_id=experiment_id or _id("exp", title),
        title=title,
        objective=objective,
        hypothesis_ids=hypothesis_ids or [],
        independent_variables=independent_variables or [],
        dependent_variables=dependent_variables or [],
        controls=controls or [],
        procedure=procedure,
        code_paths=code_paths or [],
        dataset_paths=dataset_paths or [],
        status=status,
        evidence_ids=evidence_ids or [],
        metadata=metadata or {},
    )
    save("experiments", experiment)
    if experiment.experiment_id not in project.experiment_ids:
        project.experiment_ids.append(experiment.experiment_id)

    for hypothesis_id in experiment.hypothesis_ids:
        hypothesis = load("hypotheses", hypothesis_id)
        if hypothesis is not None and experiment.experiment_id not in hypothesis.experiment_ids:
            hypothesis.experiment_ids.append(experiment.experiment_id)
            save("hypotheses", hypothesis)

    _touch(project)
    return experiment


def record_result(project_id, experiment_id, summary, outcome="unknown",
                  metrics=None, artifact_paths=None, evidence_ids=None,
                  result_id=None):
    project = _project(project_id)
    experiment = load("experiments", experiment_id)
    if experiment is None:
        raise ValueError(f"Experiment does not exist: {experiment_id}")

    result = ExperimentResult(
        result_id=result_id or _id("result", f"{experiment_id}:{summary}"),
        experiment_id=experiment_id,
        summary=summary,
        outcome=outcome,
        metrics=metrics or {},
        artifact_paths=artifact_paths or [],
        evidence_ids=evidence_ids or [],
        created_at=_now(),
    )
    save("results", result)

    if result.result_id not in experiment.result_ids:
        experiment.result_ids.append(result.result_id)
    if outcome not in {"unknown", "pending"}:
        experiment.status = "completed"
    save("experiments", experiment)

    if result.result_id not in project.result_ids:
        project.result_ids.append(result.result_id)
    _touch(project)
    return result


def record_decision(project_id, decision, rationale="", alternatives=None,
                    evidence_ids=None, decision_id=None):
    project = _project(project_id)
    item = ResearchDecision(
        decision_id=decision_id or _id("decision", decision),
        decision=decision,
        rationale=rationale,
        alternatives=alternatives or [],
        evidence_ids=evidence_ids or [],
        created_at=_now(),
    )
    save("decisions", item)
    if item.decision_id not in project.decision_ids:
        project.decision_ids.append(item.decision_id)
    _touch(project)
    return item


def add_timeline_event(project_id, title, description="", event_at="",
                       related_ids=None, evidence_ids=None, event_id=None):
    project = _project(project_id)
    item = ResearchTimelineEvent(
        event_id=event_id or _id("event", title),
        title=title,
        description=description,
        event_at=event_at or _now(),
        related_ids=related_ids or [],
        evidence_ids=evidence_ids or [],
    )
    save("timeline", item)
    if item.event_id not in project.timeline_event_ids:
        project.timeline_event_ids.append(item.event_id)
    _touch(project)
    return item


def link_evidence(project_id, object_kind, object_id, evidence_id,
                  relationship="supporting"):
    project = _project(project_id)

    if evidence_id not in project.evidence_ids:
        project.evidence_ids.append(evidence_id)

    if object_kind == "paper":
        obj = load("papers", object_id)
        attr = "evidence_ids"
    elif object_kind == "hypothesis":
        obj = load("hypotheses", object_id)
        attr = (
            "contradicting_evidence_ids"
            if relationship == "contradicting"
            else "supporting_evidence_ids"
        )
    elif object_kind == "experiment":
        obj = load("experiments", object_id)
        attr = "evidence_ids"
    elif object_kind == "result":
        obj = load("results", object_id)
        attr = "evidence_ids"
    elif object_kind == "decision":
        obj = load("decisions", object_id)
        attr = "evidence_ids"
    elif object_kind == "timeline":
        obj = load("timeline", object_id)
        attr = "evidence_ids"
    else:
        raise ValueError(f"Unsupported research object kind: {object_kind}")

    if obj is None:
        raise ValueError(f"Research object does not exist: {object_kind}:{object_id}")

    values = getattr(obj, attr)
    if evidence_id not in values:
        values.append(evidence_id)

    kind_map = {
        "paper": "papers",
        "hypothesis": "hypotheses",
        "experiment": "experiments",
        "result": "results",
        "decision": "decisions",
        "timeline": "timeline",
    }
    save(kind_map[object_kind], obj)
    _touch(project)
    return obj


def summarize_project(project_id):
    project = _project(project_id)

    hypotheses = [
        load("hypotheses", x)
        for x in project.hypothesis_ids
    ]
    experiments = [
        load("experiments", x)
        for x in project.experiment_ids
    ]
    results = [
        load("results", x)
        for x in project.result_ids
    ]

    return {
        "project_id": project.project_id,
        "name": project.name,
        "goal": project.goal,
        "status": project.status,
        "counts": {
            "papers": len(project.paper_ids),
            "hypotheses": len(project.hypothesis_ids),
            "experiments": len(project.experiment_ids),
            "results": len(project.result_ids),
            "decisions": len(project.decision_ids),
            "timeline_events": len(project.timeline_event_ids),
            "evidence": len(project.evidence_ids),
        },
        "open_hypotheses": [
            x.statement for x in hypotheses
            if x is not None and x.status == "open"
        ],
        "active_experiments": [
            x.title for x in experiments
            if x is not None and x.status not in {"completed", "cancelled"}
        ],
        "latest_results": [
            {
                "experiment_id": x.experiment_id,
                "summary": x.summary,
                "outcome": x.outcome,
            }
            for x in results[-5:]
            if x is not None
        ],
    }
