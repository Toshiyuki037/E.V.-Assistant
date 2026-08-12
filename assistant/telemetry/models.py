from __future__ import annotations

from dataclasses import (
    dataclass,
    field,
)

from time import (
    perf_counter,
)

from typing import (
    Any,
)


@dataclass
class TimingSpan:
    name: str
    started_at: float
    ended_at: float | None = None
    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    @property
    def duration(self) -> float | None:
        if self.ended_at is None:
            return None

        return (
            self.ended_at
            - self.started_at
        )


@dataclass
class RequestTelemetry:
    request_id: str
    user_text: str
    started_at: float = field(
        default_factory=perf_counter
    )
    finished_at: float | None = None
    spans: list[TimingSpan] = field(
        default_factory=list
    )
    marks: dict[str, float] = field(
        default_factory=dict
    )
    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    @property
    def total_duration(self) -> float | None:
        if self.finished_at is None:
            return None

        return (
            self.finished_at
            - self.started_at
        )