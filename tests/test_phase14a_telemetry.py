import time

from assistant.telemetry.models import (
    RequestTelemetry,
)

from assistant.telemetry.reporter import (
    telemetry_to_dict,
)

from assistant.telemetry.timer import (
    clear_request,
    current_request,
    finish_request,
    mark,
    span,
    start_request,
)


def test_request_telemetry_lifecycle():
    clear_request()

    telemetry = start_request(
        "hello"
    )

    assert current_request() is telemetry

    mark(
        "routing"
    )

    with span(
        "test_span"
    ):
        time.sleep(
            0.01
        )

    finished = finish_request()

    assert finished is telemetry
    assert finished.total_duration is not None
    assert finished.total_duration >= 0

    assert (
        finished.spans[0].name
        == "test_span"
    )

    assert (
        finished.spans[0].duration
        is not None
    )

    clear_request()

    assert current_request() is None


def test_telemetry_serialization():
    telemetry = RequestTelemetry(
        request_id="abc",
        user_text="test",
    )

    telemetry.finished_at = (
        telemetry.started_at
        + 1.25
    )

    data = telemetry_to_dict(
        telemetry
    )

    assert data["request_id"] == "abc"
    assert data["total_seconds"] == 1.25