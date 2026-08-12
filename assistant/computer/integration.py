
"""
E.V.I.E. - Phase 13L Computer Integration Entry Point

This is the high-level computer-control boundary intended for use by
assistant/main.py or the generic Phase 6 tool layer.
"""

from __future__ import annotations

from .integration_planner import plan_computer_message
from .integration_runtime import execute_computer_plan


def _render_result(
    result: dict,
) -> str:
    if not result.get(
        "success",
        False,
    ):
        detail = (
            result.get(
                "detail"
            )
            or "The computer action did not complete."
        )

        return (
            "Computer control failed: "
            + str(detail)
        )

    action = str(
        result.get(
            "action",
            ""
        )
    )

    method = str(
        result.get(
            "method",
            ""
        )
    )

    verified = bool(
        result.get(
            "verified",
            False,
        )
    )

    suffix = (
        " and verified"
        if verified
        else ""
    )

    return (
        f"Completed {action} through {method}{suffix}."
    )


def handle_computer_message(
    user_text: str,
    *,
    browser_session=None,
):
    plan = plan_computer_message(
        user_text
    )

    if not plan.handled:
        return {
            "handled": False,
            "response": "",
            "result": None,
            "plan": plan.to_dict(),
        }

    result = execute_computer_plan(
        plan,
        browser_session=browser_session,
    )

    return {
        "handled": True,
        "response": _render_result(
            result
        ),
        "result": result,
        "plan": plan.to_dict(),
    }
