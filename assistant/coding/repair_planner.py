"""
E.V.I.E. - Bounded Coding Repair Planner

Phase 12K

Purpose:
Ask the reasoning model for a repair plan constrained to the current
coding transaction.

Hard bounds:
- only planned_paths may be edited
- no branch switching
- no commit
- no shell commands
- validation commands must be explicit argv lists
- planner may request rollback instead of edits
"""

from __future__ import annotations

import json

from pydantic import (
    BaseModel,
    Field,
)

from .repair_models import (
    RepairEdit,
    RepairPlan,
)

from .state import (
    load_transaction,
)


SYSTEM_PROMPT = """
You are E.V.I.E.'s bounded repository repair planner.

You are repairing ONE existing coding transaction.

Rules:
- Preserve the transaction goal.
- You may only edit files listed in planned_paths.
- Do not propose Git commits, pushes, branch switches, dependency installs,
  destructive commands, or shell scripts.
- Prefer the smallest repair that addresses the failure.
- Return full replacement content only for files that must change.
- Validation commands must be argv arrays, for example:
  ["python", "-m", "py_compile", "assistant/example.py"]
- If the failure cannot be repaired safely inside planned_paths, choose
  action="request_user" or action="rollback".
- Never claim a repair succeeded before validation runs.
"""


class PlannedEditModel(
    BaseModel
):
    path: str
    content: str
    reason: str = ""


class RepairPlanModel(
    BaseModel
):
    action: str
    diagnosis: str = ""
    edits: list[PlannedEditModel] = Field(
        default_factory=list
    )
    validation_commands: list[list[str]] = Field(
        default_factory=list
    )
    confidence: int = 0
    rationale: str = ""


def _client():
    from assistant.brain import (
        client,
    )

    return client


def plan_repair(
    transaction_id: str,
    diagnostic,
):
    transaction = load_transaction(
        transaction_id
    )

    if transaction is None:
        raise ValueError(
            (
                "Coding transaction does not exist: "
                f"{transaction_id}"
            )
        )

    file_payload = []

    for path in transaction.planned_paths:
        snapshot = transaction.snapshots.get(
            path
        )

        file_payload.append(
            {
                "path":
                    path,

                "baseline_content":
                    (
                        snapshot.content
                        if snapshot is not None
                        else ""
                    ),
            }
        )

    payload = {
        "goal":
            transaction.goal,

        "planned_paths":
            transaction.planned_paths,

        "changed_paths":
            transaction.changed_paths,

        "failure":
            {
                "command":
                    diagnostic.command,

                "returncode":
                    diagnostic.returncode,

                "error_type":
                    diagnostic.error_type,

                "summary":
                    diagnostic.summary,

                "file_paths":
                    diagnostic.file_paths,
            },

        "files":
            file_payload,
    }

    response = _client().responses.parse(
        model="gpt-5.2",
        instructions=SYSTEM_PROMPT,
        input=json.dumps(
            payload,
            indent=2,
            ensure_ascii=False,
            default=str,
        ),
        text_format=RepairPlanModel,
    )

    parsed = response.output_parsed

    allowed = set(
        transaction.planned_paths
    )

    edits = []

    for edit in parsed.edits:
        if edit.path not in allowed:
            continue

        edits.append(
            RepairEdit(
                path=
                    edit.path,

                content=
                    edit.content,

                reason=
                    edit.reason,
            )
        )

    action = (
        parsed.action
        if parsed.action in {
            "repair",
            "retry",
            "request_user",
            "rollback",
            "stop",
        }
        else "request_user"
    )

    if (
        action == "repair"
        and not edits
    ):
        action = "request_user"

    return RepairPlan(
        action=
            action,

        diagnosis=
            parsed.diagnosis,

        edits=
            edits,

        validation_commands=[
            [
                str(
                    part
                )
                for part
                in command
            ]
            for command
            in parsed.validation_commands
            if isinstance(
                command,
                list,
            )
            and command
        ],

        confidence=
            max(
                0,
                min(
                    100,
                    int(
                        parsed.confidence
                        or 0
                    ),
                ),
            ),

        rationale=
            parsed.rationale,
    )
