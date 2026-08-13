"""
E.V.I.E. - System Certification

Phase 15L — Final Certification / Freeze

Purpose:
    Produces one authoritative certification result for the completed
    Phase 15 maintenance, health, diagnostics, self-awareness, ownership,
    self-repair bridge, and backup/integrity architecture.

Important:
    This module does not add new assistant behavior.
    It validates the Phase 15 foundation and determines whether the system
    is healthy enough to freeze as a stable checkpoint.
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

from .backup import (
    validate_memory_database,
)

from .component_health import (
    run_component_health_checks,
)

from .deep_diagnostics import (
    run_deep_diagnostic,
)

from .health import (
    DEGRADED,
    HEALTHY,
    UNKNOWN,
    UNAVAILABLE,
    HealthResult,
    overall_health_status,
    run_quick_health_check,
)

from .ownership import (
    list_ownership_records,
)

from .performance import (
    analyze_recent_performance,
)

from .self_awareness import (
    get_self_awareness,
)


CERTIFIED = "CERTIFIED"
DEGRADED_CERTIFICATION = "DEGRADED"
FAILED = "FAILED"


@dataclass
class CertificationCheck:
    name: str

    status: str

    detail: str = ""

    metadata: dict[str, Any] = field(
        default_factory=dict
    )


@dataclass
class CertificationResult:
    status: str

    checks: list[
        CertificationCheck
    ] = field(
        default_factory=list
    )

    summary: str = ""

    metadata: dict[str, Any] = field(
        default_factory=dict
    )


def certification_to_dict(
    result: CertificationResult,
):
    return asdict(
        result
    )


def _check_phase15_self_awareness():
    identity = (
        get_self_awareness(
            "identity"
        )
    )

    capabilities = (
        get_self_awareness(
            "capabilities"
        )
    )

    if not (
        identity.success
        and capabilities.success
    ):
        return CertificationCheck(
            name=
                "self_awareness",

            status=
                DEGRADED,

            detail=
                "Self-awareness interface did not return authoritative identity/capabilities.",
        )

    return CertificationCheck(
        name=
            "self_awareness",

        status=
            HEALTHY,

        detail=
            "Authoritative identity and capability self-awareness is available.",
    )


def _check_ownership_map():
    records = (
        list_ownership_records()
    )

    if len(
        records
    ) < 10:

        return CertificationCheck(
            name=
                "architecture_ownership",

            status=
                DEGRADED,

            detail=
                "Architecture ownership registry is unexpectedly sparse.",

            metadata={
                "record_count":
                    len(
                        records
                    ),
            },
        )

    return CertificationCheck(
        name=
            "architecture_ownership",

        status=
            HEALTHY,

        detail=
            f"{len(records)} ownership records available.",

        metadata={
            "record_count":
                len(
                    records
                ),
        },
    )


def _check_backup_integrity():
    memory_integrity = (
        validate_memory_database()
    )

    return CertificationCheck(
        name=
            "backup_integrity",

        status=(
            HEALTHY
            if memory_integrity.success
            else DEGRADED
        ),

        detail=
            memory_integrity.detail,

        metadata={
            "component":
                memory_integrity.component,
        },
    )


def _check_performance_health():
    summary = (
        analyze_recent_performance()
    )

    if summary.request_count <= 0:

        return CertificationCheck(
            name=
                "performance_health",

            status=
                UNKNOWN,

            detail=
                "No telemetry records available for performance certification.",
        )

    return CertificationCheck(
        name=
            "performance_health",

        status=
            HEALTHY,

        detail=(
            f"{summary.request_count} recent requests analyzed. "
            f"Primary bottleneck: "
            f"{summary.primary_bottleneck or 'unknown'}."
        ),

        metadata={
            "request_count":
                summary.request_count,

            "median_total_seconds":
                summary.median_total_seconds,

            "p95_total_seconds":
                summary.p95_total_seconds,

            "primary_bottleneck":
                summary.primary_bottleneck,
        },
    )


def _health_checks_to_certification(
    prefix: str,
    results: list[
        HealthResult
    ],
):
    return [
        CertificationCheck(
            name=
                f"{prefix}:{result.component}",

            status=
                result.status,

            detail=
                result.detail,

            metadata=
                dict(
                    result.metadata
                    or {}
                ),
        )

        for result
        in results
    ]


def _certification_status(
    checks: list[
        CertificationCheck
    ],
):
    statuses = {
        check.status
        for check
        in checks
    }

    if UNAVAILABLE in statuses:
        return FAILED

    if DEGRADED in statuses:
        return DEGRADED_CERTIFICATION

    # UNKNOWN should not fail certification outright if every tested
    # critical subsystem is otherwise healthy.
    return CERTIFIED


def run_system_certification(
    *,
    include_deep_diagnostics: bool = True,
    include_expensive_models: bool = True,
):
    checks = []


    quick_results = (
        run_quick_health_check()
    )

    checks.extend(
        _health_checks_to_certification(
            "quick",
            quick_results,
        )
    )


    component_results = (
        run_component_health_checks()
    )

    checks.extend(
        _health_checks_to_certification(
            "component",
            component_results,
        )
    )


    if include_deep_diagnostics:

        deep = (
            run_deep_diagnostic(
                include_expensive_models=
                    include_expensive_models,
            )
        )

        checks.extend(
            _health_checks_to_certification(
                "deep",
                deep.results,
            )
        )


    checks.append(
        _check_phase15_self_awareness()
    )

    checks.append(
        _check_ownership_map()
    )

    checks.append(
        _check_backup_integrity()
    )

    checks.append(
        _check_performance_health()
    )


    status = (
        _certification_status(
            checks
        )
    )


    degraded = [
        check.name

        for check
        in checks

        if check.status
        == DEGRADED
    ]


    unavailable = [
        check.name

        for check
        in checks

        if check.status
        == UNAVAILABLE
    ]


    unknown = [
        check.name

        for check
        in checks

        if check.status
        == UNKNOWN
    ]


    if status == CERTIFIED:

        summary = (
            "Phase 15 certification passed. "
            "The maintenance, health, diagnostics, self-awareness, "
            "ownership, repair-bridge, and integrity foundation is ready "
            "to freeze as a stable checkpoint."
        )

    elif status == DEGRADED_CERTIFICATION:

        summary = (
            "Phase 15 certification completed with degraded components. "
            "Review degraded checks before freezing."
        )

    else:

        summary = (
            "Phase 15 certification failed because one or more required "
            "components are unavailable."
        )


    return CertificationResult(
        status=
            status,

        checks=
            checks,

        summary=
            summary,

        metadata={
            "quick_overall":
                overall_health_status(
                    quick_results
                ),

            "degraded_checks":
                degraded,

            "unavailable_checks":
                unavailable,

            "unknown_checks":
                unknown,

            "check_count":
                len(
                    checks
                ),
        },
    )


def format_certification_report(
    certification: CertificationResult | None = None,
):
    if certification is None:

        certification = (
            run_system_certification()
        )


    lines = [
        "E.V.I.E. SYSTEM CERTIFICATION",
        "",
    ]


    for check in certification.checks:

        lines.append(
            f"{check.name:<46} {check.status}"
        )

        if check.detail:

            lines.append(
                f"  {check.detail}"
            )


    lines.extend(
        [
            "",
            (
                "Certification Status: "
                f"{certification.status}"
            ),
            "",
            certification.summary,
        ]
    )


    if certification.metadata.get(
        "degraded_checks"
    ):

        lines.extend(
            [
                "",
                "Degraded Checks:",
            ]
        )

        for name in certification.metadata[
            "degraded_checks"
        ]:

            lines.append(
                f"  - {name}"
            )


    if certification.metadata.get(
        "unavailable_checks"
    ):

        lines.extend(
            [
                "",
                "Unavailable Checks:",
            ]
        )

        for name in certification.metadata[
            "unavailable_checks"
        ]:

            lines.append(
                f"  - {name}"
            )


    if certification.metadata.get(
        "unknown_checks"
    ):

        lines.extend(
            [
                "",
                "Unknown Checks:",
            ]
        )

        for name in certification.metadata[
            "unknown_checks"
        ]:

            lines.append(
                f"  - {name}"
            )


    return "\n".join(
        lines
    )
