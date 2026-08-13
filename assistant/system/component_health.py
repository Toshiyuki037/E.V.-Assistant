"""
E.V.I.E. - Component Health

Phase 15D — Component-Level Health

Purpose:
    Adds subsystem-specific, lightweight health checks while keeping V1
    implementations authoritative.

Important:
    These are passive checks by default. They should not perform expensive
    inference or external writes.
"""

from __future__ import annotations

import importlib.util

from pathlib import (
    Path,
)

from .health import (
    DEGRADED,
    HEALTHY,
    UNKNOWN,
    UNAVAILABLE,
    HealthResult,
)

from .failures import (
    get_component_state,
)


def _module_available(
    module_name: str,
):
    return (
        importlib.util.find_spec(
            module_name
        )
        is not None
    )


def _with_failure_history(
    result: HealthResult,
):
    """
    Merge persisted recent failure state with a passive capability check.

    A component that is structurally present but has unresolved consecutive
    runtime failures should report DEGRADED rather than HEALTHY.
    """

    state = (
        get_component_state(
            result.component
        )
    )

    result.metadata = (
        dict(
            result.metadata
            or {}
        )
    )

    result.metadata[
        "failure_count"
    ] = state.failure_count

    result.metadata[
        "consecutive_failures"
    ] = state.consecutive_failures

    result.metadata[
        "last_failure_at"
    ] = state.last_failure_at

    result.metadata[
        "last_success_at"
    ] = state.last_success_at

    if (
        state.consecutive_failures
        > 0
        and state.last_error
    ):
        result.status = (
            DEGRADED
        )

        result.detail = (
            state.last_error
        )

        result.metadata[
            "recent_failure"
        ] = True

    return result


def check_stt():
    if not _module_available(
        "assistant.listen"
    ):
        return HealthResult(
            "voice.stt",
            UNAVAILABLE,
            "Speech-recognition module is unavailable.",
        )

    return _with_failure_history(
        HealthResult(
            "voice.stt",
            HEALTHY,
            "Speech-recognition module is available.",
        )
    )


def check_tts():
    if not _module_available(
        "assistant.speak"
    ):
        return HealthResult(
            "voice.tts",
            UNAVAILABLE,
            "Speech-synthesis module is unavailable.",
        )

    return _with_failure_history(
        HealthResult(
            "voice.tts",
            HEALTHY,
            "Speech-synthesis module is available.",
        )
    )


def check_wake_system():
    if not _module_available(
        "assistant.voice.session"
    ):
        return HealthResult(
            "voice.wake",
            UNAVAILABLE,
            "Voice-session module is unavailable.",
        )

    return _with_failure_history(
        HealthResult(
            "voice.wake",
            HEALTHY,
            "Wake/session subsystem is installed.",
        )
    )


def check_voice_identity():
    if not _module_available(
        "assistant.voice.authentication"
    ):
        return HealthResult(
            "voice.identity",
            UNAVAILABLE,
            "Voice-authentication module is unavailable.",
        )

    return _with_failure_history(
        HealthResult(
            "voice.identity",
            HEALTHY,
            "Voice-authentication subsystem is installed.",
        )
    )


def check_agent_runtime():
    if not _module_available(
        "assistant.agent.integration"
    ):
        return HealthResult(
            "agent.runtime",
            UNAVAILABLE,
            "Agent integration module is unavailable.",
        )

    return _with_failure_history(
        HealthResult(
            "agent.runtime",
            HEALTHY,
            "Agent runtime integration is available.",
        )
    )


def check_workflow_runtime():
    if not _module_available(
        "assistant.workflows.integration"
    ):
        return HealthResult(
            "workflows.runtime",
            UNAVAILABLE,
            "Workflow integration module is unavailable.",
        )

    return _with_failure_history(
        HealthResult(
            "workflows.runtime",
            HEALTHY,
            "Workflow runtime integration is available.",
        )
    )


def check_computer_control():
    if not _module_available(
        "assistant.computer.integration"
    ):
        return HealthResult(
            "computer.control",
            UNAVAILABLE,
            "Computer-control integration is unavailable.",
        )

    return _with_failure_history(
        HealthResult(
            "computer.control",
            HEALTHY,
            "Computer-control integration is available.",
        )
    )


def check_browser():
    if not _module_available(
        "assistant.tools.browser"
    ):
        return HealthResult(
            "browser",
            UNAVAILABLE,
            "Browser tool module is unavailable.",
        )

    return _with_failure_history(
        HealthResult(
            "browser",
            HEALTHY,
            "Browser tooling is installed.",
        )
    )


def check_vision():
    candidates = (
        "assistant.vision",
        "assistant.perception",
    )

    if not any(
        _module_available(
            name
        )
        for name
        in candidates
    ):
        return HealthResult(
            "vision",
            UNKNOWN,
            "No standard vision package entry point was detected.",
        )

    return _with_failure_history(
        HealthResult(
            "vision",
            HEALTHY,
            "Vision/perception package is available.",
        )
    )


def check_cuda():
    try:
        import torch

    except Exception as error:
        return HealthResult(
            "gpu.cuda",
            UNAVAILABLE,
            f"PyTorch unavailable: {error}",
        )

    available = bool(
        torch.cuda.is_available()
    )

    if not available:
        return _with_failure_history(
            HealthResult(
                "gpu.cuda",
                DEGRADED,
                "CUDA is not currently available.",
            )
        )

    device_name = (
        torch.cuda.get_device_name(
            0
        )
    )

    return _with_failure_history(
        HealthResult(
            "gpu.cuda",
            HEALTHY,
            "CUDA is available.",
            {
                "device":
                    device_name,

                "device_count":
                    int(
                        torch.cuda.device_count()
                    ),
            },
        )
    )


def check_runtime_directories():
    root = (
        Path(__file__)
        .resolve()
        .parents[2]
    )

    required = [
        root
        / "runtime",

        root
        / "memory",
    ]

    missing = [
        str(
            path
        )

        for path
        in required

        if not path.exists()
    ]

    if missing:
        return HealthResult(
            "runtime.directories",
            DEGRADED,
            "One or more runtime directories are missing.",
            {
                "missing":
                    missing,
            },
        )

    return HealthResult(
        "runtime.directories",
        HEALTHY,
        "Core runtime directories exist.",
    )


COMPONENT_CHECKS = (
    check_stt,
    check_tts,
    check_wake_system,
    check_voice_identity,
    check_agent_runtime,
    check_workflow_runtime,
    check_computer_control,
    check_browser,
    check_vision,
    check_cuda,
    check_runtime_directories,
)


def run_component_health_checks():
    results = []

    for check in COMPONENT_CHECKS:

        try:
            result = check()

        except Exception as error:
            result = HealthResult(
                component=
                    getattr(
                        check,
                        "__name__",
                        "unknown",
                    ),

                status=
                    DEGRADED,

                detail=
                    str(
                        error
                    ),
            )

        results.append(
            result
        )

    return results
