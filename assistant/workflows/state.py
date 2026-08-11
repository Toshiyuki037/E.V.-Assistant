"""
E.V.I.E. - Workflow Persistent State

Phase 11A

Storage:
    runtime/workflows/definitions/
    runtime/workflows/active/
    runtime/workflows/history/
    runtime/workflows/schedules/
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from .models import (
    WorkflowDefinition,
    WorkflowRun,
    definition_from_dict,
    definition_to_dict,
    run_from_dict,
    run_to_dict,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_RUNTIME = PROJECT_ROOT / "runtime" / "workflows"
DEFINITIONS_DIRECTORY = WORKFLOW_RUNTIME / "definitions"
ACTIVE_DIRECTORY = WORKFLOW_RUNTIME / "active"
HISTORY_DIRECTORY = WORKFLOW_RUNTIME / "history"
SCHEDULES_DIRECTORY = WORKFLOW_RUNTIME / "schedules"


def now_string():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def ensure_workflow_runtime():
    for directory in (
        DEFINITIONS_DIRECTORY,
        ACTIVE_DIRECTORY,
        HISTORY_DIRECTORY,
        SCHEDULES_DIRECTORY,
    ):
        directory.mkdir(parents=True, exist_ok=True)


def _write_json(path: Path, payload: dict):
    ensure_workflow_runtime()
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    temp.replace(path)


def _read_json(path: Path):
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def definition_path(workflow_id: str):
    return DEFINITIONS_DIRECTORY / f"{workflow_id}.json"


def save_definition(definition: WorkflowDefinition):
    if not definition.created_at:
        definition.created_at = now_string()
    definition.updated_at = now_string()
    _write_json(definition_path(definition.workflow_id), definition_to_dict(definition))
    return definition


def load_definition(workflow_id: str):
    path = definition_path(workflow_id)
    if not path.exists():
        return None
    data = _read_json(path)
    return definition_from_dict(data) if data is not None else None


def list_definitions():
    ensure_workflow_runtime()
    result = []
    for path in sorted(DEFINITIONS_DIRECTORY.glob("*.json")):
        data = _read_json(path)
        if data is not None:
            result.append(definition_from_dict(data))
    return result


def remove_definition(workflow_id: str):
    path = definition_path(workflow_id)
    if not path.exists():
        return False
    try:
        path.unlink()
        return True
    except OSError:
        return False


def active_run_path(run_id: str):
    return ACTIVE_DIRECTORY / f"{run_id}.json"


def history_run_path(run_id: str):
    return HISTORY_DIRECTORY / f"{run_id}.json"


def save_run(run: WorkflowRun):
    if not run.created_at:
        run.created_at = now_string()
    run.updated_at = now_string()
    _write_json(active_run_path(run.run_id), run_to_dict(run))
    return run


def load_run(run_id: str):
    for path in (
        active_run_path(run_id),
        history_run_path(run_id),
    ):
        if path.exists():
            data = _read_json(path)
            if data is not None:
                return run_from_dict(data)
    return None


def list_active_runs():
    ensure_workflow_runtime()
    result = []
    for path in sorted(ACTIVE_DIRECTORY.glob("*.json")):
        data = _read_json(path)
        if data is not None:
            result.append(run_from_dict(data))
    return result


def archive_run(run: WorkflowRun):
    ensure_workflow_runtime()
    _write_json(history_run_path(run.run_id), run_to_dict(run))
    active = active_run_path(run.run_id)
    if active.exists():
        try:
            active.unlink()
        except OSError:
            pass
    return run


def delete_active_run(run_id: str):
    path = active_run_path(run_id)
    if not path.exists():
        return False
    try:
        path.unlink()
        return True
    except OSError:
        return False
