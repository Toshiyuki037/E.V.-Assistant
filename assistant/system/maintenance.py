"""
E.V.I.E. - Maintenance & Recovery

Phase 15H

Purpose:
    Provides safe, bounded operational maintenance actions.

Important:
    This module does NOT edit E.V.I.E. source code.
    Source-code repair belongs to the later self-engineering bridge.

Maintenance principles:
    - prefer deterministic local maintenance
    - never expose credentials
    - never perform destructive source changes
    - isolate each action
    - re-check health after maintenance when appropriate
"""

from __future__ import annotations

from dataclasses import (
    asdict,
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
    HealthResult,
    overall_health_status,
    run_quick_health_check,
)

from .failures import (
    clear_all_component_states,
)


PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[2]
)


@dataclass
class MaintenanceResult:
    action: str

    success: bool

    detail: str = ""

    changed: bool = False

    duration_seconds: float = 0.0

    before_health: str = ""

    after_health: str = ""

    metadata: dict[str, Any] = field(
        default_factory=dict
    )


def maintenance_result_to_dict(
    result: MaintenanceResult,
):
    return asdict(
        result
    )


def _health_state():
    results = (
        run_quick_health_check()
    )

    return (
        overall_health_status(
            results
        )
    )


def _run_action(
    action: str,
    function: Callable[[], tuple[bool, str, bool, dict]],
):
    started = (
        perf_counter()
    )

    before = ""

    after = ""

    try:
        before = (
            _health_state()
        )

    except Exception:
        before = ""


    try:

        success, detail, changed, metadata = (
            function()
        )

    except Exception as error:

        return MaintenanceResult(
            action=
                action,

            success=
                False,

            detail=
                str(
                    error
                ),

            changed=
                False,

            duration_seconds=
                round(
                    perf_counter()
                    - started,
                    4,
                ),

            before_health=
                before,

            after_health=
                before,
        )


    try:
        after = (
            _health_state()
        )

    except Exception:
        after = ""


    return MaintenanceResult(
        action=
            action,

        success=
            bool(
                success
            ),

        detail=
            str(
                detail
                or ""
            ),

        changed=
            bool(
                changed
            ),

        duration_seconds=
            round(
                perf_counter()
                - started,
                4,
            ),

        before_health=
            before,

        after_health=
            after,

        metadata=
            dict(
                metadata
                or {}
            ),
    )


# ---------------------------------------------------------------------------
# Runtime State Cleanup
# ---------------------------------------------------------------------------

def _clear_stale_agent_state():
    candidates = [
        PROJECT_ROOT
        / "runtime"
        / "agent"
        / "current_task.json",

        PROJECT_ROOT
        / "runtime"
        / "agent"
        / "_task.json",
    ]

    removed = []

    for path in candidates:

        if path.exists():

            try:
                path.unlink()

                removed.append(
                    str(
                        path
                    )
                )

            except OSError:
                pass

    return (
        True,
        (
            "Cleared stale agent state."
            if removed
            else "No stale agent state was present."
        ),
        bool(
            removed
        ),
        {
            "removed":
                removed,
        },
    )


def _clear_pending_integration_selection():
    try:
        from assistant.integrations.selection import (
            clear_pending_integration_selection,
        )

    except Exception:

        return (
            False,
            "Integration selection module is unavailable.",
            False,
            {},
        )

    pending = (
        clear_pending_integration_selection()
    )

    return (
        True,
        (
            "Cleared pending integration selection."
            if pending is not None
            else "No pending integration selection was present."
        ),
        pending is not None,
        {},
    )


def _clear_failure_history():
    clear_all_component_states()

    return (
        True,
        "Cleared persisted component failure history.",
        True,
        {},
    )


# ---------------------------------------------------------------------------
# Registry Reload
# ---------------------------------------------------------------------------

def _reload_tool_registry():
    from assistant.tools.registry import (
        list_tools,
        load_default_tools,
    )

    load_default_tools()

    tools = (
        list_tools()
    )

    return (
        bool(
            tools
        ),
        f"{len(tools)} tools registered.",
        False,
        {
            "tool_count":
                len(
                    tools
                ),
        },
    )


def _reload_integration_registry():
    from assistant.integrations.registry import (
        clear_integration_registry,
        get_registry_summary,
        load_default_integrations,
    )

    clear_integration_registry()

    load_default_integrations(
        include_mock=
            False,
    )

    summary = (
        get_registry_summary()
    )

    success = (
        int(
            summary.get(
                "capability_count",
                0,
            )
        )
        > 0
    )

    return (
        success,
        (
            f"{summary.get('provider_count', 0)} providers / "
            f"{summary.get('capability_count', 0)} capabilities loaded."
        ),
        True,
        summary,
    )


# ---------------------------------------------------------------------------
# Memory Maintenance
# ---------------------------------------------------------------------------

def _rebuild_missing_embeddings():
    from assistant.memory.embeddings import (
        sync_memory_embeddings,
    )

    generated = (
        sync_memory_embeddings()
    )

    return (
        True,
        f"Generated {generated} missing memory embeddings.",
        generated > 0,
        {
            "generated":
                generated,
        },
    )


def _run_memory_consolidation():
    from assistant.memory.consolidation import (
        consolidate_memories,
    )

    actions = (
        consolidate_memories()
    )

    return (
        True,
        f"Memory consolidation produced {len(actions)} actions.",
        bool(
            actions
        ),
        {
            "actions":
                actions,
        },
    )


# ---------------------------------------------------------------------------
# Runtime Directories
# ---------------------------------------------------------------------------

def _ensure_runtime_directories():
    directories = [
        PROJECT_ROOT
        / "runtime",

        PROJECT_ROOT
        / "runtime"
        / "telemetry",

        PROJECT_ROOT
        / "runtime"
        / "health",

        PROJECT_ROOT
        / "runtime"
        / "integrations",
    ]

    created = []

    for directory in directories:

        if not directory.exists():

            directory.mkdir(
                parents=True,
                exist_ok=True,
            )

            created.append(
                str(
                    directory
                )
            )

    return (
        True,
        (
            "Runtime directories verified."
            if not created
            else (
                "Created missing runtime directories."
            )
        ),
        bool(
            created
        ),
        {
            "created":
                created,
        },
    )


# ---------------------------------------------------------------------------
# Telemetry Maintenance
# ---------------------------------------------------------------------------

def _prune_telemetry(
    *,
    keep_latest: int = 500,
):
    directory = (
        PROJECT_ROOT
        / "runtime"
        / "telemetry"
    )

    if not directory.exists():

        return (
            True,
            "Telemetry directory does not exist; nothing to prune.",
            False,
            {
                "removed":
                    0,
            },
        )

    files = sorted(
        directory.glob(
            "*.json"
        ),
        key=lambda path:
            path.stat().st_mtime,
        reverse=True,
    )

    to_remove = (
        files[
            max(
                0,
                int(
                    keep_latest
                ),
            ):
        ]
    )

    removed = 0

    for path in to_remove:

        try:
            path.unlink()

            removed += 1

        except OSError:
            pass

    return (
        True,
        f"Pruned {removed} telemetry files.",
        removed > 0,
        {
            "removed":
                removed,

            "kept":
                min(
                    len(
                        files
                    ),
                    max(
                        0,
                        int(
                            keep_latest
                        ),
                    ),
                ),
        },
    )


# ---------------------------------------------------------------------------
# Public Actions
# ---------------------------------------------------------------------------

def clear_stale_agent_state():
    return _run_action(
        "clear_stale_agent_state",
        _clear_stale_agent_state,
    )


def clear_pending_integration_selection():
    return _run_action(
        "clear_pending_integration_selection",
        _clear_pending_integration_selection,
    )


def clear_failure_history():
    return _run_action(
        "clear_failure_history",
        _clear_failure_history,
    )


def reload_tool_registry():
    return _run_action(
        "reload_tool_registry",
        _reload_tool_registry,
    )


def reload_integration_registry():
    return _run_action(
        "reload_integration_registry",
        _reload_integration_registry,
    )


def rebuild_missing_embeddings():
    return _run_action(
        "rebuild_missing_embeddings",
        _rebuild_missing_embeddings,
    )


def run_memory_consolidation():
    return _run_action(
        "run_memory_consolidation",
        _run_memory_consolidation,
    )


def ensure_runtime_directories():
    return _run_action(
        "ensure_runtime_directories",
        _ensure_runtime_directories,
    )


def prune_telemetry(
    *,
    keep_latest: int = 500,
):
    return _run_action(
        "prune_telemetry",
        lambda:
            _prune_telemetry(
                keep_latest=
                    keep_latest,
            ),
    )


MAINTENANCE_ACTIONS = {
    "clear_stale_agent_state":
        clear_stale_agent_state,

    "clear_pending_integration_selection":
        clear_pending_integration_selection,

    "clear_failure_history":
        clear_failure_history,

    "reload_tool_registry":
        reload_tool_registry,

    "reload_integration_registry":
        reload_integration_registry,

    "rebuild_missing_embeddings":
        rebuild_missing_embeddings,

    "run_memory_consolidation":
        run_memory_consolidation,

    "ensure_runtime_directories":
        ensure_runtime_directories,

    "prune_telemetry":
        prune_telemetry,
}


def list_maintenance_actions():
    return sorted(
        MAINTENANCE_ACTIONS
    )


def run_maintenance_action(
    action: str,
    **kwargs,
):
    normalized = (
        str(
            action
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

    function = (
        MAINTENANCE_ACTIONS.get(
            normalized
        )
    )

    if function is None:

        return MaintenanceResult(
            action=
                normalized
                or "unknown",

            success=
                False,

            detail=
                "Unknown maintenance action.",
        )

    return function(
        **kwargs
    )
