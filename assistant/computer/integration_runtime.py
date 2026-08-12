
"""
E.V.I.E. - Phase 13L Computer Integration Runtime

Binds high-level computer tool requests to the Phase 13J unified router and
the read-only/specialized Phase 13 controller primitives.
"""

from __future__ import annotations

from pathlib import Path

from .control_controller import control_local_computer
from .vision_controller import capture_local_monitor


def execute_computer_plan(
    plan,
    *,
    browser_session=None,
):
    action = str(
        plan.action
    )

    # vision.capture is read-only and intentionally remains outside the
    # mutating Phase 13J action dispatcher.
    if action == "vision.capture":
        path = (
            Path("runtime")
            / "computer"
            / "captures"
            / "latest-screen.png"
        )

        result = capture_local_monitor(
            str(path),
            monitor_index=1,
        )

        return {
            "success": bool(
                result.get(
                    "success",
                    False,
                )
            ),
            "action": action,
            "method": "vision",
            "verified": bool(
                result.get(
                    "success",
                    False,
                )
            ),
            "result": result,
            "attempts": [],
            "detail": "Screen capture completed.",
        }

    return control_local_computer(
        action,
        target=plan.target,
        arguments=plan.arguments,
        approved=plan.approved,
        allow_vision=plan.allow_vision,
        browser_session=browser_session,
    )
