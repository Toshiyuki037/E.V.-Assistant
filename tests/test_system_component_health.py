from assistant.system.component_health import (
    _with_failure_history,
)

from assistant.system.failures import (
    ComponentFailureState,
)

from assistant.system.health import (
    DEGRADED,
    HEALTHY,
    HealthResult,
)


def test_recent_failure_degrades_passive_health(
    monkeypatch,
):
    monkeypatch.setattr(
        "assistant.system.component_health.get_component_state",
        lambda component:
            ComponentFailureState(
                component=
                    component,

                last_status=
                    DEGRADED,

                last_error=
                    "runtime failure",

                failure_count=
                    3,

                consecutive_failures=
                    2,
            ),
    )

    result = (
        _with_failure_history(
            HealthResult(
                "computer.control",
                HEALTHY,
                "installed",
            )
        )
    )

    assert result.status == DEGRADED
    assert result.detail == "runtime failure"
    assert result.metadata["failure_count"] == 3
    assert result.metadata["consecutive_failures"] == 2
