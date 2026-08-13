"""
E.V.I.E. - Performance Health

Phase 15E — Telemetry Performance Analysis

Purpose:
    Converts persisted request telemetry into useful health information.

Design:
    - read-only
    - no model/API calls
    - resilient to corrupt telemetry files
    - reports median / p95 / slowest spans
"""

from __future__ import annotations

import json
import math

from dataclasses import (
    dataclass,
    field,
)

from pathlib import (
    Path,
)

from statistics import (
    median,
)

from typing import (
    Any,
)


PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[2]
)

TELEMETRY_DIRECTORY = (
    PROJECT_ROOT
    / "runtime"
    / "telemetry"
)


@dataclass
class PerformanceSummary:
    request_count: int = 0

    median_total_seconds: float | None = None

    p95_total_seconds: float | None = None

    slowest_total_seconds: float | None = None

    median_time_to_first_sentence: float | None = None

    median_time_to_first_audio: float | None = None

    span_medians: dict[str, float] = field(
        default_factory=dict
    )

    primary_bottleneck: str = ""

    slow_request_count: int = 0

    corrupt_file_count: int = 0

    metadata: dict[str, Any] = field(
        default_factory=dict
    )


def _percentile(
    values: list[float],
    percentile: float,
):
    if not values:
        return None

    ordered = sorted(
        float(
            value
        )
        for value
        in values
    )

    if len(
        ordered
    ) == 1:
        return ordered[
            0
        ]

    position = (
        (
            len(
                ordered
            )
            - 1
        )
        * percentile
    )

    lower = math.floor(
        position
    )

    upper = math.ceil(
        position
    )

    if lower == upper:
        return ordered[
            lower
        ]

    weight = (
        position
        - lower
    )

    return (
        ordered[
            lower
        ]
        * (
            1.0
            - weight
        )
        + ordered[
            upper
        ]
        * weight
    )


def _safe_float(
    value,
):
    try:
        if value is None:
            return None

        return float(
            value
        )

    except (
        TypeError,
        ValueError,
    ):
        return None


def load_recent_telemetry(
    limit: int = 50,
):
    if not TELEMETRY_DIRECTORY.exists():
        return (
            [],
            0,
        )

    files = sorted(
        TELEMETRY_DIRECTORY.glob(
            "*.json"
        ),
        key=lambda path:
            path.stat().st_mtime,
        reverse=True,
    )[
        :max(
            1,
            int(
                limit
            ),
        )
    ]

    records = []

    corrupt = 0

    for path in files:

        try:
            payload = json.loads(
                path.read_text(
                    encoding="utf-8"
                )
            )

        except (
            OSError,
            json.JSONDecodeError,
        ):
            corrupt += 1

            continue

        if isinstance(
            payload,
            dict,
        ):
            records.append(
                payload
            )

        else:
            corrupt += 1

    return (
        records,
        corrupt,
    )


def _extract_mark(
    record: dict,
    name: str,
):
    marks = (
        record.get(
            "marks",
            {}
        )
        or {}
    )

    if not isinstance(
        marks,
        dict,
    ):
        return None

    return _safe_float(
        marks.get(
            name
        )
    )


def summarize_performance(
    records: list[dict],
    *,
    corrupt_file_count: int = 0,
    slow_request_threshold: float = 15.0,
):
    totals = []

    first_sentences = []

    first_audio = []

    span_values: dict[
        str,
        list[float],
    ] = {}


    for record in records:

        total = _safe_float(
            record.get(
                "total_seconds"
            )
        )

        if total is not None:
            totals.append(
                total
            )


        sentence = _extract_mark(
            record,
            "first_authoritative_sentence",
        )

        if sentence is not None:
            first_sentences.append(
                sentence
            )


        audio = _extract_mark(
            record,
            "first_audio_started",
        )

        if audio is not None:
            first_audio.append(
                audio
            )


        spans = (
            record.get(
                "spans",
                []
            )
            or []
        )

        if not isinstance(
            spans,
            list,
        ):
            continue


        for span in spans:

            if not isinstance(
                span,
                dict,
            ):
                continue

            name = str(
                span.get(
                    "name",
                    ""
                )
            ).strip()

            seconds = _safe_float(
                span.get(
                    "seconds"
                )
            )

            if (
                not name
                or seconds is None
            ):
                continue

            span_values.setdefault(
                name,
                [],
            ).append(
                seconds
            )


    span_medians = {
        name:
            round(
                median(
                    values
                ),
                4,
            )

        for (
            name,
            values,
        )
        in span_values.items()

        if values
    }


    primary_bottleneck = ""

    if span_medians:

        primary_bottleneck = max(
            span_medians,
            key=
                span_medians.get,
        )


    slow_count = len(
        [
            value
            for value
            in totals
            if value
            >= slow_request_threshold
        ]
    )


    return PerformanceSummary(
        request_count=
            len(
                records
            ),

        median_total_seconds=(
            round(
                median(
                    totals
                ),
                4,
            )
            if totals
            else None
        ),

        p95_total_seconds=(
            round(
                _percentile(
                    totals,
                    0.95,
                ),
                4,
            )
            if totals
            else None
        ),

        slowest_total_seconds=(
            round(
                max(
                    totals
                ),
                4,
            )
            if totals
            else None
        ),

        median_time_to_first_sentence=(
            round(
                median(
                    first_sentences
                ),
                4,
            )
            if first_sentences
            else None
        ),

        median_time_to_first_audio=(
            round(
                median(
                    first_audio
                ),
                4,
            )
            if first_audio
            else None
        ),

        span_medians=
            span_medians,

        primary_bottleneck=
            primary_bottleneck,

        slow_request_count=
            slow_count,

        corrupt_file_count=
            int(
                corrupt_file_count
            ),

        metadata={
            "slow_request_threshold_seconds":
                slow_request_threshold,
        },
    )


def analyze_recent_performance(
    limit: int = 50,
):
    records, corrupt = (
        load_recent_telemetry(
            limit=
                limit
        )
    )

    return summarize_performance(
        records,
        corrupt_file_count=
            corrupt,
    )


def format_performance_report(
    summary: PerformanceSummary | None = None,
):
    if summary is None:
        summary = (
            analyze_recent_performance()
        )

    lines = [
        "E.V.I.E. PERFORMANCE HEALTH",
        "",
        f"Requests analyzed: {summary.request_count}",
    ]

    if summary.median_total_seconds is not None:
        lines.append(
            (
                "Median total latency: "
                f"{summary.median_total_seconds:.3f}s"
            )
        )

    if summary.p95_total_seconds is not None:
        lines.append(
            (
                "P95 total latency: "
                f"{summary.p95_total_seconds:.3f}s"
            )
        )

    if summary.slowest_total_seconds is not None:
        lines.append(
            (
                "Slowest request: "
                f"{summary.slowest_total_seconds:.3f}s"
            )
        )

    if (
        summary.median_time_to_first_sentence
        is not None
    ):
        lines.append(
            (
                "Median first sentence: "
                f"{summary.median_time_to_first_sentence:.3f}s"
            )
        )

    if (
        summary.median_time_to_first_audio
        is not None
    ):
        lines.append(
            (
                "Median first audio: "
                f"{summary.median_time_to_first_audio:.3f}s"
            )
        )

    lines.append(
        (
            "Slow requests: "
            f"{summary.slow_request_count}"
        )
    )

    if summary.primary_bottleneck:
        lines.append(
            (
                "Primary bottleneck: "
                f"{summary.primary_bottleneck}"
            )
        )

    if summary.span_medians:
        lines.extend(
            [
                "",
                "Median spans:",
            ]
        )

        for (
            name,
            seconds,
        ) in sorted(
            summary.span_medians.items(),
            key=lambda item:
                item[
                    1
                ],
            reverse=True,
        ):
            lines.append(
                f"  {name}: {seconds:.3f}s"
            )

    if summary.corrupt_file_count:
        lines.append(
            (
                "Corrupt telemetry files skipped: "
                f"{summary.corrupt_file_count}"
            )
        )

    return "\n".join(
        lines
    )
