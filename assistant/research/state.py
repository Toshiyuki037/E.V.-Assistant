"""
E.V.I.E. - Research Intelligence Persistence

Simple JSON persistence for Phase 12F.
"""

import json
from dataclasses import fields
from pathlib import Path

from .models import (
    ResearchProject,
    ResearchPaper,
    ResearchHypothesis,
    ResearchExperiment,
    ExperimentResult,
    ResearchDecision,
    ResearchTimelineEvent,
)

ROOT = Path("runtime/research")

KINDS = {
    "projects": ResearchProject,
    "papers": ResearchPaper,
    "hypotheses": ResearchHypothesis,
    "experiments": ResearchExperiment,
    "results": ExperimentResult,
    "decisions": ResearchDecision,
    "timeline": ResearchTimelineEvent,
}


def _directory(kind: str) -> Path:
    path = ROOT / kind
    path.mkdir(parents=True, exist_ok=True)
    return path


def _identifier_field(kind: str) -> str:
    mapping = {
        "projects": "project_id",
        "papers": "paper_id",
        "hypotheses": "hypothesis_id",
        "experiments": "experiment_id",
        "results": "result_id",
        "decisions": "decision_id",
        "timeline": "event_id",
    }
    return mapping[kind]


def save(kind: str, obj):
    if kind not in KINDS:
        raise ValueError(f"Unknown research kind: {kind}")
    from dataclasses import asdict
    ident = getattr(obj, _identifier_field(kind))
    path = _directory(kind) / f"{ident}.json"
    path.write_text(
        json.dumps(asdict(obj), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return obj


def load(kind: str, ident: str):
    if kind not in KINDS:
        raise ValueError(f"Unknown research kind: {kind}")
    path = _directory(kind) / f"{ident}.json"
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    cls = KINDS[kind]
    allowed = {f.name for f in fields(cls)}
    return cls(**{k: v for k, v in data.items() if k in allowed})


def list_all(kind: str):
    if kind not in KINDS:
        raise ValueError(f"Unknown research kind: {kind}")
    results = []
    for path in sorted(_directory(kind).glob("*.json")):
        obj = load(kind, path.stem)
        if obj is not None:
            results.append(obj)
    return results
