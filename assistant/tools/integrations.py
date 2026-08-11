"""
E.V.I.E. - Integration Tool Gateway

Created: August 10, 2026
Author: Max Maehara

Purpose:
    Exposes Phase 9 integrations to E.V.I.E.'s existing Phase 6 tool
    system.

Architecture:
    Natural language
        ↓
    Phase 6 / Phase 7 planner
        ↓
    integration_execute
        ↓
    Phase 6 permission boundary
        ↓
    Phase 9 account router / aggregator
        ↓
    provider implementation

Important:
    This module does NOT replace Phase 9 permissions.

    Phase 6 determines whether the action may execute.
    Phase 9 independently validates account/provider availability.

    Write actions therefore inherit E.V.I.E.'s existing persistent
    approval/resume architecture.
"""

from __future__ import annotations

from assistant.integrations.aggregator import (
    aggregate_result_to_dict,
    execute_aggregate,
)

from .registry import (
    register_tool,
)


# ---------------------------------------------------------------------------
# Integration Execute
# ---------------------------------------------------------------------------

def integration_execute(
    capability: str,
    arguments: dict | None = None,
    routing_mode: str = "all_available",
    provider: str | None = None,
    account_id: str | None = None,
    approved: bool = False,
):
    """
    Executes one normalized Phase 9 integration capability.

    Parameters:
        capability:
            Normalized Phase 9 capability.

            Examples:
                email.search
                email.send
                calendar.read
                calendar.create
                contacts.search
                tasks.read
                tasks.create
                tasks.complete
                finance.read
                media.read
                media.control

        arguments:
            Provider-independent capability arguments.

        routing_mode:
            Account routing mode.

            Examples:
                all_available
                explicit_account

        provider:
            Optional provider restriction.

        account_id:
            Optional exact account restriction.

        approved:
            Supplied ONLY by E.V.I.E.'s Phase 6 executor after the
            existing permission boundary has been satisfied.

    Important:
        Natural-language planners should never set approved themselves.
    """

    capability = (
        str(
            capability
        )
        .strip()
        .lower()
    )


    if not capability:

        raise ValueError(
            "Integration capability cannot be empty."
        )


    if arguments is None:

        arguments = {}


    if not isinstance(
        arguments,
        dict,
    ):

        raise TypeError(
            "Integration arguments must be a dictionary."
        )


    result = execute_aggregate(
        capability=
            capability,

        arguments=
            arguments,

        routing_mode=
            routing_mode,

        provider=
            provider,

        account_id=
            account_id,

        approved=
            approved,
    )


    payload = (
        aggregate_result_to_dict(
            result
        )
    )


    # -----------------------------------------------------------------------
    # Still Waiting For Integration-Level Approval
    # -----------------------------------------------------------------------
    #
    # Normally Phase 6 catches this before this function executes.
    #
    # Keeping this check gives Phase 9 its own independent safety layer.
    # -----------------------------------------------------------------------

    if result.requires_approval:

        reason = (
            result.approval_reason
            or (
                f"{capability} requires "
                "approval before execution."
            )
        )


        raise RuntimeError(
            reason
        )


    # -----------------------------------------------------------------------
    # No Successful Provider Execution
    # -----------------------------------------------------------------------

    if not result.success:

        errors = []


        for evidence in result.evidence:

            if evidence.error:

                errors.append(
                    (
                        f"{evidence.provider}:"
                        f"{evidence.account_id}: "
                        f"{evidence.error}"
                    )
                )


        if errors:

            reason = (
                " | ".join(
                    errors
                )
            )

        elif (
            result.sources_attempted
            == 0
        ):

            reason = (
                "No connected account is available "
                f"for integration capability "
                f"{capability}."
            )

        else:

            reason = (
                "The integration action did not "
                "complete successfully."
            )


        raise RuntimeError(
            reason
        )


    # -----------------------------------------------------------------------
    # Success
    # -----------------------------------------------------------------------

    return payload


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

register_tool(
    name=
        "integration_execute",

    description=(
        "Execute a Phase 9 connected-service capability. "
        "Use this for connected accounts such as Google Gmail, "
        "Google Calendar, Google Tasks, Contacts, Spotify, GitHub, "
        "Notion, Discord, finance providers, weather providers, and "
        "future E.V.I.E. integrations. "
        "Examples include email.search, email.send, calendar.read, "
        "calendar.create, contacts.search, tasks.read, tasks.create, "
        "tasks.complete, finance.read, media.read, and media.control. "
        "Pass provider/account_id when the user selects a particular "
        "account. Write operations are dynamically risk-classified by "
        "the Phase 6 executor and must never be assumed approved."
    ),

    category=
        "integrations",

    # The executor dynamically escalates this using the requested
    # Phase 9 capability.
    risk=
        "low",

    function=
        integration_execute,
)


# ---------------------------------------------------------------------------
# Standalone Test
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    print(
        "E.V.I.E. Integration Tool Gateway"
    )

    print(
        "-------------------------------"
    )


    print(
        "Tool registered: integration_execute"
    )