from assistant.system.deep_diagnostics import (
    DeepDiagnosticResult,
    _run_check,
    format_deep_diagnostic_report,
)

from assistant.system.health import (
    DEGRADED,
    HEALTHY,
    HealthResult,
)


def test_deep_check_isolation():
    result = (
        _run_check(
            "broken.component",
            lambda:
                (_ for _ in ())
                .throw(
                    RuntimeError(
                        "boom"
                    )
                ),
        )
    )

    assert result.status == DEGRADED
    assert "boom" in result.detail
    assert "diagnostic_seconds" in result.metadata


def test_deep_report_format():
    diagnostic = (
        DeepDiagnosticResult(
            results=[
                HealthResult(
                    "memory.database.deep",
                    HEALTHY,
                    "ok",
                    {
                        "diagnostic_seconds":
                            0.1,
                    },
                ),
            ],

            duration_seconds=
                0.1,

            overall=
                HEALTHY,
        )
    )

    report = (
        format_deep_diagnostic_report(
            diagnostic
        )
    )

    assert "E.V.I.E. DEEP DIAGNOSTIC" in report
    assert "memory.database.deep" in report
    assert "Overall: HEALTHY" in report
