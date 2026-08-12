
"""
E.V.I.E. - Unified Control Policy

Phase 13J

This module decides:
- method priority
- whether fallback may continue
- whether an action requires approval
- whether vision is allowed
"""

from __future__ import annotations

from .capabilities import get_action_risk
from .control_models import (
    AttemptStatus,
    ControlMethod,
    ComputerControlRequest,
)
from .models import DeviceRisk


METHOD_ORDER = [
    ControlMethod.NATIVE,
    ControlMethod.INTEGRATION,
    ControlMethod.ACCESSIBILITY,
    ControlMethod.DOM,
    ControlMethod.VISION,
]


APPROVAL_RISKS = {
    DeviceRisk.MEDIUM,
    DeviceRisk.HIGH,
}


def risk_for_request(
    request: ComputerControlRequest,
) -> DeviceRisk:
    return get_action_risk(
        request.action
    )


def requires_approval(
    request: ComputerControlRequest,
) -> bool:
    return (
        risk_for_request(request)
        in APPROVAL_RISKS
    )


def ensure_request_allowed(
    request: ComputerControlRequest,
):
    if (
        requires_approval(request)
        and not request.approved
    ):
        raise PermissionError(
            (
                "Computer control action requires explicit approval: "
                f"{request.action}"
            )
        )


def ordered_methods(
    request: ComputerControlRequest,
) -> list[ControlMethod]:
    methods = list(
        METHOD_ORDER
    )

    preferred = str(
        request.preferred_method
        or ""
    ).strip().lower()

    if preferred:
        try:
            preferred_method = ControlMethod(
                preferred
            )
        except ValueError:
            raise ValueError(
                f"Unknown preferred control method: {preferred}"
            )

        methods.remove(
            preferred_method
        )

        methods.insert(
            0,
            preferred_method,
        )

    if not request.allow_vision:
        methods = [
            method
            for method in methods
            if method != ControlMethod.VISION
        ]

    return methods


def may_fallback_after(
    status: AttemptStatus,
) -> bool:
    """
    Only absence/unsupported control permits fallback.

    Ambiguous targets, policy blocks, approval failures, and ordinary
    execution failures stop the chain instead of silently dropping to vision.
    """

    return status in {
        AttemptStatus.UNSUPPORTED,
        AttemptStatus.NOT_FOUND,
    }
