from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path

from .models import EngineeringEdit, EngineeringPlan


PROJECT_ROOT = Path(__file__).resolve().parents[2]

PENDING_FILE = (
    PROJECT_ROOT
    / "runtime"
    / "coding"
    / "pending_self_engineering.json"
)


def clear_pending_engineering():
    if PENDING_FILE.exists():
        PENDING_FILE.unlink()


def _write(payload):
    PENDING_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    PENDING_FILE.write_text(
        json.dumps(
            payload,
            indent=2,
            ensure_ascii=False,
            default=str,
        ),
        encoding="utf-8",
    )

    return payload


def save_pending_plan(
    plan: EngineeringPlan,
    *,
    root_path: str,
    candidate_paths: list[str],
):
    return _write(
        {
            "state": "awaiting_execution_approval",
            "root_path": root_path,
            "candidate_paths": list(candidate_paths),
            "plan": asdict(plan),
            "transaction_id": "",
        }
    )


def save_pending_recovery(
    transaction_id: str,
    *,
    root_path: str,
):
    return _write(
        {
            "state": "awaiting_recovery",
            "root_path": root_path,
            "candidate_paths": [],
            "plan": {},
            "transaction_id": transaction_id,
        }
    )


def save_pending_transaction(
    transaction_id: str,
    *,
    root_path: str,
    suggested_commit_message: str,
):
    return _write(
        {
            "state": "awaiting_commit_approval",
            "root_path": root_path,
            "candidate_paths": [],
            "plan": {
                "commit_message": suggested_commit_message,
            },
            "transaction_id": transaction_id,
        }
    )


def load_pending_engineering():
    if not PENDING_FILE.exists():
        return None

    try:
        return json.loads(
            PENDING_FILE.read_text(
                encoding="utf-8"
            )
        )
    except Exception:
        return None


def pending_plan_from_payload(payload):
    plan = payload.get("plan", {}) or {}

    edits = [
        EngineeringEdit(**item)
        for item in (
            plan.get("edits", [])
            or []
        )
    ]

    return EngineeringPlan(
        goal=plan.get("goal", ""),
        repository=plan.get("repository", ""),
        planned_paths=list(
            plan.get("planned_paths", [])
            or []
        ),
        edits=edits,
        targeted_commands=[
            list(command)
            for command in (
                plan.get(
                    "targeted_commands",
                    [],
                )
                or []
            )
        ],
        regression_command=list(
            plan.get(
                "regression_command",
                [],
            )
            or []
        ),
        commit_message=plan.get(
            "commit_message",
            "",
        ),
        documentation_note=plan.get(
            "documentation_note",
            "",
        ),
        confidence=int(
            plan.get(
                "confidence",
                0,
            )
            or 0
        ),
        rationale=plan.get(
            "rationale",
            "",
        ),
        metadata=dict(
            plan.get(
                "metadata",
                {},
            )
            or {}
        ),
    )
