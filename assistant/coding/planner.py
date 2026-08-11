"""
E.V.I.E. - Self-Engineering Planner

Phase 12M

Purpose:
Produce a bounded repository-level change plan using:
- unified workspace evidence
- repository graph
- impact analysis
- current file contents

The planner is not allowed to write files, create branches, or commit.
"""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, Field

from assistant.workspace.query_controller import query_workspace

from .impact import analyze_change_scope
from .models import EngineeringEdit, EngineeringPlan


SYSTEM_PROMPT = """
You are E.V.I.E.'s repository-level engineering planner.

You are given a user goal, repository evidence, repository impact analysis,
and current contents of candidate files.

Rules:
- Preserve the requested goal exactly.
- Make the smallest coherent repository-level change.
- Only propose edits to files explicitly listed in planned_paths.
- Return COMPLETE replacement contents for edited files.
- Never propose shell scripts, git push, PR creation, destructive commands,
  dependency installation, secret access, or permission bypass.
- Targeted validation commands must be argv arrays.
- Full regression command must also be an argv array.
- Prefer python -m py_compile for changed Python files and python -m pytest -q
  for full regression when appropriate.
- If the change cannot be safely accomplished with the available files,
  keep edits empty and explain why.
"""


class EditModel(BaseModel):
    path: str
    content: str
    reason: str = ""


class PlanModel(BaseModel):
    planned_paths: list[str] = Field(default_factory=list)
    edits: list[EditModel] = Field(default_factory=list)
    targeted_commands: list[list[str]] = Field(default_factory=list)
    regression_command: list[str] = Field(default_factory=list)
    commit_message: str = ""
    documentation_note: str = ""
    confidence: int = 0
    rationale: str = ""


def _client():
    from assistant.brain import client
    return client


def _read_candidate_files(root_path, paths):
    root = Path(root_path).resolve()
    payload = []

    for relative in paths:
        target = (root / relative).resolve()
        try:
            target.relative_to(root)
        except ValueError:
            continue

        content = ""
        if target.exists() and target.is_file():
            content = target.read_text(
                encoding="utf-8",
                errors="ignore",
            )

        payload.append(
            {
                "path": relative,
                "content": content,
            }
        )

    return payload


def plan_engineering_change(
    *,
    goal: str,
    repository: str,
    root_path: str,
    candidate_paths: list[str],
    workspace_sources: list[str] | None = None,
    evidence_limit: int = 30,
):
    impact = analyze_change_scope(
        repository,
        candidate_paths,
    )

    workspace = query_workspace(
        goal,
        repository=repository,
        workspace_path=root_path,
        sources=workspace_sources or [
            "repository",
            "local",
            "github",
            "notion",
            "memory",
            "knowledge",
        ],
        limit=evidence_limit,
        synthesize=False,
        minimum_per_source=1,
    )

    evidence_payload = [
        {
            "evidence_id": item.evidence_id,
            "source_type": item.source_type,
            "title": item.title,
            "path": item.path,
            "content": item.content[:8000],
        }
        for item in workspace.evidence
    ]

    impact_payload = {
        "risk": impact["risk"],
        "paths": impact["paths"],
        "impacted_nodes": [
            {
                "path": item["node"].path,
                "depth": item["depth"],
            }
            for item in impact["impacted_nodes"][:40]
        ],
        "tests": [
            node.path
            for node in impact["tests"]
        ],
    }

    prompt = {
        "goal": goal,
        "repository": repository,
        "candidate_paths": candidate_paths,
        "impact": impact_payload,
        "files": _read_candidate_files(
            root_path,
            candidate_paths,
        ),
        "workspace_evidence": evidence_payload,
    }

    response = _client().responses.parse(
        model="gpt-5.2",
        instructions=SYSTEM_PROMPT,
        input=json.dumps(
            prompt,
            indent=2,
            ensure_ascii=False,
            default=str,
        ),
        text_format=PlanModel,
    )

    parsed = response.output_parsed
    allowed = set(candidate_paths)

    planned_paths = [
        path
        for path in parsed.planned_paths
        if path in allowed
    ]

    edits = [
        EngineeringEdit(
            path=edit.path,
            content=edit.content,
            reason=edit.reason,
        )
        for edit in parsed.edits
        if edit.path in allowed
    ]

    for edit in edits:
        if edit.path not in planned_paths:
            planned_paths.append(edit.path)

    return EngineeringPlan(
        goal=goal,
        repository=repository,
        planned_paths=planned_paths,
        edits=edits,
        targeted_commands=[
            [str(part) for part in command]
            for command in parsed.targeted_commands
            if command
        ],
        regression_command=[
            str(part)
            for part in parsed.regression_command
        ],
        commit_message=parsed.commit_message.strip(),
        documentation_note=parsed.documentation_note.strip(),
        confidence=max(
            0,
            min(
                100,
                int(parsed.confidence or 0),
            ),
        ),
        rationale=parsed.rationale,
        metadata={
            "impact_risk": impact["risk"],
            "impact_count": len(
                impact["impacted_nodes"]
            ),
            "workspace_evidence_ids": [
                item.evidence_id
                for item in workspace.evidence
            ],
        },
    )
