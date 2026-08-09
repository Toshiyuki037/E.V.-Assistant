"""
E.V.I.E. - Agent Verifier

Created: August 9, 2026
Last Edited: August 9, 2026
Author: Max Maehara

Purpose:
    Provides Phase 7 execution verification, failure recovery,
    dynamic continuation planning, and final goal verification.

Capabilities:
    - deterministic Phase 6 result verification
    - stdout / stderr inspection
    - exact tool-signature awareness
    - failed-step recovery
    - dynamic continuation after successful investigative steps
    - final goal completion verification

Important:
    This module NEVER executes tools.

    It only interprets real execution results and determines
    what the agent should do next.

Most Recent Change:
    Added continuation planning so successful investigative actions
    can generate additional steps when the original goal is not yet
    complete.
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

from assistant.tools.verifier import (
    verify_tool_result as
    verify_phase6_tool_result,
)

from .models import (
    AgentStep,
    AgentTask,
)


# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------

load_dotenv()

client = OpenAI()


# ---------------------------------------------------------------------------
# Structured Models
# ---------------------------------------------------------------------------

class PlannedAgentStep(BaseModel):
    description: str

    tool_name: str

    arguments_json: str = "{}"


class RecoveryDecision(BaseModel):
    action: str

    reason: str = ""

    next_steps: list[
        PlannedAgentStep
    ] = Field(
        default_factory=list
    )


class ContinuationDecision(BaseModel):
    complete: bool

    reason: str = ""

    next_steps: list[
        PlannedAgentStep
    ] = Field(
        default_factory=list
    )


class CompletionDecision(BaseModel):
    complete: bool

    confidence: int = Field(
        default=0,
        ge=0,
        le=100,
    )

    summary: str = ""

    missing: list[str] = Field(
        default_factory=list
    )


# ---------------------------------------------------------------------------
# Registered Tool Contracts
# ---------------------------------------------------------------------------

def describe_agent_tools():
    """
    Gives recovery and continuation reasoning access to the exact
    currently registered Phase 6 tool signatures.
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
# Registered Tool Names
# ---------------------------------------------------------------------------

def get_registered_tool_names():
    load_default_tools()

    return {
        tool.name
        for tool
        in list_tools()
    }


# ---------------------------------------------------------------------------
# Deterministic Phase 6 Verification
# ---------------------------------------------------------------------------

def verify_step_result(
    execution,
):
    """
    Uses the existing Phase 6 deterministic verifier.
    """

    return (
        verify_phase6_tool_result(
            execution
        )
    )


# ---------------------------------------------------------------------------
# Compact Tool Results
# ---------------------------------------------------------------------------

def extract_execution_details(
    execution,
):
    """
    Preserves the execution information most useful for agent reasoning.

    This intentionally includes real stdout, stderr, exit codes,
    file paths, workspace paths, and application metadata.
    """

    if not isinstance(
        execution,
        dict,
    ):

        return execution


    details = {
        "success":
            execution.get(
                "success"
            ),

        "executed":
            execution.get(
                "executed"
            ),

        "tool":
            execution.get(
                "tool"
            ),

        "risk":
            execution.get(
                "risk"
            ),

        "requires_approval":
            execution.get(
                "requires_approval"
            ),

        "error":
            execution.get(
                "error"
            ),

        "reason":
            execution.get(
                "reason"
            ),
    }


    result = execution.get(
        "result"
    )


    if isinstance(
        result,
        dict,
    ):

        details["result"] = {
            "workspace":
                result.get(
                    "workspace"
                ),

            "cwd":
                result.get(
                    "cwd"
                ),

            "command":
                result.get(
                    "command"
                ),

            "command_text":
                result.get(
                    "command_text"
                ),

            "exit_code":
                result.get(
                    "exit_code"
                ),

            "stdout":
                result.get(
                    "stdout"
                ),

            "stderr":
                result.get(
                    "stderr"
                ),

            "timed_out":
                result.get(
                    "timed_out"
                ),

            "file":
                result.get(
                    "file"
                ),

            "directory":
                result.get(
                    "directory"
                ),

            "entries":
                result.get(
                    "entries"
                ),

            "content":
                result.get(
                    "content"
                ),

            "opened":
                result.get(
                    "opened"
                ),

            "new_window":
                result.get(
                    "new_window"
                ),

            "focused":
                result.get(
                    "focused"
                ),

            "window_title":
                result.get(
                    "window_title"
                ),

            "pid":
                result.get(
                    "pid"
                ),
        }

    else:

        details["result"] = (
            result
        )


    return details


# ---------------------------------------------------------------------------
# Task History
# ---------------------------------------------------------------------------

def build_history(
    task: AgentTask,
):
    """
    Converts the entire current task into compact reasoning context.
    """

    history = []


    for step in task.steps:

        history.append(
            {
                "step_number":
                    step.step_number,

                "description":
                    step.description,

                "tool_name":
                    step.tool_name,

                "arguments":
                    step.arguments,

                "status":
                    step.status,

                "attempts":
                    step.attempts,

                "result":
                    extract_execution_details(
                        step.result
                    ),

                "error":
                    step.error,
            }
        )


    return history


# ---------------------------------------------------------------------------
# Parse Tool Arguments
# ---------------------------------------------------------------------------

def parse_arguments(
    arguments_json: str,
):
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
# Convert Planned Steps
# ---------------------------------------------------------------------------

def convert_planned_steps(
    planned_steps,
    starting_number: int,
):
    """
    Converts model-generated next steps into AgentStep objects.

    Invalid / hallucinated tool names are discarded.
    """

    registered = (
        get_registered_tool_names()
    )

    converted = []


    for planned in planned_steps:

        tool_name = (
            planned.tool_name
            .strip()
            .lower()
        )


        if tool_name not in registered:

            continue


        converted.append(
            AgentStep(
                step_number=(
                    starting_number
                    + len(
                        converted
                    )
                ),

                description=
                    planned.description,

                tool_name=
                    tool_name,

                arguments=
                    parse_arguments(
                        planned.arguments_json
                    ),
            )
        )


    return converted


# ---------------------------------------------------------------------------
# Failure Recovery
# ---------------------------------------------------------------------------

def decide_recovery(
    task: AgentTask,
    failed_step: AgentStep,
):
    """
    Determines what to do after a real failed action.
    """

    payload = {
        "goal":
            task.goal,

        "failed_step": {
            "step_number":
                failed_step.step_number,

            "description":
                failed_step.description,

            "tool_name":
                failed_step.tool_name,

            "arguments":
                failed_step.arguments,

            "attempts":
                failed_step.attempts,

            "error":
                failed_step.error,

            "execution":
                extract_execution_details(
                    failed_step.result
                ),
        },

        "task_history":
            build_history(
                task
            ),

        "available_tools":
            describe_agent_tools(),
    }


    response = (
        client.responses.parse(
            model="gpt-5.5",

            instructions="""
You are E.V.I.E.'s Phase 7 failure recovery controller.

A REAL computer action failed.

You have:
- the original user goal
- the exact failed tool
- the exact arguments used
- actual stdout
- actual stderr
- actual exit code
- the full task history
- exact registered tool signatures

Determine the safest useful next action.


VALID ACTIONS:

retry

    Retry the failed step unchanged.

    Use only for genuinely temporary failures.


replace

    Replace the failed step and remaining work with a corrected
    sequence of tool actions.


continue

    Skip the failed step only when it is genuinely optional to
    the user's original goal.


fail

    Stop only when the goal cannot reasonably or safely continue.


RULES:

1. Read actual stdout and stderr.

2. A non-zero exit code does NOT automatically mean the task
   should stop.

3. Programming errors are normally recoverable.

4. File-not-found errors are normally recoverable if the requested
   file can be located using available tools.

5. Incorrect tool arguments are normally recoverable.

6. When a source-code problem must be fixed:

       inspect the relevant source when necessary
       modify it with write_file
       rerun the program or test

7. write_file and other modifying tools will still pass through
   Phase 6 permissions. Do not avoid them merely because approval
   will be required.

8. Use the exact registered tool signatures.

9. Never invent argument names.

10. Never invent file paths.

11. Never repeat the same known-bad action indefinitely.

12. Return the smallest corrective sequence.

13. Return at most four next steps.

14. If an action discovers information needed for later work,
    include the action that actually uses that information when
    possible.

Example:

Goal:
Run typewriter.py and debug it until successful.

Failure:
typewriter.py was not found.

A search then needs to locate the file.

A useful corrected sequence could be:

1. search/list to locate the requested file
2. run the discovered path

If the exact discovered path is not known yet, it is acceptable
for the corrective sequence to contain only the search step.
The continuation controller will use the real search result afterward.


Example:

Failure:
run_python returned:

SyntaxError: expected ':'

Good recovery:

1. read_file the source
2. write_file corrected source
3. run_python again


Example:

Failure:
run_python() got unexpected keyword argument 'path'

Registered signature:

run_python(arguments=None, cwd=".", workspace_path=None, timeout=60)

Correct action:

replace

Next step:

run_python(
    arguments=["actual_script.py"]
)
""".strip(),

            input=json.dumps(
                payload,
                ensure_ascii=False,
                default=str,
            ),

            text_format=
                RecoveryDecision,
        )
    )


    return (
        response.output_parsed
    )


# ---------------------------------------------------------------------------
# Continuation Planning
# ---------------------------------------------------------------------------

def decide_continuation(
    task: AgentTask,
):
    """
    Runs when every CURRENTLY PLANNED step has completed.

    This prevents investigative actions from incorrectly ending the
    entire task.

    Example:

        search for typewriter.py
            ↓
        finds TypewriterTest/typewriter.py
            ↓
        current plan ends
            ↓
        continuation planner decides:
            run discovered path
    """

    payload = {
        "goal":
            task.goal,

        "task_history":
            build_history(
                task
            ),

        "available_tools":
            describe_agent_tools(),
    }


    response = (
        client.responses.parse(
            model="gpt-5.5",

            instructions="""
You are E.V.I.E.'s Phase 7 continuation controller.

Every CURRENTLY PLANNED action has finished.

Your job is to determine whether the ORIGINAL USER GOAL is actually
finished.

This is different from asking whether the current plan ended.

A successful investigative action may reveal information that must
be used in another action.


EXAMPLE:

Goal:

Run typewriter.py and fix errors until successful.

History:

1. run_python("typewriter.py")
   failed because the file was not found.

2. workspace search
   succeeded and found:
   TypewriterTest/typewriter.py

The task is NOT complete.

Correct next action:

run_python(
    arguments=[
        "TypewriterTest/typewriter.py"
    ]
)


ANOTHER EXAMPLE:

Goal:

Debug script until successful.

History:

1. run_python
   SyntaxError

2. read_file
   source was successfully read

The task is NOT complete.

Correct next actions may be:

1. write_file corrected source
2. run_python again


RULES:

1. Judge the ORIGINAL GOAL, not merely the current plan.

2. Use actual execution results only.

3. Never invent discovered paths.

4. Never invent stdout or stderr.

5. Use exact registered tool signatures.

6. If the history reveals a file path needed for the next action,
   use that real path.

7. If the user requested:
       debug until successful
       fix errors
       keep trying
       rerun until it works
       verify the result

   then keep working until evidence supports completion.

8. Never bypass permissions.

9. Do not add unnecessary steps.

10. Return at most four next steps.

11. If the original goal is already supported by the real history:

        complete = true
        next_steps = []

12. If more work remains:

        complete = false
        next_steps = concrete actions
""".strip(),

            input=json.dumps(
                payload,
                ensure_ascii=False,
                default=str,
            ),

            text_format=
                ContinuationDecision,
        )
    )


    return (
        response.output_parsed
    )


# ---------------------------------------------------------------------------
# Final Goal Verification
# ---------------------------------------------------------------------------

def verify_goal_completion(
    task: AgentTask,
):
    """
    Performs the final strict verification of the original user goal.
    """

    payload = {
        "goal":
            task.goal,

        "task_history":
            build_history(
                task
            ),
    }


    response = (
        client.responses.parse(
            model="gpt-5.5",

            instructions="""
You are E.V.I.E.'s final Phase 7 completion verifier.

Determine whether the ORIGINAL USER GOAL is actually complete.

Judge ONLY from real execution evidence.

Useful evidence includes:

- exit codes
- stdout
- stderr
- filesystem results
- file contents
- Git output
- VS Code open results
- new_window metadata
- application focus results
- other deterministic tool results


RULES:

1. Never assume a planned action happened.

2. Never mark success merely because every current step finished.

3. For programming tasks:

       exit code 0 is evidence the program executed successfully.

       expected stdout is evidence the program produced the
       requested result.

4. For debugging tasks:

       the final successful run must occur AFTER the relevant
       correction.

5. If the user explicitly requested a new VS Code window:

       new_window=True

   in the actual VS Code tool result is sufficient evidence that
   the new-window launch was requested successfully.

6. If important evidence is missing:

       complete = false

7. Never invent missing evidence.
""".strip(),

            input=json.dumps(
                payload,
                ensure_ascii=False,
                default=str,
            ),

            text_format=
                CompletionDecision,
        )
    )


    return (
        response.output_parsed
    )


# ---------------------------------------------------------------------------
# Standalone Test
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    print(
        "E.V.I.E. Agent Verifier"
    )

    print(
        "------------------------"
    )


    sample = {
        "success":
            False,

        "executed":
            True,

        "tool":
            "run_python",

        "risk":
            "low",

        "result": {
            "exit_code":
                1,

            "stdout":
                "",

            "stderr":
                (
                    "SyntaxError: "
                    "expected ':'"
                ),

            "timed_out":
                False,
        },
    }


    print(
        verify_step_result(
            sample
        )
    )