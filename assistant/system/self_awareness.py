"""
E.V.I.E. - Self Awareness Interface

Phase 15G

Purpose:
    Provides an authoritative, read-only interface for questions about
    E.V.I.E.'s identity, version, capabilities, health, diagnostics,
    performance, architecture, integrations, and limitations.

Important:
    This layer should answer from runtime truth and the system manifest,
    not from conversational memory or model guesswork.
"""

from __future__ import annotations

from dataclasses import (
    asdict,
    dataclass,
    field,
)

from typing import (
    Any,
)

from .manifest import (
    EVIE_VERSION,
    get_capability,
    get_system_manifest,
    list_capabilities,
)

from .health import (
    health_summary,
)

from .diagnostic_state import (
    run_diagnostic_snapshot,
)

from .deep_diagnostics import (
    run_deep_diagnostic,
)

from .performance import (
    analyze_recent_performance,
)


@dataclass
class SelfAwarenessResult:
    topic: str

    success: bool

    summary: str

    data: dict[str, Any] = field(
        default_factory=dict
    )

    source: str = "system"


def self_awareness_result_to_dict(
    result: SelfAwarenessResult,
):
    return asdict(
        result
    )


def _normalise_topic(
    topic: str,
):
    return (
        str(
            topic
            or ""
        )
        .strip()
        .lower()
        .replace(
            "-",
            "_",
        )
        .replace(
            " ",
            "_",
        )
    )


def get_identity():
    manifest = (
        get_system_manifest()
    )

    summary = (
        f"{manifest['name']} version "
        f"{manifest['version']}, "
        f"{manifest['release']}."
    )

    return SelfAwarenessResult(
        topic=
            "identity",

        success=
            True,

        summary=
            summary,

        data={
            "name":
                manifest[
                    "name"
                ],

            "version":
                manifest[
                    "version"
                ],

            "release":
                manifest[
                    "release"
                ],

            "current_phase":
                manifest[
                    "current_phase"
                ],

            "completed_phases":
                manifest[
                    "completed_phases"
                ],
        },

        source=
            "manifest",
    )


def get_version():
    return SelfAwarenessResult(
        topic=
            "version",

        success=
            True,

        summary=
            f"E.V.I.E. is running version {EVIE_VERSION}.",

        data={
            "version":
                EVIE_VERSION,
        },

        source=
            "manifest",
    )


def get_phases():
    manifest = (
        get_system_manifest()
    )

    completed = (
        manifest[
            "completed_phases"
        ]
    )

    current = (
        manifest[
            "current_phase"
        ]
    )

    summary = (
        f"Phases 1 through {max(completed)} are complete. "
        f"Current development phase: {current}."
    )

    return SelfAwarenessResult(
        topic=
            "phases",

        success=
            True,

        summary=
            summary,

        data={
            "completed_phases":
                completed,

            "current_phase":
                current,
        },

        source=
            "manifest",
    )


def get_capabilities(
    *,
    supported_only: bool = True,
):
    capabilities = (
        list_capabilities(
            supported_only=
                supported_only,
        )
    )

    names = (
        sorted(
            capabilities
        )
    )

    summary = (
        "Supported capabilities: "
        + ", ".join(
            names
        )
        + "."
    )

    return SelfAwarenessResult(
        topic=
            "capabilities",

        success=
            True,

        summary=
            summary,

        data={
            "capabilities":
                capabilities,

            "count":
                len(
                    capabilities
                ),
        },

        source=
            "manifest",
    )


def get_capability_status(
    capability_name: str,
):
    capability = (
        get_capability(
            capability_name
        )
    )

    if capability is None:

        return SelfAwarenessResult(
            topic=
                "capability",

            success=
                False,

            summary=(
                f"No authoritative capability named "
                f"{capability_name!r} is registered."
            ),

            data={
                "capability":
                    capability_name,
            },

            source=
                "manifest",
        )


    supported = bool(
        capability.get(
            "supported",
            False,
        )
    )


    return SelfAwarenessResult(
        topic=
            "capability",

        success=
            True,

        summary=(
            f"{capability_name}: "
            f"{'supported' if supported else 'not currently supported'}. "
            f"{capability.get('description', '')}"
        ).strip(),

        data={
            "capability":
                capability_name,

            "supported":
                supported,

            "definition":
                capability,
        },

        source=
            "manifest",
    )


def get_integrations():
    manifest = (
        get_system_manifest()
    )

    integrations = (
        manifest.get(
            "integrations",
            {}
        )
        or {}
    )

    providers = (
        sorted(
            integrations
        )
    )

    summary = (
        "Configured integration families: "
        + ", ".join(
            providers
        )
        + "."
    )

    return SelfAwarenessResult(
        topic=
            "integrations",

        success=
            True,

        summary=
            summary,

        data={
            "integrations":
                integrations,

            "providers":
                providers,
        },

        source=
            "manifest",
    )


def get_limitations():
    manifest = (
        get_system_manifest()
    )

    limitations = (
        list(
            manifest.get(
                "known_limitations",
                [],
            )
            or []
        )
    )

    summary = (
        "Known limitations: "
        + (
            " ".join(
                limitations
            )
            if limitations
            else "No known limitations are currently listed."
        )
    )

    return SelfAwarenessResult(
        topic=
            "limitations",

        success=
            True,

        summary=
            summary,

        data={
            "limitations":
                limitations,
        },

        source=
            "manifest",
    )


def get_health():
    summary_data = (
        health_summary()
    )

    overall = (
        summary_data.get(
            "overall",
            "UNKNOWN",
        )
    )

    components = (
        summary_data.get(
            "components",
            [],
        )
        or []
    )

    unhealthy = [
        item

        for item
        in components

        if item.get(
            "status"
        )
        not in {
            "HEALTHY",
        }
    ]

    summary = (
        f"Overall system health: {overall}."
    )

    if unhealthy:

        summary += (
            f" {len(unhealthy)} component checks "
            f"are not fully healthy."
        )

    return SelfAwarenessResult(
        topic=
            "health",

        success=
            True,

        summary=
            summary,

        data=
            summary_data,

        source=
            "health_engine",
    )


def get_diagnostics():
    snapshot = (
        run_diagnostic_snapshot()
    )

    results = [
        {
            "component":
                result.component,

            "status":
                result.status,

            "detail":
                result.detail,

            "metadata":
                result.metadata,
        }

        for result
        in snapshot[
            "results"
        ]
    ]

    failures = [
        {
            "component":
                state.component,

            "last_status":
                state.last_status,

            "last_error":
                state.last_error,

            "last_failure_at":
                state.last_failure_at,

            "last_success_at":
                state.last_success_at,

            "failure_count":
                state.failure_count,

            "consecutive_failures":
                state.consecutive_failures,
        }

        for state
        in snapshot.get(
            "failure_history",
            [],
        )
    ]

    summary = (
        f"Diagnostic snapshot overall status: "
        f"{snapshot['overall']}."
    )

    return SelfAwarenessResult(
        topic=
            "diagnostics",

        success=
            True,

        summary=
            summary,

        data={
            "overall":
                snapshot[
                    "overall"
                ],

            "results":
                results,

            "failure_history":
                failures,
        },

        source=
            "diagnostic_state",
    )


def get_deep_diagnostics(
    *,
    include_expensive_models: bool = True,
):
    diagnostic = (
        run_deep_diagnostic(
            include_expensive_models=
                include_expensive_models,
        )
    )

    results = [
        {
            "component":
                result.component,

            "status":
                result.status,

            "detail":
                result.detail,

            "metadata":
                result.metadata,
        }

        for result
        in diagnostic.results
    ]

    summary = (
        f"Deep diagnostic overall status: "
        f"{diagnostic.overall}. "
        f"Completed in "
        f"{diagnostic.duration_seconds:.3f} seconds."
    )

    return SelfAwarenessResult(
        topic=
            "deep_diagnostics",

        success=
            True,

        summary=
            summary,

        data={
            "overall":
                diagnostic.overall,

            "duration_seconds":
                diagnostic.duration_seconds,

            "results":
                results,

            "metadata":
                diagnostic.metadata,
        },

        source=
            "deep_diagnostics",
    )


def get_performance():
    performance = (
        analyze_recent_performance()
    )

    bottleneck = (
        performance.primary_bottleneck
        or "unknown"
    )

    summary = (
        f"Primary measured bottleneck: "
        f"{bottleneck}."
    )

    if performance.median_total_seconds is not None:

        summary += (
            f" Median total latency is "
            f"{performance.median_total_seconds:.3f} seconds."
        )

    return SelfAwarenessResult(
        topic=
            "performance",

        success=
            True,

        summary=
            summary,

        data={
            "request_count":
                performance.request_count,

            "median_total_seconds":
                performance.median_total_seconds,

            "p95_total_seconds":
                performance.p95_total_seconds,

            "slowest_total_seconds":
                performance.slowest_total_seconds,

            "median_time_to_first_sentence":
                performance.median_time_to_first_sentence,

            "median_time_to_first_audio":
                performance.median_time_to_first_audio,

            "span_medians":
                performance.span_medians,

            "primary_bottleneck":
                performance.primary_bottleneck,

            "slow_request_count":
                performance.slow_request_count,

            "corrupt_file_count":
                performance.corrupt_file_count,
        },

        source=
            "telemetry",
    )


def get_self_awareness(
    topic: str,
    **kwargs,
):
    normalized = (
        _normalise_topic(
            topic
        )
    )


    routes = {
        "identity":
            get_identity,

        "version":
            get_version,

        "phases":
            get_phases,

        "capabilities":
            get_capabilities,

        "integrations":
            get_integrations,

        "limitations":
            get_limitations,

        "health":
            get_health,

        "diagnostics":
            get_diagnostics,

        "performance":
            get_performance,
    }


    if normalized in {
        "deep_diagnostic",
        "deep_diagnostics",
    }:

        return get_deep_diagnostics(
            **kwargs
        )


    function = (
        routes.get(
            normalized
        )
    )


    if function is None:

        return SelfAwarenessResult(
            topic=
                normalized
                or "unknown",

            success=
                False,

            summary=(
                "Unknown self-awareness topic."
            ),

            data={
                "requested_topic":
                    topic,
            },

            source=
                "system",
        )


    return function(
        **kwargs
    )
