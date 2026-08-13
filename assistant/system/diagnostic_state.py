"""
E.V.I.E. - Phase 15C/D Diagnostic Aggregation

Adds failure-history and subsystem-level reporting on top of the Phase 15B
health engine.
"""

from __future__ import annotations

from .component_health import (
    run_component_health_checks,
)

from .failures import (
    list_component_states,
)

from .health import (
    run_quick_health_check,
    overall_health_status,
)


def run_diagnostic_snapshot():
    """
    Passive diagnostic snapshot.

    Does not intentionally invoke network APIs, model inference, or writes
    beyond existing health-state bookkeeping.
    """

    core = (
        run_quick_health_check()
    )

    components = (
        run_component_health_checks()
    )

    results = (
        core
        + components
    )

    return {
        "overall":
            overall_health_status(
                results
            ),

        "results":
            results,

        "failure_history":
            list_component_states(),
    }


def format_diagnostic_snapshot(
    snapshot=None,
):
    if snapshot is None:
        snapshot = (
            run_diagnostic_snapshot()
        )

    lines = [
        "E.V.I.E. DIAGNOSTIC SNAPSHOT",
        "",
    ]

    for result in snapshot[
        "results"
    ]:
        lines.append(
            f"{result.component:<30} {result.status}"
        )

        if result.detail:
            lines.append(
                f"  {result.detail}"
            )

    histories = (
        snapshot.get(
            "failure_history",
            []
        )
    )

    if histories:
        lines.extend(
            [
                "",
                "Recent Failure State",
            ]
        )

        for state in histories:
            lines.append(
                (
                    f"{state.component}: "
                    f"{state.last_status} "
                    f"(failures={state.failure_count}, "
                    f"consecutive={state.consecutive_failures})"
                )
            )

            if state.last_error:
                lines.append(
                    f"  {state.last_error}"
                )

    lines.extend(
        [
            "",
            f"Overall: {snapshot['overall']}",
        ]
    )

    return "\n".join(
        lines
    )
