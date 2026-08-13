from assistant.system import failures


def test_failure_success_lifecycle(
    monkeypatch,
    tmp_path,
):
    monkeypatch.setattr(
        failures,
        "RUNTIME_DIRECTORY",
        tmp_path,
    )

    monkeypatch.setattr(
        failures,
        "FAILURE_STATE_FILE",
        tmp_path / "component_state.json",
    )

    failures.record_component_failure(
        "google.calendar",
        "adapter mismatch",
    )

    state = failures.get_component_state(
        "google.calendar"
    )

    assert state.failure_count == 1
    assert state.consecutive_failures == 1
    assert state.last_error == "adapter mismatch"

    failures.record_component_success(
        "google.calendar"
    )

    state = failures.get_component_state(
        "google.calendar"
    )

    assert state.failure_count == 1
    assert state.consecutive_failures == 0
    assert state.last_error == ""
    assert state.last_success_at
