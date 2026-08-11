"""
E.V.I.E. - Integration Aggregator

Created: August 10, 2026
Last Edited: August 10, 2026
Author: Max Maehara

Purpose:
    Executes normalized Phase 9 capabilities across routed accounts,
    preserves provenance, and enforces integration write approvals.

Safety:
    - low-risk operations may execute immediately
    - medium/high-risk operations require approved=True
    - write operations may not fan out across multiple accounts
      accidentally
"""

from __future__ import annotations

from dataclasses import (
    asdict,
    dataclass,
    field,
)

from typing import Any

from .account_router import (
    RoutedAccount,
    route_accounts,
)

from .permissions import (
    get_permission,
)

from .registry import (
    get_integration_capability,
    load_default_integrations,
)


# ---------------------------------------------------------------------------
# Evidence
# ---------------------------------------------------------------------------

@dataclass
class IntegrationEvidence:
    provider: str

    account_id: str

    capability: str

    success: bool

    data: Any = None

    error: str = ""

    executed: bool = False

    requires_approval: bool = False

    risk: str = "low"


# ---------------------------------------------------------------------------
# Aggregate Result
# ---------------------------------------------------------------------------

@dataclass
class AggregatedIntegrationResult:
    success: bool

    capability: str

    routing_mode: str

    sources_attempted: int

    sources_succeeded: int

    evidence: list[
        IntegrationEvidence
    ] = field(
        default_factory=list
    )

    requires_approval: bool = False

    approval_reason: str = ""


# ---------------------------------------------------------------------------
# Evidence Serialization
# ---------------------------------------------------------------------------

def evidence_to_dict(
    evidence: IntegrationEvidence,
):
    return asdict(
        evidence
    )


# ---------------------------------------------------------------------------
# Result Serialization
# ---------------------------------------------------------------------------

def aggregate_result_to_dict(
    result: AggregatedIntegrationResult,
):
    return asdict(
        result
    )


# ---------------------------------------------------------------------------
# Capability Risk
# ---------------------------------------------------------------------------

def get_capability_risk(
    capability: str,
    registered=None,
):
    """
    Permission policy is authoritative.

    Registry risk is used as a compatibility fallback.
    """

    permission = get_permission(
        capability
    )


    if permission is not None:

        return (
            permission.risk
            .strip()
            .lower()
        )


    if registered is not None:

        risk = getattr(
            registered,
            "risk",
            "low",
        )


        return (
            str(
                risk
            )
            .strip()
            .lower()
        )


    return "low"


# ---------------------------------------------------------------------------
# Approval Requirement
# ---------------------------------------------------------------------------

def capability_requires_approval(
    capability: str,
    registered=None,
):
    risk = get_capability_risk(
        capability,
        registered,
    )


    return (
        risk
        in {
            "medium",
            "high",
        }
    )


# ---------------------------------------------------------------------------
# Execute One Routed Account
# ---------------------------------------------------------------------------

def execute_routed_account(
    routed: RoutedAccount,
    arguments: dict,
    approved: bool = False,
):
    registered = (
        get_integration_capability(
            routed.provider,
            routed.capability,
        )
    )


    if registered is None:

        return IntegrationEvidence(
            provider=
                routed.provider,

            account_id=
                routed.account_id,

            capability=
                routed.capability,

            success=
                False,

            error=
                "Capability is not registered.",

            executed=
                False,
        )


    risk = get_capability_risk(
        routed.capability,
        registered,
    )


    requires_approval = (
        capability_requires_approval(
            routed.capability,
            registered,
        )
    )


    # -----------------------------------------------------------------------
    # Approval Boundary
    # -----------------------------------------------------------------------

    if (
        requires_approval
        and not approved
    ):

        return IntegrationEvidence(
            provider=
                routed.provider,

            account_id=
                routed.account_id,

            capability=
                routed.capability,

            success=
                False,

            error=(
                f"{routed.capability} requires user approval "
                f"before execution."
            ),

            executed=
                False,

            requires_approval=
                True,

            risk=
                risk,
        )


    call_arguments = dict(
        arguments
    )


    # -----------------------------------------------------------------------
    # Account Scope
    # -----------------------------------------------------------------------

    call_arguments[
        "account_id"
    ] = routed.account_id


    try:

        result = (
            registered.function(
                **call_arguments
            )
        )


        return IntegrationEvidence(
            provider=
                routed.provider,

            account_id=
                routed.account_id,

            capability=
                routed.capability,

            success=
                True,

            data=
                result,

            executed=
                True,

            requires_approval=
                False,

            risk=
                risk,
        )


    except Exception as error:

        return IntegrationEvidence(
            provider=
                routed.provider,

            account_id=
                routed.account_id,

            capability=
                routed.capability,

            success=
                False,

            error=
                str(
                    error
                ),

            executed=
                True,

            requires_approval=
                False,

            risk=
                risk,
        )


# ---------------------------------------------------------------------------
# Aggregate Execute
# ---------------------------------------------------------------------------

def execute_aggregate(
    capability: str,
    arguments: dict | None = None,
    routing_mode: str = "all_available",
    provider: str | None = None,
    account_id: str | None = None,
    approved: bool = False,
):
    """
    Executes one normalized integration capability.

    approved=False is always the safe default.

    Medium/high-risk actions return requires_approval=True instead of
    executing.

    Write actions are also prevented from automatically fanning out to
    several accounts.
    """

    load_default_integrations(
        include_mock=False
    )


    if arguments is None:

        arguments = {}

    # -----------------------------------------------------------------------
    # Explicit Account Normalization
    # -----------------------------------------------------------------------
    #
    # account_id always wins over a stale/default routing_mode.
    #
    # This prevents an explicitly selected account from accidentally being
    # treated as an all-account write.
    # -----------------------------------------------------------------------

    if account_id:

        routing_mode = (
            "explicit_account"
        )


        if provider:

            provider = (
                str(
                    provider
                )
                .strip()
                .lower()
            )


        account_id = (
            str(
                account_id
            )
            .strip()
        )

    registered_for_risk = None


    # -----------------------------------------------------------------------
    # Route
    # -----------------------------------------------------------------------

    routed_accounts = (
        route_accounts(
            capability=
                capability,

            mode=
                routing_mode,

            provider=
                provider,

            account_id=
                account_id,
        )
    )


    if routed_accounts:

        registered_for_risk = (
            get_integration_capability(
                routed_accounts[
                    0
                ].provider,

                capability,
            )
        )


    risk = get_capability_risk(
        capability,
        registered_for_risk,
    )


    requires_approval = (
        capability_requires_approval(
            capability,
            registered_for_risk,
        )
    )


    # -----------------------------------------------------------------------
    # Prevent Write Fan-Out
    # -----------------------------------------------------------------------

    if (
        requires_approval
        and len(
            routed_accounts
        )
        > 1
        and routing_mode
        == "all_available"
    ):

        return AggregatedIntegrationResult(
            success=
                False,

            capability=
                capability,

            routing_mode=
                routing_mode,

            sources_attempted=
                0,

            sources_succeeded=
                0,

            evidence=
                [],

            requires_approval=
                True,

            approval_reason=(
                "A write-capable integration action matched multiple "
                "accounts. Select one account before approval."
            ),
        )


    # -----------------------------------------------------------------------
    # Execute / Stage
    # -----------------------------------------------------------------------

    evidence = []


    for routed in routed_accounts:

        evidence.append(
            execute_routed_account(
                routed=
                    routed,

                arguments=
                    arguments,

                approved=
                    approved,
            )
        )


    succeeded = [
        item

        for item
        in evidence

        if item.success
    ]


    approval_items = [
        item

        for item
        in evidence

        if item.requires_approval
    ]


    approval_reason = ""


    if approval_items:

        approval_reason = (
            f"{capability} is a {risk}-risk action "
            "and requires user approval."
        )


    return AggregatedIntegrationResult(
        success=
            bool(
                succeeded
            ),

        capability=
            capability,

        routing_mode=
            routing_mode,

        sources_attempted=
            len(
                evidence
            ),

        sources_succeeded=
            len(
                succeeded
            ),

        evidence=
            evidence,

        requires_approval=
            bool(
                approval_items
            ),

        approval_reason=
            approval_reason,
    )


# ---------------------------------------------------------------------------
# Flatten Successful Data
# ---------------------------------------------------------------------------

def flatten_successful_data(
    result: AggregatedIntegrationResult,
):
    flattened = []


    for evidence in result.evidence:

        if not evidence.success:

            continue


        data = evidence.data


        if isinstance(
            data,
            list,
        ):

            flattened.extend(
                data
            )


        elif data is not None:

            flattened.append(
                data
            )


    return flattened