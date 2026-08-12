from __future__ import annotations

import json

from datetime import (
    datetime,
)

from pathlib import (
    Path,
)

from .models import (
    RequestTelemetry,
)


TELEMETRY_DIRECTORY = (
    Path("runtime")
    / "telemetry"
)


def _round_seconds(
    value,
):
    if value is None:
        return None

    return round(
        float(
            value
        ),
        4,
    )


def telemetry_to_dict(
    telemetry: RequestTelemetry,
):
    return {
        "request_id":
            telemetry.request_id,

        "user_text":
            telemetry.user_text,

        "total_seconds":
            _round_seconds(
                telemetry.total_duration
            ),

        "marks": {
            name:
                _round_seconds(
                    value
                    - telemetry.started_at
                )

            for name, value
            in telemetry.marks.items()
        },

        "spans": [
            {
                "name":
                    item.name,

                "seconds":
                    _round_seconds(
                        item.duration
                    ),

                "metadata":
                    item.metadata,
            }

            for item
            in telemetry.spans
        ],

        "metadata":
            telemetry.metadata,
    }


def persist_telemetry(
    telemetry: RequestTelemetry,
):
    TELEMETRY_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    stamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S_%f"
    )

    path = (
        TELEMETRY_DIRECTORY
        / (
            f"{stamp}_"
            f"{telemetry.request_id}.json"
        )
    )

    path.write_text(
        json.dumps(
            telemetry_to_dict(
                telemetry
            ),
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    return path


def print_latency_report(
    telemetry: RequestTelemetry,
):
    print()
    print("[Latency]")

    for item in telemetry.spans:

        if item.duration is None:
            continue

        print(
            f"{item.name}: "
            f"{item.duration:.3f}s"
        )

    if telemetry.total_duration is not None:

        print(
            "total: "
            f"{telemetry.total_duration:.3f}s"
        )