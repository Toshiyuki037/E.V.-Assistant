"""
E.V.I.E. - Tool Result Verifier

Created: August 9, 2026
Last Edited: August 9, 2026
Author: Max Maehara

Purpose:
    Normalizes executor results into a reliable verification state
    before E.V.I.E. describes an action as successful.
"""

from dataclasses import dataclass
from typing import Any


# ---------------------------------------------------------------------------
# Verification Result
# ---------------------------------------------------------------------------

@dataclass
class ToolVerification:
    successful: bool
    status: str
    summary: str
    details: dict[str, Any]


# ---------------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------------

def verify_tool_result(
    execution: dict,
) -> ToolVerification:
    """
    Uses deterministic result fields rather than asking the language
    model to decide whether an action succeeded.
    """

    if not execution:

        return ToolVerification(
            successful=False,
            status="failed",
            summary="No executor result was returned.",
            details={},
        )

    if (
        not execution.get(
            "executed",
            False,
        )
        and execution.get(
            "requires_approval",
            False,
        )
    ):

        return ToolVerification(
            successful=False,
            status="approval_required",
            summary=(
                "The action was not executed because approval "
                "is required."
            ),
            details=execution,
        )

    if not execution.get(
        "success",
        False,
    ):

        return ToolVerification(
            successful=False,
            status="failed",
            summary=(
                execution.get(
                    "error"
                )
                or execution.get(
                    "reason"
                )
                or "The action failed."
            ),
            details=execution,
        )

    result = (
        execution.get(
            "result"
        )
        or {}
    )

    # Subprocess/Git results.
    if "exit_code" in result:

        if result.get(
            "timed_out",
            False,
        ):

            return ToolVerification(
                successful=False,
                status="timed_out",
                summary="The command timed out.",
                details=result,
            )

        exit_code = result.get(
            "exit_code"
        )

        if exit_code != 0:

            return ToolVerification(
                successful=False,
                status="failed",
                summary=(
                    f"The command exited with code {exit_code}."
                ),
                details=result,
            )

    # Desktop actions can return success at the Python-call level while
    # reporting that no window/URL was actually affected.
    for field in (
        "opened",
        "focused",
        "launched",
        "created",
        "written",
    ):

        if (
            field in result
            and result[field] is False
        ):

            return ToolVerification(
                successful=False,
                status="failed",
                summary=(
                    f"The tool completed, but '{field}' was false."
                ),
                details=result,
            )

    return ToolVerification(
        successful=True,
        status="success",
        summary="The tool completed successfully.",
        details=result,
    )


def verification_to_dict(
    verification: ToolVerification,
):
    return {
        "successful":
            verification.successful,

        "status":
            verification.status,

        "summary":
            verification.summary,

        "details":
            verification.details,
    }


if __name__ == "__main__":

    print(
        "E.V.I.E. Tool Result Verifier"
    )

    print(
        "------------------------------"
    )

    sample = {
        "success": True,
        "executed": True,
        "tool": "run_python",
        "result": {
            "exit_code": 0,
            "stdout": "hello\n",
            "stderr": "",
            "timed_out": False,
        },
    }

    print(
        verify_tool_result(
            sample
        )
    )
