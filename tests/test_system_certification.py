from assistant.system.certification import (
    CERTIFIED,
    DEGRADED_CERTIFICATION,
    FAILED,
    CertificationCheck,
    CertificationResult,
    _certification_status,
    format_certification_report,
)

from assistant.system.health import (
    DEGRADED,
    HEALTHY,
    UNKNOWN,
    UNAVAILABLE,
)


def test_certification_status_healthy():
    checks = [
        CertificationCheck(
            "a",
            HEALTHY,
        ),
        CertificationCheck(
            "b",
            HEALTHY,
        ),
    ]

    assert (
        _certification_status(
            checks
        )
        == CERTIFIED
    )


def test_certification_status_unknown_does_not_fail():
    checks = [
        CertificationCheck(
            "a",
            HEALTHY,
        ),
        CertificationCheck(
            "b",
            UNKNOWN,
        ),
    ]

    assert (
        _certification_status(
            checks
        )
        == CERTIFIED
    )


def test_certification_status_degraded():
    checks = [
        CertificationCheck(
            "a",
            HEALTHY,
        ),
        CertificationCheck(
            "b",
            DEGRADED,
        ),
    ]

    assert (
        _certification_status(
            checks
        )
        == DEGRADED_CERTIFICATION
    )


def test_certification_status_unavailable_fails():
    checks = [
        CertificationCheck(
            "a",
            HEALTHY,
        ),
        CertificationCheck(
            "b",
            UNAVAILABLE,
        ),
    ]

    assert (
        _certification_status(
            checks
        )
        == FAILED
    )


def test_certification_report():
    result = (
        CertificationResult(
            status=
                CERTIFIED,

            checks=[
                CertificationCheck(
                    "memory",
                    HEALTHY,
                    "ok",
                ),
            ],

            summary=
                "Certification passed.",

            metadata={
                "degraded_checks":
                    [],

                "unavailable_checks":
                    [],

                "unknown_checks":
                    [],
            },
        )
    )

    report = (
        format_certification_report(
            result
        )
    )

    assert "E.V.I.E. SYSTEM CERTIFICATION" in report
    assert "Certification Status: CERTIFIED" in report
    assert "Certification passed." in report
