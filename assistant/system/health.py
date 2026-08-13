"""
E.V.I.E. Phase 15B — Runtime Health Engine.
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

from typing import (
    Any,
    Callable,
)


HEALTHY = "HEALTHY"
DEGRADED = "DEGRADED"
UNAVAILABLE = "UNAVAILABLE"
UNKNOWN = "UNKNOWN"


# ---------------------------------------------------------------------------
# Health Result
# ---------------------------------------------------------------------------

@dataclass
class HealthResult:
    component: str

    status: str

    detail: str = ""

    metadata: dict[str, Any] = field(
        default_factory=dict
    )


def health_result_to_dict(
    result: HealthResult,
):
    return asdict(
        result
    )


# ---------------------------------------------------------------------------
# Safe Check Wrapper
# ---------------------------------------------------------------------------

def _safe_check(
    component: str,
    check_fn: Callable[
        [],
        HealthResult,
    ],
):
    try:

        result = (
            check_fn()
        )

        if isinstance(
            result,
            HealthResult,
        ):
            return result

        return HealthResult(
            component=
                component,

            status=
                UNKNOWN,

            detail=
                "Health check returned an invalid result.",
        )

    except Exception as error:

        return HealthResult(
            component=
                component,

            status=
                DEGRADED,

            detail=
                str(
                    error
                ),
        )


# ---------------------------------------------------------------------------
# Memory Database
# ---------------------------------------------------------------------------

def check_memory_database():

    from assistant.memory.database import (
        DB_PATH,
        get_connection,
    )


    if not Path(
        DB_PATH
    ).exists():

        return HealthResult(
            component=
                "memory.database",

            status=
                UNAVAILABLE,

            detail=
                "Memory database file does not exist.",
        )


    with get_connection() as conn:

        conn.execute(
            "SELECT 1"
        ).fetchone()


        tables = {
            row[
                "name"
            ]

            for row
            in conn.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type='table'
                """
            ).fetchall()
        }


    missing = (
        {
            "conversations",
            "memories",
        }
        - tables
    )


    if missing:

        return HealthResult(
            component=
                "memory.database",

            status=
                DEGRADED,

            detail=(
                "Missing required tables: "
                + ", ".join(
                    sorted(
                        missing
                    )
                )
            ),
        )


    return HealthResult(
        component=
            "memory.database",

        status=
            HEALTHY,

        detail=
            "SQLite memory database is readable.",
    )


# ---------------------------------------------------------------------------
# Memory Embeddings
# ---------------------------------------------------------------------------

def check_memory_embeddings():

    from assistant.memory.embeddings import (
        MODEL_NAME,
    )


    return HealthResult(
        component=
            "memory.embeddings",

        status=
            HEALTHY,

        detail=
            "Embedding model is configured.",

        metadata={
            "model":
                MODEL_NAME,
        },
    )


# ---------------------------------------------------------------------------
# Memory Reranker
# ---------------------------------------------------------------------------

def check_memory_reranker():

    from assistant.memory.retriever import (
        RERANKER_MODEL,
    )


    return HealthResult(
        component=
            "memory.reranker",

        status=
            HEALTHY,

        detail=
            "Memory reranker is configured.",

        metadata={
            "model":
                RERANKER_MODEL,
        },
    )


# ---------------------------------------------------------------------------
# Tool Registry
# ---------------------------------------------------------------------------

def check_tool_registry():

    from assistant.tools.registry import (
        list_tools,
        load_default_tools,
    )


    load_default_tools()


    tools = (
        list_tools()
    )


    if not tools:

        return HealthResult(
            component=
                "tools.registry",

            status=
                UNAVAILABLE,

            detail=
                "No tools are registered.",
        )


    return HealthResult(
        component=
            "tools.registry",

        status=
            HEALTHY,

        detail=
            f"{len(tools)} tools registered.",

        metadata={
            "tool_count":
                len(
                    tools
                ),
        },
    )


# ---------------------------------------------------------------------------
# Integration Registry
# ---------------------------------------------------------------------------

def check_integration_registry():

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


    count = int(
        summary.get(
            "capability_count",
            0,
        )
    )


    if count <= 0:

        return HealthResult(
            component=
                "integrations.registry",

            status=
                UNAVAILABLE,

            detail=
                "No integration capabilities registered.",

            metadata=
                summary,
        )


    return HealthResult(
        component=
            "integrations.registry",

        status=
            HEALTHY,

        detail=(
            f"{summary.get('provider_count', 0)} providers "
            f"and {count} capabilities registered."
        ),

        metadata=
            summary,
    )


# ---------------------------------------------------------------------------
# Integration Accounts
# ---------------------------------------------------------------------------

def check_integration_accounts():

    from assistant.integrations.connections import (
        load_accounts,
    )


    accounts = (
        load_accounts()
    )


    if not accounts:

        return HealthResult(
            component=
                "integrations.accounts",

            status=
                UNKNOWN,

            detail=
                "No integration accounts are registered.",
        )


    healthy = []

    disconnected = []

    unauthenticated = []


    for account in accounts:

        label = (
            f"{account.provider}:"
            f"{account.account_id}"
        )


        if not account.connected:

            disconnected.append(
                label
            )


        elif not account.authenticated:

            unauthenticated.append(
                label
            )


        else:

            healthy.append(
                label
            )


    if (
        disconnected
        or unauthenticated
    ):

        return HealthResult(
            component=
                "integrations.accounts",

            status=
                DEGRADED,

            detail=
                "One or more integration accounts are not fully available.",

            metadata={
                "healthy":
                    healthy,

                "disconnected":
                    disconnected,

                "unauthenticated":
                    unauthenticated,
            },
        )


    return HealthResult(
        component=
            "integrations.accounts",

        status=
            HEALTHY,

        detail=(
            f"{len(healthy)} integration accounts "
            "connected and authenticated."
        ),

        metadata={
            "healthy":
                healthy,
        },
    )


# ---------------------------------------------------------------------------
# Integration Capabilities
# ---------------------------------------------------------------------------

def check_integration_capabilities():

    from assistant.integrations.capabilities import (
        list_account_capabilities,
    )

    from assistant.integrations.connections import (
        load_accounts,
    )

    from assistant.integrations.registry import (
        load_default_integrations,
    )


    # -----------------------------------------------------------------------
    # Provider capability definitions must be loaded in this Python process.
    # -----------------------------------------------------------------------

    load_default_integrations(
        include_mock=
            False,
    )


    accounts = (
        load_accounts()
    )


    if not accounts:

        return HealthResult(
            component=
                "integrations.capabilities",

            status=
                UNKNOWN,

            detail=
                "No accounts available for capability health inspection.",
        )


    connected_accounts = [
        account

        for account
        in accounts

        if (
            account.connected
            and account.authenticated
        )
    ]


    if not connected_accounts:

        return HealthResult(
            component=
                "integrations.capabilities",

            status=
                UNKNOWN,

            detail=
                "No connected and authenticated accounts are available.",
        )


    available = []

    limited = []

    failures = []

    inspected_accounts = 0


    for account in connected_accounts:

        try:

            states = (
                list_account_capabilities(
                    account.provider,
                    account.account_id,
                )
            )


        except Exception as error:

            failures.append(
                {
                    "account":
                        (
                            f"{account.provider}:"
                            f"{account.account_id}"
                        ),

                    "provider":
                        account.provider,

                    "capability":
                        "*",

                    "reason":
                        str(
                            error
                        ),

                    "source":
                        "health_check_exception",
                }
            )

            continue


        inspected_accounts += 1


        for state in states:

            item = {
                "account":
                    (
                        f"{state.provider}:"
                        f"{state.account_id}"
                    ),

                "provider":
                    state.provider,

                "capability":
                    state.capability,

                "reason":
                    state.reason,

                "source":
                    state.source,
            }


            if state.available:

                available.append(
                    item
                )

                continue


            reason_lower = (
                str(
                    state.reason
                    or ""
                )
                .strip()
                .lower()
            )


            # ---------------------------------------------------------------
            # Expected account-specific limitations
            #
            # These mean an individual account does not provide a service.
            # They do NOT mean E.V.I.E. itself is unhealthy.
            #
            # Current examples:
            # - OSU Google account has no Gmail service
            # - OSU account is not provisioned for Google Calendar
            # ---------------------------------------------------------------

            expected_limitation = (
                (
                    "not enabled for this google account"
                    in reason_lower
                )

                or (
                    "must be signed up for google calendar"
                    in reason_lower
                )

                or (
                    "notacalendaruser"
                    in reason_lower
                )
            )


            if expected_limitation:

                limited.append(
                    item
                )


            else:

                failures.append(
                    item
                )


    # -----------------------------------------------------------------------
    # Fail-safe
    #
    # Connected accounts exist but capability discovery returned nothing.
    # That is a health problem.
    # -----------------------------------------------------------------------

    if (
        connected_accounts
        and not available
        and not limited
        and not failures
    ):

        return HealthResult(
            component=
                "integrations.capabilities",

            status=
                DEGRADED,

            detail=(
                "Connected integration accounts exist, "
                "but no capability states were discovered."
            ),

            metadata={
                "connected_account_count":
                    len(
                        connected_accounts
                    ),

                "inspected_account_count":
                    inspected_accounts,

                "available_count":
                    0,

                "limited_count":
                    0,

                "failure_count":
                    0,
            },
        )


    # -----------------------------------------------------------------------
    # Unexpected runtime/capability failures
    # -----------------------------------------------------------------------

    if failures:

        return HealthResult(
            component=
                "integrations.capabilities",

            status=
                DEGRADED,

            detail=(
                f"{len(failures)} integration capability states "
                "are failing unexpectedly."
            ),

            metadata={
                "connected_account_count":
                    len(
                        connected_accounts
                    ),

                "inspected_account_count":
                    inspected_accounts,

                "available_count":
                    len(
                        available
                    ),

                "limited_count":
                    len(
                        limited
                    ),

                "failure_count":
                    len(
                        failures
                    ),

                "limited":
                    limited,

                "failures":
                    failures,
            },
        )


    # -----------------------------------------------------------------------
    # Healthy system
    #
    # Account-specific limitations remain visible in metadata but do not
    # degrade overall E.V.I.E. health.
    # -----------------------------------------------------------------------

    detail = (
        f"{len(available)} account capability states are available "
        f"across {len(connected_accounts)} connected accounts."
    )


    if limited:

        detail += (
            f" {len(limited)} account-specific capability limitations "
            "were detected and are expected."
        )


    return HealthResult(
        component=
            "integrations.capabilities",

        status=
            HEALTHY,

        detail=
            detail,

        metadata={
            "connected_account_count":
                len(
                    connected_accounts
                ),

            "inspected_account_count":
                inspected_accounts,

            "available_count":
                len(
                    available
                ),

            "limited_count":
                len(
                    limited
                ),

            "failure_count":
                0,

            "limited":
                limited,
        },
    )


# ---------------------------------------------------------------------------
# Telemetry
# ---------------------------------------------------------------------------

def check_telemetry():

    directory = (
        Path("runtime")
        / "telemetry"
    )


    try:

        directory.mkdir(
            parents=True,
            exist_ok=True,
        )


        probe = (
            directory
            / ".healthcheck"
        )


        probe.write_text(
            "ok",
            encoding="utf-8",
        )


        probe.unlink(
            missing_ok=True
        )


    except Exception as error:

        return HealthResult(
            component=
                "telemetry",

            status=
                DEGRADED,

            detail=
                str(
                    error
                ),
        )


    return HealthResult(
        component=
            "telemetry",

        status=
            HEALTHY,

        detail=
            "Telemetry directory is writable.",
    )


# ---------------------------------------------------------------------------
# Quick Health Checks
# ---------------------------------------------------------------------------

QUICK_CHECKS = (
    (
        "memory.database",
        check_memory_database,
    ),

    (
        "memory.embeddings",
        check_memory_embeddings,
    ),

    (
        "memory.reranker",
        check_memory_reranker,
    ),

    (
        "tools.registry",
        check_tool_registry,
    ),

    (
        "integrations.registry",
        check_integration_registry,
    ),

    (
        "integrations.accounts",
        check_integration_accounts,
    ),

    (
        "integrations.capabilities",
        check_integration_capabilities,
    ),

    (
        "telemetry",
        check_telemetry,
    ),
)


def run_quick_health_check():

    return [
        _safe_check(
            name,
            function,
        )

        for (
            name,
            function,
        )
        in QUICK_CHECKS
    ]


# ---------------------------------------------------------------------------
# Overall Health
# ---------------------------------------------------------------------------

def overall_health_status(
    results,
):

    statuses = {
        result.status

        for result
        in results
    }


    if UNAVAILABLE in statuses:

        return UNAVAILABLE


    if DEGRADED in statuses:

        return DEGRADED


    if UNKNOWN in statuses:

        return UNKNOWN


    return HEALTHY


# ---------------------------------------------------------------------------
# Structured Health Summary
# ---------------------------------------------------------------------------

def health_summary(
    results=None,
):

    if results is None:

        results = (
            run_quick_health_check()
        )


    return {
        "overall":
            overall_health_status(
                results
            ),

        "components": [
            health_result_to_dict(
                result
            )

            for result
            in results
        ],
    }