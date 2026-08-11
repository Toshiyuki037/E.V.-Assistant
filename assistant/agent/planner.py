"""
E.V.I.E. - Agent Planner

Created: August 9, 2026
Last Edited: August 9, 2026
Author: Max Maehara

Purpose:
    Determines whether a request requires Phase 7 agentic execution
    and creates a bounded execution plan using registered Phase 6 tools.

Capabilities:
    - distinguishes normal reasoning from computer actions
    - distinguishes single-tool actions from multi-step tasks
    - supports adaptive / iterative tasks
    - uses exact registered tool signatures
    - creates bounded plans
    - preserves Phase 6 permission boundaries

Important:
    This module PLANS only.

    It does not execute tools.

Most Recent Change:
    Added adaptive task routing so requests such as
    "run this and fix it if it fails" correctly enter Phase 7
    even when only one initial action is known.
"""

import inspect
import json

from dotenv import load_dotenv
from openai import OpenAI

from pydantic import (
    BaseModel,
    Field,
)

from assistant.tools.registry import (
    list_tools,
    load_default_tools,
)

from assistant.intelligence.integration_runtime import (
    prepare_integration_arguments,
)

from assistant.intelligence.normalize import (
    normalize_user_input,
)

from .models import (
    AgentPlan,
    AgentStep,
)


# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------

load_dotenv()

client = OpenAI()


# ---------------------------------------------------------------------------
# Limits
# ---------------------------------------------------------------------------

MAX_INITIAL_STEPS = 8


# ---------------------------------------------------------------------------
# Structured Output
# ---------------------------------------------------------------------------

class PlannedStep(BaseModel):
    description: str

    tool_name: str

    arguments_json: str = "{}"


class PlannerResponse(BaseModel):
    use_agent: bool

    confidence: int = Field(
        default=0,
        ge=0,
        le=100,
    )

    summary: str = ""

    steps: list[
        PlannedStep
    ] = Field(
        default_factory=list
    )


# ---------------------------------------------------------------------------
# Planner Instructions
# ---------------------------------------------------------------------------

PLANNER_SYSTEM_PROMPT = """
You are E.V.I.E.'s Phase 7 agentic task planner.

E.V.I.E. already has Phase 6 for simple single computer actions.

Your job is to decide whether the user's request requires Phase 7
agentic execution.


PHASE 7 SHOULD BE USED WHEN:

- two or more meaningful computer actions are required
- actions must happen in sequence
- later actions depend on earlier results
- the user asks E.V.I.E. to create, modify, test, inspect, and verify
- the user asks E.V.I.E. to investigate a failure
- the user asks E.V.I.E. to retry or keep working until success
- the task is adaptive or iterative
- the next action cannot be known until a real execution result exists
- the user asks for two or more independent connected-service actions
  in one request
- the user combines information from multiple connected providers
- the user asks for multiple independent integration capabilities even
  when the actions do not depend on each other


DO NOT USE PHASE 7 FOR:

- ordinary conversation
- arithmetic
- general knowledge questions
- one Git command
- one file open
- one application launch
- one URL open
- one simple read-only computer action


GENERAL RULES:

1. Use only registered E.V.I.E. tools.

2. Never invent a tool name.

3. Create the smallest useful plan.

4. Maximum eight initial steps.

5. Each planned step should perform ONE meaningful computer action.

6. Never bypass Phase 6 permissions.

7. Prefer dedicated tools over run_command.

8. Prefer inspection before modification when investigation is needed.

9. Do not invent tool results.

10. Do not assume future steps succeed.

11. Do not include conversational responses as plan steps.

12. Preserve the user's requested ordering.

13. Do not automatically commit or push unless the user explicitly asks.

14. When creating source code, include the COMPLETE intended file
    contents in the create_file or write_file content argument.

15. create_file may create parent directories automatically, so do not
    add unnecessary directory-creation steps.

16. For Python execution, prefer run_python.

17. Do NOT create conditional plan steps such as:

        "If execution fails, inspect the file."

    Conditional behavior belongs to the Phase 7 recovery controller.

18. Do NOT add a separate verification step merely to inspect stdout.

    The final Phase 7 verifier receives real tool results automatically.


PROJECT KNOWLEDGE QUESTIONS:

Do NOT use Phase 7 merely because the user asks where code is located,
how part of the current project works, what a file does, or where a
function/class is implemented.

Examples that should normally use_agent = false:

- "Where is memory retrieval implemented?"
- "What does assistant/tools/terminal.py do?"
- "Where is the Phase 7 planner?"
- "Explain the memory system."
- "What file handles screen capture?"

E.V.I.E. already has project knowledge retrieval for these questions.

Use Phase 7 only when the user explicitly asks E.V.I.E. to perform
computer actions such as opening, editing, executing, searching the
live filesystem when indexed knowledge is insufficient, testing,
debugging, or modifying something.

TOOL ARGUMENT CONTRACTS:

The registered tool descriptions include the exact Python signatures.

You MUST use parameter names from those signatures exactly.

Never invent argument names.

Example:

If the registered signature is:

run_python(
    arguments=None,
    cwd=".",
    workspace_path=None,
    timeout=60
)

and the user wants to run:

TypewriterTest/typewriter.py

the correct arguments are:

{
    "arguments": [
        "TypewriterTest/typewriter.py"
    ]
}

NOT:

{
    "path": "TypewriterTest/typewriter.py"
}


Another example:

If the tool signature is:

open_file_in_vscode(
    path,
    line=None,
    workspace_path=None,
    new_window=False
)

and the user asks for a new VS Code window:

{
    "path": "TypewriterTest/typewriter.py",
    "new_window": true
}


ADAPTIVE / ITERATIVE TASKS:

Phase 7 MUST also be used when the request contains adaptive behavior,
even when only ONE immediate action is known initially.

Examples:

- "Run this and fix it if it fails."
- "Debug this until it works."
- "Run the tests and investigate any failures."
- "Try this and correct whatever goes wrong."
- "Keep working until it succeeds."
- "Run it, inspect errors, fix them, and rerun."
- "Verify the result and repair problems if necessary."
- "Run this script and keep debugging until it exits successfully."

These are Phase 7 tasks because the next actions depend on REAL results.

For adaptive tasks it is valid for the INITIAL plan to contain only
one step.

Example:

User:

Run TypewriterTest/typewriter.py. If it fails, debug it until it works.

Correct initial plan:

1. run_python

Do NOT pre-plan a specific repair.

Do NOT assume what the error will be.

The recovery controller will inspect the real stderr/stdout and create
new corrective steps dynamically.


PHASE 10 MULTI-INTENT CONNECTED SERVICES:

Multiple independent connected-service requests in one user message
belong to Phase 7.

Each requested connected-service capability becomes its own
integration_execute step.

Example:

User:

    Check the weather in Honolulu and show my latest GitHub commits
    to E.V.-Assistant.

Correct plan:

Step 1:
    Tool:
        integration_execute

    Arguments:
        {
            "capability": "weather.current",
            "provider": "weather",
            "account_id": "public",
            "routing_mode": "explicit_account",
            "arguments": {
                "location": "Honolulu"
            }
        }

Step 2:
    Tool:
        integration_execute

    Arguments:
        {
            "capability": "github.commits",
            "provider": "github",
            "account_id": "primary",
            "routing_mode": "explicit_account",
            "arguments": {
                "repo": "E.V.-Assistant"
            }
        }

Another example:

User:

    Show my latest commits and open issues for E.V.-Assistant.

Correct plan:

Step 1:
    integration_execute
    capability = github.commits

Step 2:
    integration_execute
    capability = github.issues

Both steps preserve:
    provider = github
    account_id = primary
    routing_mode = explicit_account
    arguments.repo = E.V.-Assistant


PHASE 10 MULTI-INTENT RULES:

1. Each integration_execute step performs exactly one capability.

2. Use canonical registered capability names when possible.

3. Never combine multiple capabilities into one integration_execute call.

4. Never bypass Phase 6 permissions.

5. Never include or invent an approved argument.

6. Do not invent accounts.

7. Preserve explicit entities such as repository, location, page title,
   section, symbol, dates, and account identifiers.

8. Multiple independent connected-service reads are Phase 7 even when
   the second read does not depend on the first.

9. Use the smallest number of steps required.

10. The final verifier should synthesize all successful integration
    results into one user-facing answer.



MULTI-STEP EXAMPLE:

User:

Create TypewriterTest/typewriter.py, open it in a new VS Code window,
and run it.

Correct Phase 7 plan:

Step 1:
    Tool:
        create_file

    Arguments:
        {
            "path":
                "TypewriterTest/typewriter.py",

            "content":
                "<complete Python source>"
        }

Step 2:
    Tool:
        open_file_in_vscode

    Arguments:
        {
            "path":
                "TypewriterTest/typewriter.py",

            "new_window":
                true
        }

Step 3:
    Tool:
        run_python

    Arguments:
        {
            "arguments":
                [
                    "TypewriterTest/typewriter.py"
                ]
        }

use_agent = true


SINGLE ACTION EXAMPLE:

User:

Show me my Git status.

Only one direct action is needed:

git_status

Therefore:

use_agent = false


NO COMPUTER ACTION EXAMPLE:

User:

What's 2 + 2?

Therefore:

use_agent = false
"""


# ---------------------------------------------------------------------------
# Tool Description
# ---------------------------------------------------------------------------

def describe_agent_tools():
    """
    Returns registered Phase 6 tools with their exact callable
    signatures.

    This prevents the planner from inventing argument names.
    """

    load_default_tools()

    blocks = []


    for tool in list_tools():

        try:

            signature = inspect.signature(
                tool.function
            )

        except (
            TypeError,
            ValueError,
        ):

            signature = (
                "(signature unavailable)"
            )


        blocks.append(
            (
                f"Tool: {tool.name}\n"
                f"Category: {tool.category}\n"
                f"Risk: {tool.risk}\n"
                f"Signature: "
                f"{tool.name}{signature}\n"
                f"Description: "
                f"{tool.description}"
            )
        )


    return "\n\n".join(
        blocks
    )


# ---------------------------------------------------------------------------
# Parse Arguments
# ---------------------------------------------------------------------------

def parse_arguments(
    arguments_json: str,
):
    """
    Converts structured planner JSON into a Python dictionary.

    Invalid JSON safely becomes an empty dictionary.
    """

    if not arguments_json:

        return {}


    try:

        arguments = json.loads(
            arguments_json
        )

    except json.JSONDecodeError:

        return {}


    if not isinstance(
        arguments,
        dict,
    ):

        return {}


    return arguments


# ---------------------------------------------------------------------------
# Registered Tool Validation
# ---------------------------------------------------------------------------

def get_registered_tool_names():
    """
    Returns the currently registered tool names.
    """

    load_default_tools()

    return {
        tool.name
        for tool
        in list_tools()
    }


def tool_name_exists(
    tool_name: str,
):
    """
    Prevents a hallucinated tool from entering an AgentPlan.
    """

    return (
        tool_name
        in get_registered_tool_names()
    )


# ---------------------------------------------------------------------------
# Plan Task
# ---------------------------------------------------------------------------

def plan_task(
    user_message: str,
):
    """
    Converts a natural-language user goal into an AgentPlan.

    Outcomes:

        use_agent=False
            Normal reasoning or Phase 6 should handle the request.

        use_agent=True
            Phase 7 should take ownership of the goal.

    Adaptive Phase 7 plans may contain only one INITIAL step because
    additional steps are generated after real execution results.
    """

    load_default_tools()


    user_message = (
        user_message.strip()
    )


    if not user_message:

        return AgentPlan(
            goal="",

            use_agent=False,

            confidence=100,

            summary=(
                "No user request was provided."
            ),
        )


    # -----------------------------------------------------------------------
    # Phase 10D - Normalize User Input
    # -----------------------------------------------------------------------

    normalized_user_message = (
        normalize_user_input(
            user_message
        )
    )


    prompt = (
        f"{PLANNER_SYSTEM_PROMPT}\n\n"

        "REGISTERED TOOL CONTRACTS:\n\n"

        f"{describe_agent_tools()}\n\n"

        "USER GOAL:\n"

        f"{normalized_user_message}"
    )


    try:

        response = (
            client.responses.parse(
                model=
                    "gpt-5.5",

                instructions=(
                    "Determine whether this is "
                    "a Phase 7 agentic task and "
                    "create the smallest valid "
                    "initial execution plan."
                ),

                input=
                    prompt,

                text_format=
                    PlannerResponse,
            )
        )


        parsed = (
            response.output_parsed
        )


    except Exception as error:

        return AgentPlan(
            goal=
                user_message,

            use_agent=False,

            confidence=0,

            summary=(
                "Agent planning failed: "
                f"{error}"
            ),
        )


    if parsed is None:

        return AgentPlan(
            goal=
                user_message,

            use_agent=False,

            confidence=0,

            summary=(
                "Agent planner returned "
                "no structured result."
            ),
        )


    # -----------------------------------------------------------------------
    # Phase 7 Not Required
    # -----------------------------------------------------------------------

    if not parsed.use_agent:

        return AgentPlan(
            goal=
                user_message,

            use_agent=False,

            confidence=
                parsed.confidence,

            summary=
                parsed.summary,
        )


    # -----------------------------------------------------------------------
    # Convert Planned Steps
    # -----------------------------------------------------------------------

    steps = []


    for planned in parsed.steps[
        :MAX_INITIAL_STEPS
    ]:

        tool_name = (
            planned.tool_name
            .strip()
            .lower()
        )


        if not tool_name_exists(
            tool_name
        ):

            continue


        arguments = (
            parse_arguments(
                planned.arguments_json
            )
        )


        # -------------------------------------------------------------------
        # Phase 10A / 10E - Prepare Integration Arguments
        # -------------------------------------------------------------------

        if (
            tool_name
            == "integration_execute"
        ):

            arguments = (
                prepare_integration_arguments(
                    arguments
                )
            )


        steps.append(
            AgentStep(
                step_number=
                    len(steps)
                    + 1,

                description=
                    planned.description,

                tool_name=
                    tool_name,

                arguments=
                    arguments,
            )
        )


    # -----------------------------------------------------------------------
    # Agent Needs At Least One Initial Action
    # -----------------------------------------------------------------------
    #
    # IMPORTANT:
    #
    # We intentionally DO NOT require two initial steps.
    #
    # Adaptive tasks may begin with:
    #
    #     run_python
    #
    # and dynamically create additional steps only after observing
    # the real result.
    # -----------------------------------------------------------------------

    if not steps:

        return AgentPlan(
            goal=
                user_message,

            use_agent=False,

            confidence=
                parsed.confidence,

            summary=(
                "No valid initial "
                "computer action was planned."
            ),
        )


    # -----------------------------------------------------------------------
    # Return Agent Plan
    # -----------------------------------------------------------------------

    return AgentPlan(
        goal=
            user_message,

        use_agent=True,

        steps=
            steps,

        confidence=
            parsed.confidence,

        summary=
            parsed.summary,
    )


# ---------------------------------------------------------------------------
# Format Plan
# ---------------------------------------------------------------------------

def format_plan(
    plan: AgentPlan,
):
    """
    Creates readable terminal output for Phase 7 debugging.
    """

    lines = [
        (
            f"Goal: "
            f"{plan.goal}"
        ),

        (
            f"Use agent: "
            f"{plan.use_agent}"
        ),

        (
            f"Confidence: "
            f"{plan.confidence}"
        ),
    ]


    if plan.summary:

        lines.append(
            (
                f"Summary: "
                f"{plan.summary}"
            )
        )


    if plan.steps:

        lines.append(
            ""
        )

        lines.append(
            "Steps:"
        )


        for step in plan.steps:

            lines.append(
                (
                    f"{step.step_number}. "
                    f"{step.description}"
                )
            )


            lines.append(
                (
                    "   Tool: "
                    f"{step.tool_name}"
                )
            )


            lines.append(
                (
                    "   Arguments: "
                    f"{step.arguments}"
                )
            )


    return "\n".join(
        lines
    )


# ---------------------------------------------------------------------------
# Standalone Test
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    print(
        "E.V.I.E. Agent Planner"
    )

    print(
        "-----------------------"
    )


    tests = (
        "What's 2 + 2?",

        "Show me my Git status.",

        (
            "Open my E.V.I.E. project "
            "in VS Code and then show "
            "me its Git status."
        ),

        (
            "Create TypewriterTest/"
            "typewriter.py with a Python "
            "script that prints "
            "\"Hello from E.V.I.E.\" "
            "one character at a time with "
            "random delays, open it in a "
            "new VS Code window, then run it."
        ),

        (
            "Run TypewriterTest/typewriter.py. "
            "If it fails, inspect the actual "
            "error and the file, determine "
            "what is wrong, fix the code, "
            "rerun it, and continue debugging "
            "until it exits successfully and "
            "prints exactly Hello from E.V.I.E.. "
            "Verify the final result."
        ),
    )


    for message in tests:

        print()

        print(
            "User:",
            message,
        )


        plan = plan_task(
            message
        )


        print(
            format_plan(
                plan
            )
        )