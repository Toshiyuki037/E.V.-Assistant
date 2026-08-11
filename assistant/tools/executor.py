"""
E.V.I.E. - Tool Executor

Created: August 9, 2026
Last Edited: August 10, 2026
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

Phase 9:
    integration_execute receives dynamic risk based on the requested
    normalized integration capability.

    Examples:
        email.search      -> low
        calendar.read     -> low
        tasks.read        -> low

        calendar.create   -> medium
        tasks.create      -> medium
        tasks.complete    -> medium

        email.send        -> high

Security:
    Unknown Phase 9 capabilities fail closed as high risk.
"""

from __future__ import annotations

from assistant.integrations.permissions import (
    get_permission as
    get_integration_permission,
)

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
# Integration Risk
# ---------------------------------------------------------------------------

def determine_integration_risk(
    arguments: dict,
):
    """
    Determines Phase 6 action risk from a normalized Phase 9
    integration capability.

    Unknown capabilities fail closed as high risk.
    """

    capability = (
        str(
            arguments.get(
                "capability",
                "",
            )
        )
        .strip()
        .lower()
    )


    if not capability:

        return "high"


    permission = (
        get_integration_permission(
            capability
        )
    )


    if permission is None:

        # ---------------------------------------------------------------
        # Fail closed.
        #
        # A future integration capability must receive an explicit
        # Phase 9 permission policy before it can silently execute.
        # ---------------------------------------------------------------

        return "high"


    risk = (
        str(
            permission.risk
        )
        .strip()
        .lower()
    )


    if risk not in {
        "low",
        "medium",
        "high",
    }:

        return "high"


    return risk


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

    Phase 9 integration actions receive capability-level inspection.
    """

    risk = (
        tool.risk
    )


    # -----------------------------------------------------------------------
    # Terminal Risk Escalation
    # -----------------------------------------------------------------------

    if tool.name == "run_command":

        command_arguments = (
            arguments.get(
                "arguments"
            )
            or []
        )


        command_text = " ".join(
            str(
                item
            )

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


    # -----------------------------------------------------------------------
    # Phase 9 Integration Risk Escalation
    # -----------------------------------------------------------------------

    if (
        tool.name
        == "integration_execute"
    ):

        integration_risk = (
            determine_integration_risk(
                arguments
            )
        )


        risk = highest_risk(
            risk,
            integration_risk,
        )


    return risk


# ---------------------------------------------------------------------------
# Execute Registered Function
# ---------------------------------------------------------------------------

def invoke_tool_function(
    tool,
    arguments: dict,
    approved: bool,
):
    """
    Invokes the actual registered implementation.

    Phase 9's gateway receives the existing Phase 6 approval state so
    its own independent permission boundary can agree with Phase 6.

    Other tools retain their existing signatures and behavior.
    """

    if (
        tool.name
        == "integration_execute"
    ):

        call_arguments = dict(
            arguments
        )


        # ---------------------------------------------------------------
        # Planner/User Input May Never Supply Approval State
        # ---------------------------------------------------------------

        call_arguments.pop(
            "approved",
            None,
        )


        call_arguments[
            "approved"
        ] = bool(
            approved
        )


        return tool.function(
            **call_arguments
        )


    return tool.function(
        **arguments
    )


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


    if not isinstance(
        arguments,
        dict,
    ):

        return {
            "success":
                False,

            "executed":
                False,

            "tool":
                tool_name,

            "error":
                "Tool arguments must be a dictionary.",
        }


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
            invoke_tool_function(
                tool=
                    tool,

                arguments=
                    arguments,

                approved=
                    approved,
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
    # Low-risk Test
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
    # Low-risk Terminal Test
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
    # Medium-risk Filesystem Test
    # -----------------------------------------------------------------------

    print()

    print(
        "TEST 3 - create_file without approval"
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

        approved=
            False,
    )


    print(
        result
    )


    # -----------------------------------------------------------------------
    # Phase 9 Risk Classification Tests
    # -----------------------------------------------------------------------

    print()

    print(
        "TEST 4 - Phase 9 read risk"
    )


    tool = get_tool(
        "integration_execute"
    )


    if tool is not None:

        print(
            determine_effective_risk(
                tool,
                {
                    "capability":
                        "tasks.read"
                },
            )
        )


        print()

        print(
            "TEST 5 - Phase 9 write risk"
        )


        print(
            determine_effective_risk(
                tool,
                {
                    "capability":
                        "calendar.create"
                },
            )
        )


        print()

        print(
            "TEST 6 - Phase 9 email send risk"
        )


        print(
            determine_effective_risk(
                tool,
                {
                    "capability":
                        "email.send"
                },
            )
        )