"""
E.V.I.E. - Tool Permission Engine

Created: August 9, 2026
Last Edited: August 9, 2026
Author: Max Maehara

Purpose:
    Determines whether a requested tool action may execute
    automatically, requires approval, or must be blocked.

Risk Levels:

    LOW
        Read-only or easily reversible actions.

    MEDIUM
        Actions that modify project state but are normally recoverable.

    HIGH
        Destructive, privileged, system-wide, or otherwise dangerous
        operations.

Most Recent Change:
    Initial Phase 6 permission and command-risk engine.
"""

from dataclasses import dataclass


# ---------------------------------------------------------------------------
# Permission Result
# ---------------------------------------------------------------------------

@dataclass
class PermissionDecision:
    allowed: bool
    requires_approval: bool
    risk: str
    reason: str


# ---------------------------------------------------------------------------
# High-Risk Command Patterns
# ---------------------------------------------------------------------------

HIGH_RISK_COMMAND_PATTERNS = (
    "rm -rf",
    "rmdir /s",
    "del /f",
    "format ",
    "diskpart",
    "shutdown",
    "restart-computer",
    "stop-computer",
    "reg delete",
    "reg add",
    "remove-item -recurse",
    "remove-item -force",
    "git reset --hard",
    "git clean -fd",
    "git clean -fx",
    "git push --force",
    "git push -f",
    "bcdedit",
    "cipher /w",
)


MEDIUM_RISK_COMMAND_PATTERNS = (
    "pip install",
    "pip uninstall",
    "npm install",
    "npm uninstall",
    "npm update",
    "npx ",
    "git add",
    "git commit",
    "git checkout",
    "git switch",
    "git merge",
)


# ---------------------------------------------------------------------------
# Risk Escalation
# ---------------------------------------------------------------------------

def classify_command_risk(
    command_text: str,
):
    """
    Inspects a terminal command and escalates risk when needed.

    This is intentionally conservative.
    """

    text = (
        command_text
        .strip()
        .lower()
    )

    for pattern in (
        HIGH_RISK_COMMAND_PATTERNS
    ):

        if pattern in text:
            return "high"

    for pattern in (
        MEDIUM_RISK_COMMAND_PATTERNS
    ):

        if pattern in text:
            return "medium"

    return "low"


def highest_risk(
    first: str,
    second: str,
):
    order = {
        "low": 0,
        "medium": 1,
        "high": 2,
    }

    if (
        order[second]
        > order[first]
    ):
        return second

    return first


# ---------------------------------------------------------------------------
# Permission Decision
# ---------------------------------------------------------------------------

def evaluate_permission(
    base_risk: str,
    approved: bool = False,
    escalated_risk: str | None = None,
):
    """
    Evaluates whether execution is allowed.

    Current Phase 6 policy:

        LOW:
            execute automatically

        MEDIUM:
            execute only with explicit approval

        HIGH:
            execute only with explicit approval

    Later phases can support more sophisticated policies such as
    trusted projects, authenticated users, and persistent permissions.
    """

    risk = base_risk

    if escalated_risk:

        risk = highest_risk(
            risk,
            escalated_risk,
        )

    if risk == "low":

        return PermissionDecision(
            allowed=True,
            requires_approval=False,
            risk=risk,
            reason=(
                "Low-risk action is allowed "
                "automatically."
            ),
        )

    if (
        risk == "medium"
        and approved
    ):

        return PermissionDecision(
            allowed=True,
            requires_approval=False,
            risk=risk,
            reason=(
                "Medium-risk action was "
                "explicitly approved."
            ),
        )

    if risk == "medium":

        return PermissionDecision(
            allowed=False,
            requires_approval=True,
            risk=risk,
            reason=(
                "Medium-risk action requires "
                "explicit approval."
            ),
        )

    if (
        risk == "high"
        and approved
    ):

        return PermissionDecision(
            allowed=True,
            requires_approval=False,
            risk=risk,
            reason=(
                "High-risk action was "
                "explicitly approved."
            ),
        )

    return PermissionDecision(
        allowed=False,
        requires_approval=True,
        risk="high",
        reason=(
            "High-risk action requires "
            "explicit approval."
        ),
    )


# ---------------------------------------------------------------------------
# Standalone Test
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    tests = (
        "python -m assistant.main",
        "pytest",
        "pip install requests",
        "git reset --hard",
        "Remove-Item -Recurse project",
    )

    print(
        "E.V.I.E. Permission Engine"
    )

    print(
        "---------------------------"
    )

    for command in tests:

        risk = classify_command_risk(
            command
        )

        decision = evaluate_permission(
            base_risk="low",
            escalated_risk=risk,
        )

        print()

        print(
            "Command:",
            command,
        )

        print(
            "Risk:",
            decision.risk,
        )

        print(
            "Allowed:",
            decision.allowed,
        )

        print(
            "Approval required:",
            decision.requires_approval,
        )