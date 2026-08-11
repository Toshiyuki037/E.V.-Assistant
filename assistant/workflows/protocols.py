"""
E.V.I.E. - Saved Workflow Protocols
Phase 11E

Purpose:
Persistent reusable protocol definitions built on the Phase 11 workflow engine.
"""

from __future__ import annotations

import json
import re
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .controller import create_workflow, run_workflow


PROTOCOL_DIR = Path("runtime/workflows/protocols")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _slug(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9_-]+", "-", value.strip()).strip("-").lower()
    return value or "protocol"


def _path(protocol_id: str) -> Path:
    return PROTOCOL_DIR / f"{_slug(protocol_id)}.json"


def _read(protocol_id: str) -> dict[str, Any]:
    path = _path(protocol_id)
    if not path.exists():
        raise RuntimeError(f"Protocol does not exist: {protocol_id}")
    return json.loads(path.read_text(encoding="utf-8"))


def _write(data: dict[str, Any]) -> dict[str, Any]:
    PROTOCOL_DIR.mkdir(parents=True, exist_ok=True)
    data = deepcopy(data)
    data["updated_at"] = _now()
    if not data.get("created_at"):
        data["created_at"] = data["updated_at"]
    _path(data["protocol_id"]).write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return data


def create_protocol(
    protocol_id: str,
    name: str,
    goal: str,
    steps: list[dict[str, Any]],
    description: str = "",
    default_variables: dict[str, Any] | None = None,
    enabled: bool = True,
    overwrite: bool = False,
) -> dict[str, Any]:
    protocol_id = _slug(protocol_id)
    path = _path(protocol_id)
    if path.exists() and not overwrite:
        raise RuntimeError(f"Protocol already exists: {protocol_id}")

    data = {
        "protocol_id": protocol_id,
        "name": name,
        "goal": goal,
        "description": description,
        "enabled": bool(enabled),
        "default_variables": deepcopy(default_variables or {}),
        "steps": deepcopy(steps),
        "created_at": _now(),
        "updated_at": _now(),
    }
    return _write(data)


def get_protocol(protocol_id: str) -> dict[str, Any]:
    return _read(protocol_id)


def list_protocols(include_disabled: bool = True) -> list[dict[str, Any]]:
    PROTOCOL_DIR.mkdir(parents=True, exist_ok=True)
    results = []
    for path in sorted(PROTOCOL_DIR.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if include_disabled or data.get("enabled", True):
            results.append(data)
    return results


def update_protocol(protocol_id: str, **changes: Any) -> dict[str, Any]:
    data = _read(protocol_id)
    protected = {"protocol_id", "created_at"}
    for key, value in changes.items():
        if key not in protected and value is not None:
            data[key] = deepcopy(value)
    return _write(data)


def set_protocol_enabled(protocol_id: str, enabled: bool) -> dict[str, Any]:
    return update_protocol(protocol_id, enabled=bool(enabled))


def delete_protocol(protocol_id: str) -> bool:
    path = _path(protocol_id)
    if not path.exists():
        return False
    path.unlink()
    return True


def clone_protocol(
    protocol_id: str,
    new_protocol_id: str,
    new_name: str | None = None,
) -> dict[str, Any]:
    source = _read(protocol_id)
    return create_protocol(
        protocol_id=new_protocol_id,
        name=new_name or f"{source['name']} Copy",
        goal=source["goal"],
        description=source.get("description", ""),
        steps=source.get("steps", []),
        default_variables=source.get("default_variables", {}),
        enabled=source.get("enabled", True),
    )


def run_protocol(
    protocol_id: str,
    variables: dict[str, Any] | None = None,
):
    protocol = _read(protocol_id)
    if not protocol.get("enabled", True):
        raise RuntimeError(f"Protocol is disabled: {protocol_id}")

    merged_variables = deepcopy(protocol.get("default_variables", {}))
    merged_variables.update(variables or {})

    # Each invocation gets its own workflow definition ID so saved templates
    # remain immutable while workflow runs retain their normal Phase 11 state.
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
    workflow_id = f"protocol-{protocol['protocol_id']}-{stamp}"

    create_workflow(
        workflow_id=workflow_id,
        name=protocol["name"],
        goal=protocol["goal"],
        description=protocol.get("description", ""),
        steps=deepcopy(protocol.get("steps", [])),
    )

    return run_workflow(
        workflow_id,
        variables=merged_variables,
    )
