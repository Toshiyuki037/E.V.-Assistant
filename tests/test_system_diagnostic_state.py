from assistant.system.diagnostic_state import (
    format_diagnostic_snapshot,
)

from assistant.system.failures import (
    ComponentFailureState,
)

from assistant.system.health import (
    DEGRADED,
    HEALTHY,
    HealthResult,
)


def test_snapshot_formatting():
    snapshot = {
        "overall":
            DEGRADED,

        "results": [
            HealthResult(
                "memory.database",
                HEALTHY,
                "ok",
            ),
            HealthResult(
                "google.calendar",
                DEGRADED,
                "adapter mismatch",
            ),
        ],

        "failure_history": [
            ComponentFailureState(
                component=
                    "google.calendar",

                last_status=
                    DEGRADED,

                last_error=
                    "adapter mismatch",

                failure_count=
                    2,

                consecutive_failures=
                    2,
            )
        ],
    }

    report = (
        format_diagnostic_snapshot(
            snapshot
        )
    )

    assert "E.V.I.E. DIAGNOSTIC SNAPSHOT" in report
    assert "google.calendar" in report
    assert "adapter mismatch" in report
    assert "Overall: DEGRADED" in report
