"""
E.V.I.E. - Tool Audit Logger

Created: August 9, 2026
Last Edited: August 9, 2026
Author: Max Maehara

Purpose:
    Records tool requests and results for debugging, accountability,
    and future autonomous-task verification.

How It Works:
    Tool events are stored as JSON Lines under:

        runtime/tools/audit.jsonl

Most Recent Change:
    Initial Phase 6 audit logging.
"""

import json

from datetime import datetime
from pathlib import Path


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

ROOT = (
    Path(__file__)
    .resolve()
    .parent
    .parent
    .parent
)

AUDIT_DIRECTORY = (
    ROOT
    / "runtime"
    / "tools"
)

AUDIT_DIRECTORY.mkdir(
    parents=True,
    exist_ok=True,
)

AUDIT_FILE = (
    AUDIT_DIRECTORY
    / "audit.jsonl"
)


# ---------------------------------------------------------------------------
# Safe JSON Conversion
# ---------------------------------------------------------------------------

def make_json_safe(
    value,
):
    """
    Converts common Python values into JSON-safe representations.
    """

    if isinstance(
        value,
        Path,
    ):
        return str(
            value
        )

    if isinstance(
        value,
        dict,
    ):

        return {
            str(key):
                make_json_safe(
                    item
                )

            for key, item
            in value.items()
        }

    if isinstance(
        value,
        (
            list,
            tuple,
            set,
        ),
    ):

        return [
            make_json_safe(
                item
            )

            for item in value
        ]

    if isinstance(
        value,
        (
            str,
            int,
            float,
            bool,
        ),
    ) or value is None:

        return value

    return repr(
        value
    )


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def log_tool_event(
    tool_name: str,
    status: str,
    risk: str,
    arguments=None,
    result=None,
    error=None,
):
    """
    Writes one tool execution event.
    """

    event = {
        "timestamp":
            datetime.now().isoformat(
                timespec="seconds"
            ),

        "tool":
            tool_name,

        "status":
            status,

        "risk":
            risk,

        "arguments":
            make_json_safe(
                arguments
                or {}
            ),

        "result":
            make_json_safe(
                result
            ),

        "error":
            (
                str(error)
                if error
                else None
            ),
    }

    with AUDIT_FILE.open(
        "a",
        encoding="utf-8",
    ) as file:

        file.write(
            json.dumps(
                event,
                ensure_ascii=False,
            )
        )

        file.write(
            "\n"
        )

    return event


# ---------------------------------------------------------------------------
# Read Recent Events
# ---------------------------------------------------------------------------

def get_recent_audit_events(
    limit: int = 20,
):
    if not AUDIT_FILE.exists():
        return []

    lines = AUDIT_FILE.read_text(
        encoding="utf-8"
    ).splitlines()

    events = []

    for line in lines[
        -limit:
    ]:

        try:

            events.append(
                json.loads(
                    line
                )
            )

        except json.JSONDecodeError:

            continue

    return events


# ---------------------------------------------------------------------------
# Standalone Test
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    event = log_tool_event(
        tool_name="audit_test",
        status="success",
        risk="low",
        arguments={
            "message":
                "Phase 6 audit test"
        },
        result={
            "working":
                True
        },
    )

    print(
        "E.V.I.E. Tool Audit"
    )

    print(
        "--------------------"
    )

    print(
        "Audit file:",
        AUDIT_FILE,
    )

    print()

    print(
        event
    )