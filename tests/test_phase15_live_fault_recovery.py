"""
Controlled Phase 15 diagnostic fault test.

This does NOT damage a real subsystem. It records a real persisted health
failure against an existing component, verifies E.V.I.E. diagnoses it, then
records recovery and verifies health returns to normal.

Run manually:
    python -m pytest -q tests/test_phase15_live_fault_recovery.py -s
"""

from assistant.system.failures import (
    clear_component_state,
    record_component_failure,
    record_component_success,
)

from assistant.system.component_health import (
    check_tts,
)

from assistant.system.health import (
    DEGRADED,
    HEALTHY,
)


def test_phase15_persisted_fault_and_recovery():
    component = (
        "voice.tts"
    )

    clear_component_state(
        component
    )


    record_component_failure(
        component,
        "Controlled Phase 15 verification fault: TTS test failure.",
    )


    broken = (
        check_tts()
    )

    print(
        "\nBROKEN STATE:"
    )

    print(
        broken
    )

    assert broken.status == DEGRADED

    assert (
        "Controlled Phase 15 verification fault"
        in broken.detail
    )


    record_component_success(
        component
    )


    recovered = (
        check_tts()
    )

    print(
        "\nRECOVERED STATE:"
    )

    print(
        recovered
    )

    assert recovered.status == HEALTHY


    clear_component_state(
        component
    )
