
"""
E.V.I.E. - Phase 13 Hardening Checks

Phase 13L

Pure helpers used by tests and diagnostics.
"""

from __future__ import annotations

from .control_models import (
    AttemptStatus,
    ComputerControlResult,
)


def assert_safe_fallback_trace(
    result: ComputerControlResult,
):
    """
    Verify that a trace did not continue after a hard-stop condition.
    """

    hard_stop_seen = False

    for attempt in result.attempts:
        if hard_stop_seen:
            raise AssertionError(
                "Control trace continued after a hard-stop attempt."
            )

        if attempt.status in {
            AttemptStatus.AMBIGUOUS,
            AttemptStatus.BLOCKED,
            AttemptStatus.FAILED,
        }:
            hard_stop_seen = True

    return True


def summarize_control_result(
    result: ComputerControlResult,
) -> dict:
    return {
        "success": result.success,
        "method": result.method,
        "verified": result.verified,
        "attempt_count": len(
            result.attempts
        ),
        "attempts": [
            attempt.to_dict()
            for attempt in result.attempts
        ],
    }
