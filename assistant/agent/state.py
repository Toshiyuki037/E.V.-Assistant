"""
E.V.I.E. - Persistent Agent State

Created: August 9, 2026
Last Edited: August 9, 2026
Author: Max Maehara

Purpose:
    Persists E.V.I.E.'s active Phase 7 task.

Capabilities:
    - save active tasks
    - restore unfinished tasks
    - preserve approval state
    - preserve retries
    - preserve replanning count
    - preserve continuation count
    - preserve step results
    - clear completed / cancelled task state

Storage:
    runtime/agent/current_task.json

Important:
    This state is runtime coordination data.

    It is not E.V.I.E.'s long-term memory system.

Most Recent Change:
    Added continuation_count persistence for dynamically extended
    Phase 7 tasks.
"""

import json

from datetime import datetime

from pathlib import Path

from .models import (
    AgentStep,
    AgentTask,
    task_to_dict,
)


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

AGENT_RUNTIME = (
    ROOT
    / "runtime"
    / "agent"
)

AGENT_RUNTIME.mkdir(
    parents=True,
    exist_ok=True,
)

CURRENT_TASK_FILE = (
    AGENT_RUNTIME
    / "current_task.json"
)


# ---------------------------------------------------------------------------
# Time
# ---------------------------------------------------------------------------

def now_string():
    """
    Returns a compact local ISO timestamp.
    """

    return (
        datetime.now()
        .isoformat(
            timespec="seconds"
        )
    )


# ---------------------------------------------------------------------------
# Save Task
# ---------------------------------------------------------------------------

def save_task(
    task: AgentTask,
):
    """
    Persists the complete active task state.
    """

    if not task.created_at:

        task.created_at = (
            now_string()
        )


    task.updated_at = (
        now_string()
    )


    AGENT_RUNTIME.mkdir(
        parents=True,
        exist_ok=True,
    )


    CURRENT_TASK_FILE.write_text(
        json.dumps(
            task_to_dict(
                task
            ),

            indent=2,

            ensure_ascii=False,

            default=str,
        ),

        encoding="utf-8",
    )


    return task


# ---------------------------------------------------------------------------
# Load Step
# ---------------------------------------------------------------------------

def load_step(
    data: dict,
    fallback_number: int,
):
    """
    Reconstructs one AgentStep from persisted JSON data.
    """

    return AgentStep(
        step_number=
            data.get(
                "step_number",
                fallback_number,
            ),

        description=
            data.get(
                "description",
                "",
            ),

        tool_name=
            data.get(
                "tool_name",
                "",
            ),

        arguments=
            data.get(
                "arguments",
                {},
            ),

        status=
            data.get(
                "status",
                "pending",
            ),

        attempts=
            data.get(
                "attempts",
                0,
            ),

        result=
            data.get(
                "result"
            ),

        error=
            data.get(
                "error"
            ),
    )


# ---------------------------------------------------------------------------
# Load Task
# ---------------------------------------------------------------------------

def load_task():
    """
    Restores the current Phase 7 task.

    Returns None when:
        - no task file exists
        - the task file cannot be decoded safely
    """

    if not CURRENT_TASK_FILE.exists():

        return None


    try:

        raw = (
            CURRENT_TASK_FILE
            .read_text(
                encoding="utf-8"
            )
        )


        data = json.loads(
            raw
        )


    except (
        OSError,
        json.JSONDecodeError,
    ):

        return None


    if not isinstance(
        data,
        dict,
    ):

        return None


    raw_steps = data.get(
        "steps",
        [],
    )


    steps = []


    if isinstance(
        raw_steps,
        list,
    ):

        for index, item in enumerate(
            raw_steps,
            start=1,
        ):

            if not isinstance(
                item,
                dict,
            ):

                continue


            steps.append(
                load_step(
                    item,
                    fallback_number=index,
                )
            )


    return AgentTask(
        goal=
            data.get(
                "goal",
                "",
            ),

        steps=
            steps,

        workspace_path=
            data.get(
                "workspace_path"
            ),

        status=
            data.get(
                "status",
                "planned",
            ),

        current_step_index=
            data.get(
                "current_step_index",
                0,
            ),

        total_executions=
            data.get(
                "total_executions",
                0,
            ),

        replan_count=
            data.get(
                "replan_count",
                0,
            ),

        continuation_count=
            data.get(
                "continuation_count",
                0,
            ),

        pending_action=
            data.get(
                "pending_action"
            ),

        final_summary=
            data.get(
                "final_summary",
                "",
            ),

        created_at=
            data.get(
                "created_at",
                "",
            ),

        updated_at=
            data.get(
                "updated_at",
                "",
            ),
    )


# ---------------------------------------------------------------------------
# Clear Task
# ---------------------------------------------------------------------------

def clear_task():
    """
    Deletes the persisted active-task state.
    """

    if not CURRENT_TASK_FILE.exists():

        return False


    try:

        CURRENT_TASK_FILE.unlink()

        return True


    except OSError:

        return False


# ---------------------------------------------------------------------------
# Task Exists
# ---------------------------------------------------------------------------

def task_exists():
    """
    Returns True when a persisted task file exists.
    """

    return (
        CURRENT_TASK_FILE.exists()
    )


# ---------------------------------------------------------------------------
# Active Task
# ---------------------------------------------------------------------------

def has_active_task():
    """
    Returns True only for unfinished tasks that may still be resumed.
    """

    task = load_task()


    if task is None:

        return False


    return task.status not in {
        "completed",
        "cancelled",
        "failed",
    }


# ---------------------------------------------------------------------------
# Waiting For Approval
# ---------------------------------------------------------------------------

def task_waiting_for_approval():
    """
    Returns True when the current Phase 7 task is paused at a
    Phase 6 permission boundary.
    """

    task = load_task()


    if task is None:

        return False


    return (
        task.status
        == "awaiting_approval"
        and task.pending_action
        is not None
    )


# ---------------------------------------------------------------------------
# Current Step
# ---------------------------------------------------------------------------

def get_current_step(
    task: AgentTask,
):
    """
    Returns the current AgentStep or None when the currently known
    plan has finished.
    """

    if (
        task.current_step_index
        < 0
    ):

        return None


    if (
        task.current_step_index
        >= len(
            task.steps
        )
    ):

        return None


    return task.steps[
        task.current_step_index
    ]


# ---------------------------------------------------------------------------
# State Summary
# ---------------------------------------------------------------------------

def summarize_task(
    task: AgentTask,
):
    """
    Returns a concise diagnostic representation of task state.
    """

    return {
        "goal":
            task.goal,

        "status":
            task.status,

        "workspace_path":
            task.workspace_path,

        "current_step_index":
            task.current_step_index,

        "step_count":
            len(
                task.steps
            ),

        "total_executions":
            task.total_executions,

        "replan_count":
            task.replan_count,

        "continuation_count":
            task.continuation_count,

        "waiting_for_approval":
            (
                task.pending_action
                is not None
            ),

        "created_at":
            task.created_at,

        "updated_at":
            task.updated_at,
    }


# ---------------------------------------------------------------------------
# Standalone Test
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    print(
        "E.V.I.E. Agent State"
    )

    print(
        "---------------------"
    )


    print(
        "State file:"
    )

    print(
        CURRENT_TASK_FILE
    )


    print()


    task = load_task()


    if task is None:

        print(
            "No persistent agent task."
        )


    else:

        summary = summarize_task(
            task
        )


        print(
            "Goal:",
            summary[
                "goal"
            ],
        )


        print(
            "Status:",
            summary[
                "status"
            ],
        )


        print(
            "Workspace:",
            summary[
                "workspace_path"
            ],
        )


        print(
            "Current step index:",
            summary[
                "current_step_index"
            ],
        )


        print(
            "Steps:",
            summary[
                "step_count"
            ],
        )


        print(
            "Executions:",
            summary[
                "total_executions"
            ],
        )


        print(
            "Replans:",
            summary[
                "replan_count"
            ],
        )


        print(
            "Continuations:",
            summary[
                "continuation_count"
            ],
        )


        print(
            "Waiting for approval:",
            summary[
                "waiting_for_approval"
            ],
        )


        current = get_current_step(
            task
        )


        if current is not None:

            print()

            print(
                "Current step:"
            )

            print(
                current
            )