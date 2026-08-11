"""
E.V.I.E. - Workflow Replanner

Phase 11D

Purpose:
Build a bounded repair proposal for a failed workflow step without
changing the original workflow goal or bypassing Phase 6 permissions.

Important:
- Phase 11 owns workflow state.
- This module only proposes a repair.
- The repaired step still executes through the normal workflow engine.
- The workflow goal is immutable.
- E.V.I.E.'s reasoning stack is loaded lazily only when replanning
  is actually required.
"""

from __future__ import annotations

import json

from pydantic import (
    BaseModel,
    Field,
)

from assistant.tools.registry import (
    list_tools,
    load_default_tools,
)

from assistant.intelligence.integration_runtime import (
    prepare_tool_arguments,
)


# ---------------------------------------------------------------------------
# Prompt
# ---------------------------------------------------------------------------

REPLANNER_SYSTEM_PROMPT = """
You are E.V.I.E.'s Phase 11 workflow repair planner.

Your job is to repair ONE FAILED WORKFLOW STEP while preserving the
original workflow goal.

You are NOT allowed to redesign the whole workflow.

You receive:
- original workflow goal
- failed step description
- failed tool
- failed arguments
- failure message
- existing workflow outputs
- available tools

Return one of:

1. retry
   Use when the same tool/arguments should simply be tried again.

2. replace
   Use when the failed step should be replaced with a safer or corrected
   tool call that still serves the SAME step objective.

3. request_user
   Use when a user must reconnect/authenticate, provide missing
   information, or make a decision.

4. stop
   Use when no safe bounded repair is possible.

Rules:

- Never change the workflow goal.
- Never add approval flags.
- Never bypass permissions.
- Never invent credentials or accounts.
- Never create destructive actions unless the failed step itself was
  already explicitly destructive and authorized.
- Prefer the smallest repair.
- Return exactly one repair action.
"""


# ---------------------------------------------------------------------------
# Structured Response
# ---------------------------------------------------------------------------

class WorkflowRepairPlan(
    BaseModel
):

    action: str = Field(
        description=(
            "retry, replace, request_user, or stop"
        )
    )

    reason: str = ""

    tool_name: str = ""

    arguments_json: str = "{}"

    user_message: str = ""


# ---------------------------------------------------------------------------
# Available Tools
# ---------------------------------------------------------------------------

def _available_tools_text():

    load_default_tools()


    tools = (
        list_tools()
    )


    lines = []


    for tool in tools:

        lines.append(
            (
                f"- {tool.name}: "
                f"{tool.description}"
            )
        )


    return "\n".join(
        lines
    )


# ---------------------------------------------------------------------------
# Lazy Reasoning Client
# ---------------------------------------------------------------------------

def _get_reasoning_client():
    """
    Import E.V.I.E.'s reasoning stack only if replanning is genuinely
    required.

    This prevents lightweight processes such as the Phase 11 scheduler
    from loading semantic-memory / transformer models during startup.
    """

    from assistant.brain import (
        client,
    )


    return client


# ---------------------------------------------------------------------------
# Repair
# ---------------------------------------------------------------------------

def propose_workflow_repair(
    run,
    step,
):

    prompt = (
        "ORIGINAL WORKFLOW GOAL:\n"
        f"{run.goal}\n\n"

        "FAILED STEP:\n"
        f"{step.description}\n\n"

        "FAILED TOOL:\n"
        f"{step.tool_name}\n\n"

        "FAILED ARGUMENTS:\n"
        f"{json.dumps(step.arguments, default=str)}\n\n"

        "FAILURE:\n"
        f"{step.error or ''}\n\n"

        "CURRENT WORKFLOW OUTPUTS:\n"
        f"{json.dumps(run.outputs, default=str)}\n\n"

        "AVAILABLE TOOLS:\n"
        f"{_available_tools_text()}"
    )


    client = (
        _get_reasoning_client()
    )


    response = (
        client.responses.parse(
            model="gpt-5.2",

            instructions=
                REPLANNER_SYSTEM_PROMPT,

            input=
                prompt,

            text_format=
                WorkflowRepairPlan,
        )
    )


    repair = (
        response.output_parsed
    )


    action = (
        str(
            repair.action
            or ""
        )
        .strip()
        .lower()
    )


    if action not in {
        "retry",
        "replace",
        "request_user",
        "stop",
    }:

        action = (
            "stop"
        )


    arguments = {}


    if (
        repair.arguments_json
        and action
        == "replace"
    ):

        try:

            parsed = (
                json.loads(
                    repair.arguments_json
                )
            )


            if isinstance(
                parsed,
                dict,
            ):

                arguments = (
                    parsed
                )


        except json.JSONDecodeError:

            arguments = {}


    if (
        action
        == "replace"
        and repair.tool_name
    ):

        arguments = (
            prepare_tool_arguments(
                repair.tool_name,
                arguments,
            )
        )


    return {
        "action":
            action,

        "reason":
            str(
                repair.reason
                or ""
            ),

        "tool_name":
            str(
                repair.tool_name
                or ""
            ),

        "arguments":
            arguments,

        "user_message":
            str(
                repair.user_message
                or ""
            ),
    }