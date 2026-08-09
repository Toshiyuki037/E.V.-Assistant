"""
E.V.I.E. - Tool Executor

Created: August 9, 2026
Last Edited: August 9, 2026
Author: Max Maehara

Purpose:
    Provides the single controlled execution gateway for E.V.I.E.'s
    computer tools.

How It Works:
    1. Look up requested tool.
    2. Determine effective risk.
    3. Check permission policy.
    4. Audit the request.
    5. Execute if allowed.
    6. Capture result or error.
    7. Audit the outcome.

Important:
    Future brain/tool integration should call execute_tool()
    rather than invoking tool functions directly.

Most Recent Change:
    Initial Phase 6 central tool executor.
"""

from .audit import (
    log_tool_event,
)

from .permissions import (
    classify_command_risk,
    evaluate_permission,
    highest_risk,
)

from .registry import (
    get_tool,
    load_default_tools,
)


# ---------------------------------------------------------------------------
# Load Registered Tools
# ---------------------------------------------------------------------------

load_default_tools()


# ---------------------------------------------------------------------------
# Effective Risk
# ---------------------------------------------------------------------------

def determine_effective_risk(
    tool,
    arguments: dict,
):
    """
    Calculates effective action risk.

    Terminal commands receive extra command-level inspection.
    """

    risk = (
        tool.risk
    )

    if tool.name == "run_command":

        command_arguments = (
            arguments.get(
                "arguments"
            )
            or []
        )

        command_text = " ".join(
            str(item)
            for item
            in command_arguments
        )

        command_risk = (
            classify_command_risk(
                command_text
            )
        )

        risk = highest_risk(
            risk,
            command_risk,
        )

    return risk


# ---------------------------------------------------------------------------
# Main Executor
# ---------------------------------------------------------------------------

def execute_tool(
    tool_name: str,
    arguments=None,
    approved: bool = False,
):
    """
    Executes a registered tool through E.V.I.E.'s permission
    and audit layers.

    Returns a structured result dictionary.
    """

    if arguments is None:

        arguments = {}

    tool = get_tool(
        tool_name
    )

    if tool is None:

        return {
            "success":
                False,

            "executed":
                False,

            "tool":
                tool_name,

            "error":
                "Unknown tool.",
        }


    # -----------------------------------------------------------------------
    # Risk
    # -----------------------------------------------------------------------

    effective_risk = (
        determine_effective_risk(
            tool,
            arguments,
        )
    )


    # -----------------------------------------------------------------------
    # Permission
    # -----------------------------------------------------------------------

    permission = (
        evaluate_permission(
            base_risk=
                effective_risk,

            approved=
                approved,
        )
    )


    log_tool_event(
        tool_name=
            tool.name,

        status=
            (
                "approved"
                if permission.allowed
                else "blocked"
            ),

        risk=
            permission.risk,

        arguments=
            arguments,

        result={
            "permission_reason":
                permission.reason
        },
    )


    if not permission.allowed:

        return {
            "success":
                False,

            "executed":
                False,

            "tool":
                tool.name,

            "risk":
                permission.risk,

            "requires_approval":
                permission.requires_approval,

            "reason":
                permission.reason,
        }


    # -----------------------------------------------------------------------
    # Execution
    # -----------------------------------------------------------------------

    try:

        result = (
            tool.function(
                **arguments
            )
        )


        log_tool_event(
            tool_name=
                tool.name,

            status=
                "success",

            risk=
                permission.risk,

            arguments=
                arguments,

            result=
                result,
        )


        return {
            "success":
                True,

            "executed":
                True,

            "tool":
                tool.name,

            "risk":
                permission.risk,

            "result":
                result,
        }


    except Exception as error:

        log_tool_event(
            tool_name=
                tool.name,

            status=
                "error",

            risk=
                permission.risk,

            arguments=
                arguments,

            error=
                error,
        )


        return {
            "success":
                False,

            "executed":
                True,

            "tool":
                tool.name,

            "risk":
                permission.risk,

            "error":
                str(
                    error
                ),
        }


# ---------------------------------------------------------------------------
# Standalone Tests
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    print(
        "E.V.I.E. Tool Executor"
    )

    print(
        "-----------------------"
    )


    # -----------------------------------------------------------------------
    # Low-risk test
    # -----------------------------------------------------------------------

    print()

    print(
        "TEST 1 - list_directory"
    )

    result = execute_tool(
        "list_directory",
        {
            "path":
                "."
        },
    )

    print(
        result
    )


    # -----------------------------------------------------------------------
    # Low-risk terminal test
    # -----------------------------------------------------------------------

    print()

    print(
        "TEST 2 - run_python"
    )

    result = execute_tool(
        "run_python",
        {
            "arguments":
                [
                    "-c",
                    (
                        "print("
                        "'E.V.I.E. executor works'"
                        ")"
                    ),
                ]
        },
    )

    print(
        result
    )


    # -----------------------------------------------------------------------
    # Medium-risk filesystem test
    # -----------------------------------------------------------------------

    print()

    print(
        "TEST 3 - create_file "
        "without approval"
    )

    result = execute_tool(
        "create_file",
        {
            "path":
                "runtime/"
                "phase6_test.txt",

            "content":
                "Phase 6 tool test.",
        },
        approved=False,
    )

    print(
        result
    )