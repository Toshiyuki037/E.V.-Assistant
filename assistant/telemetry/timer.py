from __future__ import annotations

from contextlib import (
    contextmanager,
)

from contextvars import (
    ContextVar,
)

from time import (
    perf_counter,
)

from uuid import (
    uuid4,
)

from .models import (
    RequestTelemetry,
    TimingSpan,
)


_CURRENT_REQUEST: ContextVar[
    RequestTelemetry | None
] = ContextVar(
    "evie_current_request_telemetry",
    default=None,
)


def start_request(
    user_text: str,
) -> RequestTelemetry:
    telemetry = RequestTelemetry(
        request_id=
            uuid4().hex,
        user_text=
            str(
                user_text
            ),
    )

    _CURRENT_REQUEST.set(
        telemetry
    )

    telemetry.marks[
        "request_received"
    ] = perf_counter()

    return telemetry


def current_request():
    return _CURRENT_REQUEST.get()


def mark(
    name: str,
):
    telemetry = current_request()

    if telemetry is None:
        return

    telemetry.marks[
        str(
            name
        )
    ] = perf_counter()


@contextmanager
def span(
    name: str,
    **metadata,
):
    telemetry = current_request()

    if telemetry is None:
        yield
        return

    item = TimingSpan(
        name=
            str(
                name
            ),
        started_at=
            perf_counter(),
        metadata=
            dict(
                metadata
            ),
    )

    telemetry.spans.append(
        item
    )

    try:
        yield item

    finally:
        item.ended_at = (
            perf_counter()
        )


def finish_request():
    telemetry = current_request()

    if telemetry is None:
        return None

    telemetry.finished_at = (
        perf_counter()
    )

    return telemetry


def clear_request():
    _CURRENT_REQUEST.set(
        None
    )