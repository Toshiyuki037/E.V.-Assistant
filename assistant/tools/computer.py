from __future__ import annotations

from assistant.computer.control_controller import control_local_computer
from assistant.computer.action_catalog import planner_contract_text
from .registry import register_tool


def computer_control(
    action: str,
    target: str = "",
    arguments: dict | None = None,
    allow_vision: bool = True,
    approved: bool = False,
):
    return control_local_computer(
        action,
        target=target,
        arguments=dict(arguments or {}),
        allow_vision=bool(allow_vision),
        approved=bool(approved),
    )


register_tool(
    name="computer_control",
    description=(
        "Phase 13 unified Windows/computer control gateway. "
        "Prefer this over run_command, PowerShell, SendKeys, pyautogui, "
        "or coordinate clicking for desktop control. "
        + planner_contract_text()
    ),
    category="computer",
    risk="low",
    function=computer_control,
)
