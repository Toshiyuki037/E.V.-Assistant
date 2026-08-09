"""
E.V.I.E. - Agent Runtime Integration

Created: August 9, 2026
Last Edited: August 9, 2026
Author: Max Maehara

Purpose:
    Connects Phase 7 task execution to E.V.I.E.'s normal prompt loop.

This module:
    - handles pending Phase 7 approvals
    - supports cancellation
    - supports resume
    - starts new multi-step tasks
    - leaves ordinary / single-tool requests alone
"""

from assistant.tools.session import (
    parse_approval_response,
)

from .controller import (
    agent_task_active,
    approve_agent_action,
    cancel_agent,
    execute_agent_request,
    get_agent_task,
    reject_agent_action,
    resume_agent,
)


# ---------------------------------------------------------------------------
# Command Detection
# ---------------------------------------------------------------------------

def is_cancel_request(
    text: str,
):
    normalized = (
        text
        .strip()
        .lower()
    )

    return normalized in {
        "cancel task",
        "cancel the task",
        "stop task",
        "stop the task",
        "stop working on that",
        "abort task",
        "abort the task",
    }


def is_resume_request(
    text: str,
):
    normalized = (
        text
        .strip()
        .lower()
    )

    return normalized in {
        "resume task",
        "resume the task",
        "continue task",
        "continue the task",
        "keep going",
        "continue",
    }


# ---------------------------------------------------------------------------
# Handle Agent Message
# ---------------------------------------------------------------------------

def handle_agent_message(
    user_message: str,
):
    """
    Returns:

        {
            "handled": bool,
            "response": str | None,
        }

    When handled=False, main.py should continue through the
    normal Phase 6 / memory / brain flow.
    """

    task = get_agent_task()


    # -----------------------------------------------------------------------
    # Existing Task Awaiting Approval
    # -----------------------------------------------------------------------

    if (
        task is not None
        and task.status
        == "awaiting_approval"
    ):

        approval = (
            parse_approval_response(
                user_message
            )
        )

        if approval.decision == "approve":

            result = (
                approve_agent_action()
            )

            return {
                "handled":
                    True,

                "response":
                    result[
                        "response"
                    ],

                "follow_up":
                    approval.remainder,
            }

        if approval.decision == "reject":

            result = (
                reject_agent_action()
            )

            return {
                "handled":
                    True,

                "response":
                    result[
                        "response"
                    ],

                "follow_up":
                    approval.remainder,
            }


    # -----------------------------------------------------------------------
    # Cancel
    # -----------------------------------------------------------------------

    if (
        agent_task_active()
        and is_cancel_request(
            user_message
        )
    ):

        result = cancel_agent()

        return {
            "handled":
                True,

            "response":
                result[
                    "response"
                ],

            "follow_up":
                "",
        }


    # -----------------------------------------------------------------------
    # Resume
    # -----------------------------------------------------------------------

    if (
        agent_task_active()
        and is_resume_request(
            user_message
        )
    ):

        result = resume_agent()

        return {
            "handled":
                True,

            "response":
                result[
                    "response"
                ],

            "follow_up":
                "",
        }


    # -----------------------------------------------------------------------
    # Existing Non-Approval Task
    # -----------------------------------------------------------------------

    if agent_task_active():

        task = get_agent_task()

        if task.status in {
            "running",
            "planned",
            "incomplete",
        }:

            result = resume_agent()

            return {
                "handled":
                    True,

                "response":
                    result[
                        "response"
                    ],

                "follow_up":
                    user_message,
            }


    # -----------------------------------------------------------------------
    # New Phase 7 Request
    # -----------------------------------------------------------------------

    result = execute_agent_request(
        user_message
    )

    if not result[
        "handled"
    ]:

        return {
            "handled":
                False,

            "response":
                None,

            "follow_up":
                "",
        }

    return {
        "handled":
            True,

        "response":
            result[
                "response"
            ],

        "follow_up":
            "",
    }