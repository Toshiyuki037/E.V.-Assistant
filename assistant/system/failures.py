"""
E.V.I.E. - Failure Tracking

Phase 15C — Deep Diagnostics & Failure State

Purpose:
    Persist lightweight component failure/success history without changing
    the behavior of the underlying V1 systems.

Security:
    Diagnostic records must never contain credentials, tokens, or secret values.
"""

from __future__ import annotations

import json

from dataclasses import (
    asdict,
    dataclass,
)

from datetime import (
    datetime,
    timezone,
)

from pathlib import (
    Path,
)

from typing import (
    Any,
)


PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[2]
)

RUNTIME_DIRECTORY = (
    PROJECT_ROOT
    / "runtime"
    / "health"
)

FAILURE_STATE_FILE = (
    RUNTIME_DIRECTORY
    / "component_state.json"
)


@dataclass
class ComponentFailureState:
    component: str

    last_status: str = "UNKNOWN"

    last_error: str = ""

    last_failure_at: str = ""

    last_success_at: str = ""

    failure_count: int = 0

    consecutive_failures: int = 0

    metadata: dict[str, Any] | None = None


def _now_iso():
    return (
        datetime.now(
            timezone.utc
        )
        .isoformat()
    )


def ensure_health_runtime():
    RUNTIME_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )


def _load_raw_state():
    ensure_health_runtime()

    if not FAILURE_STATE_FILE.exists():
        return {}

    try:
        payload = json.loads(
            FAILURE_STATE_FILE.read_text(
                encoding="utf-8"
            )
        )
    except (
        OSError,
        json.JSONDecodeError,
    ):
        return {}

    return (
        payload
        if isinstance(
            payload,
            dict,
        )
        else {}
    )


def _save_raw_state(
    state: dict,
):
    ensure_health_runtime()

    FAILURE_STATE_FILE.write_text(
        json.dumps(
            state,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def get_component_state(
    component: str,
):
    key = (
        str(
            component
        )
        .strip()
        .lower()
    )

    raw = (
        _load_raw_state()
        .get(
            key
        )
    )

    if not isinstance(
        raw,
        dict,
    ):
        return ComponentFailureState(
            component=
                key,
        )

    return ComponentFailureState(
        component=
            key,

        last_status=
            str(
                raw.get(
                    "last_status",
                    "UNKNOWN",
                )
            ),

        last_error=
            str(
                raw.get(
                    "last_error",
                    "",
                )
            ),

        last_failure_at=
            str(
                raw.get(
                    "last_failure_at",
                    "",
                )
            ),

        last_success_at=
            str(
                raw.get(
                    "last_success_at",
                    "",
                )
            ),

        failure_count=
            int(
                raw.get(
                    "failure_count",
                    0,
                )
            ),

        consecutive_failures=
            int(
                raw.get(
                    "consecutive_failures",
                    0,
                )
            ),

        metadata=
            dict(
                raw.get(
                    "metadata",
                    {},
                )
                or {}
            ),
    )


def record_component_failure(
    component: str,
    error: str,
    *,
    status: str = "DEGRADED",
    metadata: dict | None = None,
):
    key = (
        str(
            component
        )
        .strip()
        .lower()
    )

    state = (
        get_component_state(
            key
        )
    )

    state.last_status = (
        str(
            status
        )
    )

    state.last_error = (
        str(
            error
            or ""
        )
        .strip()
    )

    state.last_failure_at = (
        _now_iso()
    )

    state.failure_count += 1

    state.consecutive_failures += 1

    state.metadata = (
        dict(
            metadata
            or {}
        )
    )

    raw = (
        _load_raw_state()
    )

    raw[
        key
    ] = asdict(
        state
    )

    _save_raw_state(
        raw
    )

    return state


def record_component_success(
    component: str,
    *,
    metadata: dict | None = None,
):
    key = (
        str(
            component
        )
        .strip()
        .lower()
    )

    state = (
        get_component_state(
            key
        )
    )

    state.last_status = (
        "HEALTHY"
    )

    state.last_error = ""

    state.last_success_at = (
        _now_iso()
    )

    state.consecutive_failures = 0

    state.metadata = (
        dict(
            metadata
            or {}
        )
    )

    raw = (
        _load_raw_state()
    )

    raw[
        key
    ] = asdict(
        state
    )

    _save_raw_state(
        raw
    )

    return state


def list_component_states():
    raw = (
        _load_raw_state()
    )

    return [
        get_component_state(
            key
        )

        for key
        in sorted(
            raw
        )
    ]


def clear_component_state(
    component: str,
):
    key = (
        str(
            component
        )
        .strip()
        .lower()
    )

    raw = (
        _load_raw_state()
    )

    existed = (
        key
        in raw
    )

    if existed:
        del raw[
            key
        ]

        _save_raw_state(
            raw
        )

    return existed


def clear_all_component_states():
    _save_raw_state(
        {}
    )

    return True
