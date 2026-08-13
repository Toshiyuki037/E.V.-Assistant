"""
E.V.I.E. - Deep Diagnostic Runner

Phase 15F

Purpose:
    Performs active but safe diagnostics for core local E.V.I.E. components.

Important:
    - no destructive actions
    - no integration writes
    - no credential disclosure
    - provider network probes remain optional
    - every check is isolated so one failure cannot crash diagnostics
"""

from __future__ import annotations

from dataclasses import (
    dataclass,
    field,
)

from pathlib import (
    Path,
)

from time import (
    perf_counter,
)

from typing import (
    Any,
    Callable,
)

from .health import (
    DEGRADED,
    HEALTHY,
    UNKNOWN,
    UNAVAILABLE,
    HealthResult,
    overall_health_status,
)


@dataclass
class DeepDiagnosticResult:
    results: list[
        HealthResult
    ] = field(
        default_factory=list
    )

    duration_seconds: float = 0.0

    overall: str = UNKNOWN

    metadata: dict[str, Any] = field(
        default_factory=dict
    )


def _run_check(
    component: str,
    function: Callable[
        [],
        HealthResult,
    ],
):
    started = (
        perf_counter()
    )

    try:

        result = (
            function()
        )

        if not isinstance(
            result,
            HealthResult,
        ):
            result = HealthResult(
                component=
                    component,

                status=
                    UNKNOWN,

                detail=
                    "Diagnostic returned invalid result.",
            )

    except Exception as error:

        result = HealthResult(
            component=
                component,

            status=
                DEGRADED,

            detail=
                str(
                    error
                ),
        )

    result.metadata = (
        dict(
            result.metadata
            or {}
        )
    )

    result.metadata[
        "diagnostic_seconds"
    ] = round(
        perf_counter()
        - started,
        4,
    )

    return result


# ---------------------------------------------------------------------------
# Deep Local Checks
# ---------------------------------------------------------------------------

def deep_check_memory_database():
    from assistant.memory.database import (
        get_connection,
    )

    with get_connection() as conn:

        integrity = (
            conn.execute(
                "PRAGMA quick_check"
            )
            .fetchone()
        )

        value = (
            integrity[
                0
            ]
            if integrity
            else ""
        )

    if str(
        value
    ).lower() != "ok":
        return HealthResult(
            "memory.database.deep",
            DEGRADED,
            f"SQLite quick_check returned: {value}",
        )

    return HealthResult(
        "memory.database.deep",
        HEALTHY,
        "SQLite quick_check passed.",
    )


def deep_check_embedding_model():
    from assistant.memory.embeddings import (
        create_embedding,
    )

    vector = (
        create_embedding(
            "E.V.I.E. diagnostic embedding"
        )
    )

    if (
        vector is None
        or len(
            vector
        )
        <= 0
    ):
        return HealthResult(
            "memory.embeddings.deep",
            DEGRADED,
            "Embedding inference returned no vector.",
        )

    return HealthResult(
        "memory.embeddings.deep",
        HEALTHY,
        "Embedding inference succeeded.",
        {
            "dimensions":
                int(
                    len(
                        vector
                    )
                ),
        },
    )


def deep_check_reranker():
    from assistant.memory.retriever import (
        get_reranker,
    )

    model = (
        get_reranker()
    )

    scores = (
        model.predict(
            [
                [
                    "E.V.I.E. health check",
                    "E.V.I.E. health check",
                ],
                [
                    "E.V.I.E. health check",
                    "completely unrelated sentence",
                ],
            ],
            show_progress_bar=
                False,
        )
    )

    if (
        scores is None
        or len(
            scores
        )
        != 2
    ):
        return HealthResult(
            "memory.reranker.deep",
            DEGRADED,
            "Reranker inference returned an invalid result.",
        )

    return HealthResult(
        "memory.reranker.deep",
        HEALTHY,
        "Reranker inference succeeded.",
    )


def deep_check_cuda():
    try:
        import torch

    except Exception as error:
        return HealthResult(
            "gpu.cuda.deep",
            UNAVAILABLE,
            f"PyTorch unavailable: {error}",
        )

    if not torch.cuda.is_available():
        return HealthResult(
            "gpu.cuda.deep",
            DEGRADED,
            "CUDA is unavailable.",
        )

    device = (
        torch.cuda.current_device()
    )

    tensor = (
        torch.tensor(
            [
                1.0,
                2.0,
            ],
            device=
                "cuda",
        )
    )

    result = (
        tensor.sum()
        .item()
    )

    if result != 3.0:
        return HealthResult(
            "gpu.cuda.deep",
            DEGRADED,
            "CUDA tensor computation produced an unexpected result.",
        )

    return HealthResult(
        "gpu.cuda.deep",
        HEALTHY,
        "CUDA allocation and computation succeeded.",
        {
            "device":
                torch.cuda.get_device_name(
                    device
                ),
        },
    )


def deep_check_runtime_write():
    root = (
        Path(__file__)
        .resolve()
        .parents[2]
    )

    directory = (
        root
        / "runtime"
        / "health"
    )

    directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    probe = (
        directory
        / ".deep_diagnostic_probe"
    )

    probe.write_text(
        "ok",
        encoding="utf-8",
    )

    content = (
        probe.read_text(
            encoding="utf-8"
        )
    )

    probe.unlink(
        missing_ok=True
    )

    if content != "ok":
        return HealthResult(
            "runtime.write.deep",
            DEGRADED,
            "Runtime read/write verification failed.",
        )

    return HealthResult(
        "runtime.write.deep",
        HEALTHY,
        "Runtime read/write verification succeeded.",
    )


def deep_check_tool_registry():
    from assistant.tools.registry import (
        list_tools,
        load_default_tools,
    )

    load_default_tools()

    tools = (
        list_tools()
    )

    names = {
        tool.name
        for tool
        in tools
    }

    if not names:
        return HealthResult(
            "tools.registry.deep",
            UNAVAILABLE,
            "Tool registry is empty.",
        )

    return HealthResult(
        "tools.registry.deep",
        HEALTHY,
        f"{len(names)} tools available.",
        {
            "tool_count":
                len(
                    names
                ),
        },
    )


def deep_check_integration_registry():
    from assistant.integrations.registry import (
        get_registry_summary,
        load_default_integrations,
    )

    load_default_integrations(
        include_mock=
            False,
    )

    summary = (
        get_registry_summary()
    )

    if not summary.get(
        "defaults_loaded"
    ):
        return HealthResult(
            "integrations.registry.deep",
            DEGRADED,
            "Integration defaults were not loaded.",
        )

    if int(
        summary.get(
            "capability_count",
            0,
        )
    ) <= 0:
        return HealthResult(
            "integrations.registry.deep",
            UNAVAILABLE,
            "Integration capability registry is empty.",
        )

    return HealthResult(
        "integrations.registry.deep",
        HEALTHY,
        (
            f"{summary.get('provider_count', 0)} providers / "
            f"{summary.get('capability_count', 0)} capabilities loaded."
        ),
    )


LOCAL_DEEP_CHECKS = (
    (
        "memory.database.deep",
        deep_check_memory_database,
    ),
    (
        "memory.embeddings.deep",
        deep_check_embedding_model,
    ),
    (
        "memory.reranker.deep",
        deep_check_reranker,
    ),
    (
        "gpu.cuda.deep",
        deep_check_cuda,
    ),
    (
        "runtime.write.deep",
        deep_check_runtime_write,
    ),
    (
        "tools.registry.deep",
        deep_check_tool_registry,
    ),
    (
        "integrations.registry.deep",
        deep_check_integration_registry,
    ),
)


def run_deep_diagnostic(
    *,
    include_expensive_models: bool = True,
):
    started = (
        perf_counter()
    )

    results = []


    for (
        component,
        function,
    ) in LOCAL_DEEP_CHECKS:

        if (
            not include_expensive_models
            and component
            in {
                "memory.embeddings.deep",
                "memory.reranker.deep",
            }
        ):
            continue

        results.append(
            _run_check(
                component,
                function,
            )
        )


    duration = (
        perf_counter()
        - started
    )


    return DeepDiagnosticResult(
        results=
            results,

        duration_seconds=
            round(
                duration,
                4,
            ),

        overall=
            overall_health_status(
                results
            ),

        metadata={
            "include_expensive_models":
                bool(
                    include_expensive_models
                ),
        },
    )


def format_deep_diagnostic_report(
    diagnostic: DeepDiagnosticResult | None = None,
):
    if diagnostic is None:

        diagnostic = (
            run_deep_diagnostic()
        )


    lines = [
        "E.V.I.E. DEEP DIAGNOSTIC",
        "",
    ]


    for result in diagnostic.results:

        duration = (
            result.metadata.get(
                "diagnostic_seconds"
            )
        )

        suffix = (
            f" ({duration:.3f}s)"
            if isinstance(
                duration,
                (
                    int,
                    float,
                ),
            )
            else ""
        )

        lines.append(
            (
                f"{result.component:<32} "
                f"{result.status}"
                f"{suffix}"
            )
        )

        if result.detail:

            lines.append(
                f"  {result.detail}"
            )


    lines.extend(
        [
            "",
            (
                "Diagnostic duration: "
                f"{diagnostic.duration_seconds:.3f}s"
            ),
            (
                "Overall: "
                f"{diagnostic.overall}"
            ),
        ]
    )


    return "\n".join(
        lines
    )
