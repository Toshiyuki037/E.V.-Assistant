"""
E.V.I.E. - Agent Controller

Created: August 9, 2026
Last Edited: August 9, 2026
Author: Max Maehara

Purpose:
    High-level Phase 7 interface used by main.py.
"""

from .planner import (
    plan_task,
)

from .runner import (
    cancel_agent_task,
    format_agent_result,
    resolve_agent_approval,
    resume_agent_task,
    run_agent_task,
)

from .state import (
    has_active_task,
    load_task,
)


# ---------------------------------------------------------------------------
# Detect
# ---------------------------------------------------------------------------

def should_use_agent(
    user_message: str,
):
    plan = plan_task(
        user_message
    )

    return (
        plan.use_agent,
        plan,
    )


# ---------------------------------------------------------------------------
# Start
# ---------------------------------------------------------------------------

def execute_agent_request(
    user_message: str,
):
    result = run_agent_task(
        user_message
    )

    return {
        "handled":
            (
                result.status
                != "not_agent_task"
            ),

        "result":
            result,

        "response":
            format_agent_result(
                result
            ),
    }


# ---------------------------------------------------------------------------
# Approval
# ---------------------------------------------------------------------------

def approve_agent_action():
    result = resolve_agent_approval(
        True
    )

    return {
        "handled":
            True,

        "result":
            result,

        "response":
            format_agent_result(
                result
            ),
    }


def reject_agent_action():
    result = resolve_agent_approval(
        False
    )

    return {
        "handled":
            True,

        "result":
            result,

        "response":
            format_agent_result(
                result
            ),
    }


# ---------------------------------------------------------------------------
# Resume
# ---------------------------------------------------------------------------

def resume_agent():
    result = resume_agent_task()

    return {
        "handled":
            True,

        "result":
            result,

        "response":
            format_agent_result(
                result
            ),
    }


# ---------------------------------------------------------------------------
# Cancel
# ---------------------------------------------------------------------------

def cancel_agent():
    result = cancel_agent_task()

    return {
        "handled":
            True,

        "result":
            result,

        "response":
            format_agent_result(
                result
            ),
    }


# ---------------------------------------------------------------------------
# Active State
# ---------------------------------------------------------------------------

def agent_task_active():
    return has_active_task()


def get_agent_task():
    return load_task()