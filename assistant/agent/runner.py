"""
E.V.I.E. - Agent Runner

Created: August 9, 2026
Last Edited: August 9, 2026
Author: Max Maehara

Purpose:
    Executes Phase 7 agentic tasks through E.V.I.E.'s existing
    Phase 6 controlled tool system.

Capabilities:
    - bounded multi-step execution
    - Phase 6 permission enforcement
    - approval pause / resume
    - persistent task state
    - failed-step recovery
    - dynamic continuation
    - retries and replanning
    - final goal verification
    - placeholder mutation protection
    - user cancellation

Security:
    Phase 7 never directly performs computer actions.

    Every real action goes through execute_tool().

Most Recent Change:
    Added deterministic protection against placeholder content being
    written by create_file/write_file recovery actions.
"""

import inspect
import re

from assistant.perception.workspace import (
    get_workspace_context,
)

from assistant.tools.executor import (
    execute_tool,
)

from assistant.tools.registry import (
    get_tool,
    load_default_tools,
)

from .models import (
    AgentResult,
    AgentTask,
)

from .planner import (
    format_plan,
    plan_task,
)

from .state import (
    clear_task,
    load_task,
    save_task,
)

from .verifier import (
    convert_planned_steps,
    decide_continuation,
    decide_recovery,
    verify_goal_completion,
    verify_step_result,
)


# ---------------------------------------------------------------------------
# Limits
# ---------------------------------------------------------------------------

MAX_TOTAL_EXECUTIONS = 16

MAX_STEP_ATTEMPTS = 3

MAX_REPLANS = 5

MAX_CONTINUATIONS = 5

MIN_COMPLETION_CONFIDENCE = 70


load_default_tools()


# ---------------------------------------------------------------------------
# Placeholder Protection
# ---------------------------------------------------------------------------

PLACEHOLDER_MUTATION_TOOLS = {
    "create_file",
    "write_file",
}


PLACEHOLDER_EXACT_VALUES = {
    "same as above",
    "same content as above",
    "same file as above",
    "insert code here",
    "insert content here",
    "replace with corrected code",
    "replace with corrected content",
    "corrected file content",
    "complete file content",
    "actual corrected source",
}


PLACEHOLDER_TAG_PATTERN = re.compile(
    (
        r"^\s*<[^>\n]*"
        r"(?:"
        r"corrected|"
        r"complete|"
        r"replacement|"
        r"actual|"
        r"insert|"
        r"file\s+content|"
        r"source\s+code|"
        r"code\s+here"
        r")"
        r"[^>\n]*>\s*$"
    ),

    flags=re.IGNORECASE,
)


def detect_placeholder_content(
    tool_name: str,
    arguments: dict,
):
    """
    Returns an error message when a Phase 7 file mutation contains
    obvious model placeholder text instead of real file contents.

    Returns None when the mutation looks valid.
    """

    if (
        tool_name
        not in PLACEHOLDER_MUTATION_TOOLS
    ):

        return None


    content = arguments.get(
        "content"
    )


    if content is None:

        return (
            "File mutation did not contain "
            "a content argument."
        )


    if not isinstance(
        content,
        str,
    ):

        return (
            "File mutation content must "
            "be a string."
        )


    stripped = (
        content.strip()
    )


    if not stripped:

        # Empty files are technically valid, so don't universally block
        # them. If the user truly asked for one, allow it.

        return None


    normalized = (
        " ".join(
            stripped.lower().split()
        )
    )


    if (
        normalized
        in PLACEHOLDER_EXACT_VALUES
    ):

        return (
            "Agent generated placeholder "
            "file content instead of the "
            "actual requested contents."
        )


    if PLACEHOLDER_TAG_PATTERN.fullmatch(
        stripped
    ):

        return (
            "Agent generated angle-bracket "
            "placeholder content instead of "
            "actual file contents."
        )


    # Catch very short obvious stand-ins without blocking normal source
    # code containing TODO comments or HTML.

    if len(stripped) <= 250:

        obvious_phrases = (
            "corrected file content after inspection",
            "complete corrected file",
            "actual file content here",
            "insert corrected source here",
            "replacement source here",
        )


        lower = (
            stripped.lower()
        )


        if any(
            phrase in lower
            for phrase
            in obvious_phrases
        ):

            return (
                "Agent generated descriptive "
                "placeholder text rather than "
                "actual executable file contents."
            )


    return None


# ---------------------------------------------------------------------------
# Synthetic Failure
# ---------------------------------------------------------------------------

def build_placeholder_failure(
    tool_name: str,
    reason: str,
):
    """
    Creates a normal-looking failed execution record so the existing
    recovery controller can repair the planning mistake.
    """

    return {
        "success":
            False,

        "executed":
            False,

        "tool":
            tool_name,

        "risk":
            "medium",

        "error":
            reason,

        "result": {
            "exit_code":
                None,

            "stdout":
                "",

            "stderr":
                reason,

            "timed_out":
                False,
        },
    }


# ---------------------------------------------------------------------------
# Workspace
# ---------------------------------------------------------------------------

def get_current_workspace_path():
    context = (
        get_workspace_context()
    )


    return context.get(
        "workspace_path"
    )


# ---------------------------------------------------------------------------
# Workspace Binding
# ---------------------------------------------------------------------------

def bind_workspace(
    tool_name: str,
    arguments: dict,
    workspace_path: str | None,
):
    """
    Adds workspace_path only when the target tool supports it.
    """

    tool = get_tool(
        tool_name
    )


    if (
        tool is None
        or not workspace_path
    ):

        return arguments


    try:

        parameters = inspect.signature(
            tool.function
        ).parameters

    except (
        TypeError,
        ValueError,
    ):

        return arguments


    if (
        "workspace_path"
        in parameters
        and "workspace_path"
        not in arguments
    ):

        arguments[
            "workspace_path"
        ] = workspace_path


    return arguments


# ---------------------------------------------------------------------------
# Create Task
# ---------------------------------------------------------------------------

def create_agent_task(
    user_message: str,
):
    plan = plan_task(
        user_message
    )


    if not plan.use_agent:

        return (
            None,
            plan,
        )


    task = AgentTask(
        goal=
            plan.goal,

        steps=
            plan.steps,

        workspace_path=
            get_current_workspace_path(),

        status=
            "planned",
    )


    save_task(
        task
    )


    return (
        task,
        plan,
    )


# ---------------------------------------------------------------------------
# Renumber
# ---------------------------------------------------------------------------

def renumber_steps(
    task: AgentTask,
):
    for index, step in enumerate(
        task.steps,
        start=1,
    ):

        step.step_number = (
            index
        )


# ---------------------------------------------------------------------------
# Replace Remaining Steps
# ---------------------------------------------------------------------------

def replace_remaining_steps(
    task: AgentTask,
    new_steps,
):
    completed = (
        task.steps[
            :task.current_step_index
        ]
    )


    task.steps = (
        completed
        + new_steps
    )


    renumber_steps(
        task
    )


    task.current_step_index = (
        len(
            completed
        )
    )


    save_task(
        task
    )


# ---------------------------------------------------------------------------
# Append Continuation Steps
# ---------------------------------------------------------------------------

def append_steps(
    task: AgentTask,
    new_steps,
):
    if not new_steps:

        return


    task.steps.extend(
        new_steps
    )


    renumber_steps(
        task
    )


    save_task(
        task
    )


# ---------------------------------------------------------------------------
# Failure Diagnostics
# ---------------------------------------------------------------------------

def print_step_failure(
    step,
):
    print()

    print(
        "[Agent Step Failure]"
    )


    print(
        "Step:",
        step.step_number,
    )


    print(
        "Tool:",
        step.tool_name,
    )


    execution = (
        step.result
        if isinstance(
            step.result,
            dict,
        )
        else {}
    )


    result = execution.get(
        "result",
        {}
    )


    if isinstance(
        result,
        dict,
    ):

        exit_code = result.get(
            "exit_code"
        )


        stdout = (
            result.get(
                "stdout"
            )
            or ""
        )


        stderr = (
            result.get(
                "stderr"
            )
            or ""
        )


        if exit_code is not None:

            print(
                "Exit code:",
                exit_code,
            )


        if stdout:

            print()

            print(
                "STDOUT:"
            )

            print(
                stdout.rstrip()
            )


        if stderr:

            print()

            print(
                "STDERR:"
            )

            print(
                stderr.rstrip()
            )


    elif step.error:

        print(
            "Error:",
            step.error,
        )


# ---------------------------------------------------------------------------
# Execute Agent Step Safely
# ---------------------------------------------------------------------------

def execute_agent_step(
    step,
    arguments,
    approved: bool = False,
):
    """
    Single Phase 7 gateway into Phase 6 execution.

    Performs agent-specific validation first, then delegates the real
    action to execute_tool().
    """

    placeholder_error = (
        detect_placeholder_content(
            step.tool_name,
            arguments,
        )
    )


    if placeholder_error:

        return (
            build_placeholder_failure(
                step.tool_name,
                placeholder_error,
            )
        )


    return execute_tool(
        tool_name=
            step.tool_name,

        arguments=
            arguments,

        approved=
            approved,
    )


# ---------------------------------------------------------------------------
# Recovery
# ---------------------------------------------------------------------------

def recover_from_failure(
    task: AgentTask,
    step,
):
    if (
        task.replan_count
        >= MAX_REPLANS
    ):

        return "fail"


    recovery = decide_recovery(
        task,
        step,
    )


    if recovery is None:

        return "fail"


    action = (
        recovery.action
        .strip()
        .lower()
    )


    # -----------------------------------------------------------------------
    # Retry
    # -----------------------------------------------------------------------

    if action == "retry":

        if (
            step.attempts
            >= MAX_STEP_ATTEMPTS
        ):

            return "fail"


        step.status = "pending"


        save_task(
            task
        )


        return "retry"


    # -----------------------------------------------------------------------
    # Continue
    # -----------------------------------------------------------------------

    if action == "continue":

        step.status = "skipped"

        task.current_step_index += 1


        save_task(
            task
        )


        return "continue"


    # -----------------------------------------------------------------------
    # Replace
    # -----------------------------------------------------------------------

    if action == "replace":

        if not recovery.next_steps:

            return "fail"


        task.replan_count += 1


        new_steps = (
            convert_planned_steps(
                recovery.next_steps,

                starting_number=(
                    task.current_step_index
                    + 1
                ),
            )
        )


        if not new_steps:

            return "fail"


        replace_remaining_steps(
            task,
            new_steps,
        )


        return "replace"


    return "fail"


# ---------------------------------------------------------------------------
# Continuation
# ---------------------------------------------------------------------------

def continue_if_needed(
    task: AgentTask,
):
    if (
        task.continuation_count
        >= MAX_CONTINUATIONS
    ):

        return "fail"


    continuation = decide_continuation(
        task
    )


    if continuation is None:

        return "complete"


    if continuation.complete:

        return "complete"


    if not continuation.next_steps:

        return "complete"


    new_steps = (
        convert_planned_steps(
            continuation.next_steps,

            starting_number=(
                len(task.steps)
                + 1
            ),
        )
    )


    if not new_steps:

        return "complete"


    task.continuation_count += 1


    append_steps(
        task,
        new_steps,
    )


    task.status = "running"


    save_task(
        task
    )


    return "continue"


# ---------------------------------------------------------------------------
# Run Task
# ---------------------------------------------------------------------------

def run_task(
    task: AgentTask | None = None,
):
    if task is None:

        task = load_task()


    if task is None:

        return AgentResult(
            success=False,

            status="no_task",

            goal="",

            message=(
                "No active agent task exists."
            ),
        )


    task.status = "running"


    save_task(
        task
    )


    while True:

        # -------------------------------------------------------------------
        # Execute Current Plan
        # -------------------------------------------------------------------

        while (
            task.current_step_index
            < len(task.steps)
        ):

            # ---------------------------------------------------------------
            # Hard Execution Limit
            # ---------------------------------------------------------------

            if (
                task.total_executions
                >= MAX_TOTAL_EXECUTIONS
            ):

                task.status = "failed"

                task.final_summary = (
                    "Task stopped because the "
                    "Phase 7 execution limit "
                    "was reached."
                )


                save_task(
                    task
                )


                return AgentResult(
                    success=False,

                    status="failed",

                    goal=
                        task.goal,

                    message=
                        task.final_summary,

                    steps=
                        task.steps,
                )


            # ---------------------------------------------------------------
            # Current Step
            # ---------------------------------------------------------------

            step = task.steps[
                task.current_step_index
            ]


            step.status = "running"

            step.attempts += 1

            task.total_executions += 1


            arguments = dict(
                step.arguments
            )


            arguments = bind_workspace(
                step.tool_name,
                arguments,
                task.workspace_path,
            )


            step.arguments = (
                arguments
            )


            save_task(
                task
            )


            # ---------------------------------------------------------------
            # Execute Through Controlled Gateway
            # ---------------------------------------------------------------

            execution = execute_agent_step(
                step,
                arguments,
                approved=False,
            )


            # ---------------------------------------------------------------
            # Approval Required
            # ---------------------------------------------------------------

            if execution.get(
                "requires_approval",
                False,
            ):

                step.status = (
                    "awaiting_approval"
                )


                task.status = (
                    "awaiting_approval"
                )


                task.pending_action = {
                    "step_number":
                        step.step_number,

                    "tool_name":
                        step.tool_name,

                    "arguments":
                        arguments,

                    "risk":
                        execution.get(
                            "risk"
                        ),

                    "description":
                        step.description,
                }


                save_task(
                    task
                )


                return AgentResult(
                    success=False,

                    status=
                        "approval_required",

                    goal=
                        task.goal,

                    message=(
                        f"Step "
                        f"{step.step_number} "
                        "requires approval."
                    ),

                    requires_approval=
                        True,

                    pending_action=
                        task.pending_action,

                    steps=
                        task.steps,
                )


            # ---------------------------------------------------------------
            # Verification
            # ---------------------------------------------------------------

            verification = (
                verify_step_result(
                    execution
                )
            )


            step.result = (
                execution
            )


            # ---------------------------------------------------------------
            # Success
            # ---------------------------------------------------------------

            if verification.successful:

                step.status = "completed"

                step.error = None

                task.current_step_index += 1


                save_task(
                    task
                )


                continue


            # ---------------------------------------------------------------
            # Failure
            # ---------------------------------------------------------------

            step.status = "failed"

            step.error = (
                verification.summary
            )


            save_task(
                task
            )


            print_step_failure(
                step
            )


            recovery_result = (
                recover_from_failure(
                    task,
                    step,
                )
            )


            if recovery_result in {
                "retry",
                "continue",
                "replace",
            }:

                continue


            task.status = "failed"

            task.final_summary = (
                step.error
                or (
                    "The task could not "
                    "recover from the "
                    "failed action."
                )
            )


            save_task(
                task
            )


            return AgentResult(
                success=False,

                status="failed",

                goal=
                    task.goal,

                message=
                    task.final_summary,

                steps=
                    task.steps,
            )


        # -------------------------------------------------------------------
        # Current Plan Finished - Check Continuation
        # -------------------------------------------------------------------

        continuation_result = (
            continue_if_needed(
                task
            )
        )


        if continuation_result == "continue":

            continue


        if continuation_result == "fail":

            task.status = "failed"

            task.final_summary = (
                "Task stopped because the "
                "Phase 7 continuation limit "
                "was reached."
            )


            save_task(
                task
            )


            return AgentResult(
                success=False,

                status="failed",

                goal=
                    task.goal,

                message=
                    task.final_summary,

                steps=
                    task.steps,
            )


        # -------------------------------------------------------------------
        # Final Verification
        # -------------------------------------------------------------------

        completion = (
            verify_goal_completion(
                task
            )
        )


        if (
            completion
            and completion.complete
            and completion.confidence
            >= MIN_COMPLETION_CONFIDENCE
        ):

            task.status = "completed"


            task.final_summary = (
                completion.summary
                or (
                    "The task completed "
                    "successfully."
                )
            )


            save_task(
                task
            )


            result = AgentResult(
                success=True,

                status="completed",

                goal=
                    task.goal,

                message=
                    task.final_summary,

                steps=
                    task.steps,
            )


            clear_task()


            return result


        # -------------------------------------------------------------------
        # Incomplete
        # -------------------------------------------------------------------

        task.status = "incomplete"


        task.final_summary = (
            completion.summary
            if completion
            else (
                "The execution finished, "
                "but the original goal "
                "could not be verified."
            )
        )


        save_task(
            task
        )


        return AgentResult(
            success=False,

            status="incomplete",

            goal=
                task.goal,

            message=
                task.final_summary,

            steps=
                task.steps,
        )


# ---------------------------------------------------------------------------
# Start Task
# ---------------------------------------------------------------------------

def run_agent_task(
    user_message: str,
):
    task, plan = (
        create_agent_task(
            user_message
        )
    )


    if task is None:

        return AgentResult(
            success=False,

            status="not_agent_task",

            goal=
                user_message,

            message=(
                plan.summary
                or (
                    "This request does not "
                    "require Phase 7."
                )
            ),

            steps=
                plan.steps,
        )


    print()

    print(
        "[Agent Plan]"
    )


    print(
        format_plan(
            plan
        )
    )


    return run_task(
        task
    )


# ---------------------------------------------------------------------------
# Resolve Approval
# ---------------------------------------------------------------------------

def resolve_agent_approval(
    approved: bool,
):
    task = load_task()


    if (
        task is None
        or not task.pending_action
    ):

        return AgentResult(
            success=False,

            status="no_pending_action",

            goal=(
                task.goal
                if task
                else ""
            ),

            message=(
                "No Phase 7 action "
                "is awaiting approval."
            ),
        )


    pending = (
        task.pending_action
    )


    step_number = (
        pending[
            "step_number"
        ]
    )


    step = next(
        (
            item
            for item
            in task.steps
            if (
                item.step_number
                == step_number
            )
        ),
        None,
    )


    if step is None:

        return AgentResult(
            success=False,

            status="failed",

            goal=
                task.goal,

            message=(
                "The pending Phase 7 "
                "step could not be found."
            ),
        )


    # -----------------------------------------------------------------------
    # Rejected
    # -----------------------------------------------------------------------

    if not approved:

        step.status = "cancelled"

        task.status = "cancelled"

        task.pending_action = None

        task.final_summary = (
            "Task cancelled because "
            "the pending action was rejected."
        )


        save_task(
            task
        )


        clear_task()


        return AgentResult(
            success=False,

            status="cancelled",

            goal=
                task.goal,

            message=
                task.final_summary,

            steps=
                task.steps,
        )


    # -----------------------------------------------------------------------
    # Approved - Revalidate Content Before Mutation
    # -----------------------------------------------------------------------

    arguments = (
        pending[
            "arguments"
        ]
    )


    placeholder_error = (
        detect_placeholder_content(
            pending[
                "tool_name"
            ],

            arguments,
        )
    )


    if placeholder_error:

        execution = (
            build_placeholder_failure(
                pending[
                    "tool_name"
                ],

                placeholder_error,
            )
        )

    else:

        execution = execute_tool(
            tool_name=
                pending[
                    "tool_name"
                ],

            arguments=
                arguments,

            approved=True,
        )


    verification = (
        verify_step_result(
            execution
        )
    )


    step.result = (
        execution
    )


    task.pending_action = None


    # -----------------------------------------------------------------------
    # Approved Action Failed
    # -----------------------------------------------------------------------

    if not verification.successful:

        step.status = "failed"

        step.error = (
            verification.summary
        )


        save_task(
            task
        )


        print_step_failure(
            step
        )


        recovery_result = (
            recover_from_failure(
                task,
                step,
            )
        )


        if recovery_result in {
            "retry",
            "continue",
            "replace",
        }:

            task.status = "running"


            save_task(
                task
            )


            return run_task(
                task
            )


        task.status = "failed"

        task.final_summary = (
            verification.summary
        )


        save_task(
            task
        )


        return AgentResult(
            success=False,

            status="failed",

            goal=
                task.goal,

            message=
                task.final_summary,

            steps=
                task.steps,
        )


    # -----------------------------------------------------------------------
    # Approved Action Succeeded
    # -----------------------------------------------------------------------

    step.status = "completed"

    step.error = None

    task.current_step_index += 1

    task.status = "running"


    save_task(
        task
    )


    return run_task(
        task
    )


# ---------------------------------------------------------------------------
# Resume
# ---------------------------------------------------------------------------

def resume_agent_task():
    task = load_task()


    if task is None:

        return AgentResult(
            success=False,

            status="no_task",

            goal="",

            message=(
                "No unfinished Phase 7 "
                "task exists."
            ),
        )


    if (
        task.status
        == "awaiting_approval"
    ):

        return AgentResult(
            success=False,

            status=
                "approval_required",

            goal=
                task.goal,

            message=(
                "The current Phase 7 "
                "task is waiting for approval."
            ),

            requires_approval=
                True,

            pending_action=
                task.pending_action,

            steps=
                task.steps,
        )


    return run_task(
        task
    )


# ---------------------------------------------------------------------------
# Cancel
# ---------------------------------------------------------------------------

def cancel_agent_task():
    task = load_task()


    if task is None:

        return AgentResult(
            success=False,

            status="no_task",

            goal="",

            message=(
                "No active Phase 7 "
                "task exists."
            ),
        )


    task.status = "cancelled"

    task.final_summary = (
        "Task cancelled by the user."
    )


    save_task(
        task
    )


    clear_task()


    return AgentResult(
        success=False,

        status="cancelled",

        goal=
            task.goal,

        message=
            "Task cancelled.",

        steps=
            task.steps,
    )


# ---------------------------------------------------------------------------
# Format Result
# ---------------------------------------------------------------------------

def format_agent_result(
    result: AgentResult,
):
    lines = [
        (
            f"Agent status: "
            f"{result.status}"
        ),

        (
            f"Goal: "
            f"{result.goal}"
        ),
    ]


    if result.message:

        lines.append(
            result.message
        )


    if result.steps:

        lines.append("")

        lines.append(
            "Task steps:"
        )


        for step in result.steps:

            lines.append(
                (
                    f"{step.step_number}. "
                    f"{step.description} "
                    f"[{step.status}]"
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
        "E.V.I.E. Agent Runner"
    )

    print(
        "----------------------"
    )


    print()

    print(
        "Placeholder validation:"
    )


    print(
        detect_placeholder_content(
            "write_file",

            {
                "content":
                    (
                        "<corrected file content "
                        "after inspection>"
                    )
            },
        )
    )


    print()


    print(
        "Normal source validation:"
    )


    print(
        detect_placeholder_content(
            "write_file",

            {
                "content":
                    (
                        "def main():\n"
                        "    print('hello')\n"
                    )
            },
        )
    )