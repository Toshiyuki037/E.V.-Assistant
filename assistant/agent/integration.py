"""
E.V.I.E. - Agent Runtime Integration

Created: August 9, 2026
Last Edited: August 12, 2026
Author: Max Maehara

Purpose:
    Connects Phase 7 task execution to E.V.I.E.'s normal prompt loop.

Phase 14A:
    Adds a cheap deterministic fast gate so obviously non-agentic
    requests do not pay for the expensive Phase 7 planner.

Important:
    Existing active tasks and approval continuations ALWAYS bypass
    the fast gate so pending Phase 7 state is preserved.
"""

from __future__ import annotations

import re


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
# Phase 14A - Cheap Agent Gate
# ---------------------------------------------------------------------------

_AGENTIC_PHRASES = (
    " and then ",
    " then ",
    " after that ",
    " once that ",
    " when that ",
    " if it fails",
    " if that fails",
    " if this fails",
    " if necessary",
    " keep trying",
    " keep working",
    " until it works",
    " until it succeeds",
    " until successful",
    " debug it",
    " fix it",
    " repair it",
    " investigate",
    " diagnose",
    " verify that",
    " verify it",
    " run the tests",
    " run tests",
    " full regression",
    " regression suite",
    " inspect the changes",
    " inspect current",
    " commit everything",
    " stage all",
)


_MULTI_ACTION_VERBS = (
    "open",
    "launch",
    "focus",
    "move",
    "maximize",
    "minimize",
    "close",
    "type",
    "write",
    "copy",
    "save",
    "create",
    "delete",
    "rename",
    "run",
    "test",
    "search",
    "find",
    "inspect",
    "read",
    "commit",
    "stage",
    "push",
    "navigate",
    "click",
    "fill",
)


def should_consider_agent(
    user_message: str,
) -> bool:
    """
    Cheap pre-planner gate.

    Returns True only when the message has meaningful evidence of
    a multi-step, sequential, adaptive, or compound computer task.

    This function intentionally does NOT decide the final Phase 7 plan.
    It only determines whether invoking the expensive Phase 7 planner
    is justified.
    """

    text = (
        str(
            user_message
            or ""
        )
        .strip()
    )

    if not text:
        return False


    normalized = (
        " "
        + re.sub(
            r"\s+",
            " ",
            text.lower(),
        )
        + " "
    )


    # -----------------------------------------------------------------------
    # Strong Adaptive / Sequential Signals
    # -----------------------------------------------------------------------

    if any(
        phrase in normalized
        for phrase in _AGENTIC_PHRASES
    ):
        return True


    # -----------------------------------------------------------------------
    # Multiple Explicit Action Clauses
    # -----------------------------------------------------------------------

    action_hits = 0

    for verb in _MULTI_ACTION_VERBS:

        if re.search(
            rf"\b{re.escape(verb)}\b",
            normalized,
        ):
            action_hits += 1


    if (
        action_hits >= 2
        and (
            " and " in normalized
            or "," in normalized
            or ";" in normalized
        )
    ):
        return True


    # -----------------------------------------------------------------------
    # Common Explicit Agentic Forms
    # -----------------------------------------------------------------------

    if re.search(
        r"\b(open|launch|run|create|write|search|find|inspect)\b"
        r".+\b(and|then)\b"
        r".+\b(open|launch|run|create|write|search|find|inspect|verify)\b",
        normalized,
    ):
        return True


    # -----------------------------------------------------------------------
    # Otherwise let Phase 6 / memory / reasoning handle it.
    # -----------------------------------------------------------------------

    return False


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

    When handled=False, main.py continues through normal
    Phase 6 / memory / brain routing.
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

        result = (
            cancel_agent()
        )

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

        result = (
            resume_agent()
        )

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

            result = (
                resume_agent()
            )

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
    # Phase 14A Fast Gate
    # -----------------------------------------------------------------------
    #
    # No active task exists.
    #
    # Avoid invoking the expensive Phase 7 planner when the message
    # clearly does not describe a multi-step/adaptive task.
    # -----------------------------------------------------------------------

    if not should_consider_agent(
        user_message
    ):

        return {
            "handled":
                False,

            "response":
                None,

            "follow_up":
                "",
        }


    # -----------------------------------------------------------------------
    # New Phase 7 Request
    # -----------------------------------------------------------------------

    result = (
        execute_agent_request(
            user_message
        )
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