
"""
E.V.I.E. - Deterministic Computer Request Planner

Phase 13L

Purpose:
Recognize a bounded set of explicit computer-control requests without needing
an LLM round trip.

The generic tool planner can still select the computer tool for broader
phrasing later, but this deterministic layer gives us stable regression
coverage for common direct commands.
"""

from __future__ import annotations

import re

from .integration_models import ComputerToolPlan


def _clean(message: str) -> str:
    return " ".join(
        str(message or "")
        .strip()
        .split()
    )


def _lower(message: str) -> str:
    return _clean(message).lower()


def plan_computer_message(
    message: str,
) -> ComputerToolPlan:
    text = _clean(message)
    lower = text.lower()

    if not text:
        return ComputerToolPlan(
            handled=False
        )

    # ---------------------------------------------------------
    # Window focus
    # ---------------------------------------------------------

    match = re.match(
        r"^(?:focus|bring(?: up| forward)?|switch to)\s+(.+)$",
        text,
        flags=re.IGNORECASE,
    )

    if match:
        target = match.group(1).strip()

        return ComputerToolPlan(
            handled=True,
            action="window.focus",
            target=target,
            confidence=96,
            rationale="Explicit window-focus request.",
        )

    # ---------------------------------------------------------
    # Application launch
    # ---------------------------------------------------------

    match = re.match(
        r"^(?:open|launch|start)\s+(.+)$",
        text,
        flags=re.IGNORECASE,
    )

    if match:
        target = match.group(1).strip()

        # Avoid greedily claiming settings requests handled below.
        if " settings" not in lower and not lower.endswith("settings"):
            return ComputerToolPlan(
                handled=True,
                action="application.launch",
                target=target,
                confidence=92,
                rationale="Explicit application-launch request.",
            )

    # ---------------------------------------------------------
    # Settings
    # ---------------------------------------------------------

    match = re.match(
        r"^(?:open|show)\s+(.+?)\s+settings$",
        text,
        flags=re.IGNORECASE,
    )

    if match:
        page = (
            match.group(1)
            .strip()
            .lower()
            .replace(" ", "_")
        )

        aliases = {
            "display": "display",
            "sound": "sound",
            "audio": "sound",
            "bluetooth": "bluetooth",
            "wifi": "wifi",
            "wi-fi": "wifi",
            "network": "network",
            "notifications": "notifications",
            "storage": "storage",
            "camera": "camera_privacy",
            "microphone": "microphone_privacy",
            "windows_update": "windows_update",
            "update": "windows_update",
        }

        page = aliases.get(
            page,
            page,
        )

        return ComputerToolPlan(
            handled=True,
            action="settings.open",
            target=page,
            confidence=98,
            rationale="Explicit Windows Settings request.",
        )

    # ---------------------------------------------------------
    # Clipboard write
    # ---------------------------------------------------------

    match = re.match(
        r"^(?:copy|put)\s+(.+?)\s+(?:to|on)\s+(?:my\s+)?clipboard$",
        text,
        flags=re.IGNORECASE,
    )

    if match:
        value = match.group(1)

        return ComputerToolPlan(
            handled=True,
            action="clipboard.write",
            arguments={
                "text": value,
            },
            approved=True,
            confidence=94,
            rationale="Explicit clipboard-write request.",
        )

    # ---------------------------------------------------------
    # Notepad / accessible UI typing
    # ---------------------------------------------------------

    match = re.match(
        r"^(?:type|write)\s+(.+?)\s+(?:into|in)\s+(.+)$",
        text,
        flags=re.IGNORECASE,
    )

    if match:
        value = match.group(1)
        target = match.group(2).strip()

        return ComputerToolPlan(
            handled=True,
            action="accessibility.set_value",
            target=target,
            arguments={
                "value": value,
                "selector": {
                    "control_type": "Document",
                },
            },
            approved=True,
            confidence=87,
            rationale=(
                "Explicit structured UI text-entry request. "
                "Phase 13J will choose the accessibility/native HWND path."
            ),
        )

    # ---------------------------------------------------------
    # Screen capture
    # ---------------------------------------------------------

    if lower in {
        "capture my screen",
        "capture the screen",
        "take a screenshot",
        "screenshot my screen",
    }:
        return ComputerToolPlan(
            handled=True,
            action="vision.capture",
            arguments={},
            confidence=97,
            rationale="Explicit screen-capture request.",
        )

    return ComputerToolPlan(
        handled=False
    )
