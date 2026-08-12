
"""
E.V.I.E. - Public Unified Computer Control API

Phase 13J
"""

from __future__ import annotations

from .control_context import ControlContext
from .control_executor import execute_computer_control
from .control_models import ComputerControlRequest


def control_local_computer(
    action: str,
    *,
    target: str = "",
    arguments: dict | None = None,
    preferred_method: str = "",
    allow_vision: bool = True,
    approved: bool = False,
    browser_session=None,
):
    request = ComputerControlRequest(
        action=str(action),
        target=str(target or ""),
        arguments=dict(
            arguments
            or {}
        ),
        preferred_method=str(
            preferred_method
            or ""
        ),
        allow_vision=bool(
            allow_vision
        ),
        approved=bool(
            approved
        ),
    )

    context = ControlContext(
        request=request,
        browser_session=browser_session,
    )

    return execute_computer_control(
        request,
        context=context,
    ).to_dict()
