"""
E.V.I.E. - Workflow Audit Log

Phase 11C

Purpose:
Persist an append-only audit trail for workflow execution.

Each event is written as one JSON object per line to:
    runtime/workflows/audit/<run_id>.jsonl
"""

from __future__ import annotations

import json

from pathlib import Path

from .state import (
    WORKFLOW_RUNTIME,
    now_string,
)


AUDIT_DIRECTORY = (
    WORKFLOW_RUNTIME
    / "audit"
)


def ensure_audit_directory():
    AUDIT_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )


def audit_path(
    run_id: str,
):
    return (
        AUDIT_DIRECTORY
        / f"{run_id}.jsonl"
    )


def record_audit_event(
    run_id: str,
    event_type: str,
    *,
    workflow_id: str = "",
    step_id: str = "",
    message: str = "",
    data: dict | None = None,
):
    ensure_audit_directory()

    event = {
        "time":
            now_string(),

        "run_id":
            str(
                run_id
                or ""
            ),

        "workflow_id":
            str(
                workflow_id
                or ""
            ),

        "step_id":
            str(
                step_id
                or ""
            ),

        "event_type":
            str(
                event_type
                or ""
            ),

        "message":
            str(
                message
                or ""
            ),

        "data":
            (
                data
                if isinstance(
                    data,
                    dict,
                )
                else {}
            ),
    }

    with audit_path(
        run_id
    ).open(
        "a",
        encoding="utf-8",
    ) as handle:

        handle.write(
            json.dumps(
                event,
                ensure_ascii=False,
                default=str,
            )
            + "\n"
        )

    return event


def load_audit_events(
    run_id: str,
):
    path = audit_path(
        run_id
    )

    if not path.exists():

        return []


    events = []


    for line in path.read_text(
        encoding="utf-8"
    ).splitlines():

        line = (
            line.strip()
        )


        if not line:

            continue


        try:

            event = (
                json.loads(
                    line
                )
            )

        except json.JSONDecodeError:

            continue


        if isinstance(
            event,
            dict,
        ):

            events.append(
                event
            )


    return events
