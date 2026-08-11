"""
E.V.I.E. - Integration Capability State

Created: August 10, 2026
Last Edited: August 10, 2026
Author: Max Maehara

Purpose:
    Determines which Phase 9 capabilities are actually usable for each
    connected account.

Important:
    A provider may expose a capability while a particular account does
    not have that service enabled.

Examples:
    - personal Google account may have Gmail
    - school Google identity may not have Gmail
    - institutional Google account may not be provisioned for Calendar
    - one account may support Tasks while another does not

Architecture:
    - provider definitions come from registry.py
    - account connection state comes from connections.py
    - provider metadata can disable service families
    - explicit per-account overrides remain authoritative
    - optional read-only probes can persist discovered capability state
"""

from __future__ import annotations

from dataclasses import (
    asdict,
    dataclass,
)

from .connections import (
    get_account,
    save_account,
)

from .registry import (
    get_integration_capability,
    list_provider_capabilities,
)


# ---------------------------------------------------------------------------
# Capability State
# ---------------------------------------------------------------------------

@dataclass
class AccountCapabilityState:
    provider: str

    account_id: str

    capability: str

    available: bool

    reason: str = ""

    source: str = ""


# ---------------------------------------------------------------------------
# Serialization
# ---------------------------------------------------------------------------

def capability_state_to_dict(
    state: AccountCapabilityState,
):
    return asdict(
        state
    )


# ---------------------------------------------------------------------------
# Explicit Overrides
# ---------------------------------------------------------------------------

def get_capability_overrides(
    account,
):
    overrides = (
        account.metadata.get(
            "capability_overrides",
            {},
        )
        or {}
    )


    if not isinstance(
        overrides,
        dict,
    ):

        return {}


    return overrides


# ---------------------------------------------------------------------------
# Set Capability State
# ---------------------------------------------------------------------------

def set_account_capability(
    provider: str,
    account_id: str,
    capability: str,
    available: bool,
    reason: str = "",
):
    """
    Persists an explicit capability availability override.

    Credentials are never modified here.
    """

    account = get_account(
        provider,
        account_id,
    )


    if account is None:

        raise RuntimeError(
            (
                "Integration account does not exist: "
                f"{provider}:{account_id}"
            )
        )


    overrides = get_capability_overrides(
        account
    )


    overrides[
        capability
    ] = {
        "available":
            bool(
                available
            ),

        "reason":
            str(
                reason
            ).strip(),
    }


    account.metadata[
        "capability_overrides"
    ] = overrides


    save_account(
        account
    )


    return get_account_capability_state(
        provider,
        account_id,
        capability,
    )


# ---------------------------------------------------------------------------
# Set Several Capabilities
# ---------------------------------------------------------------------------

def set_account_capabilities(
    provider: str,
    account_id: str,
    capabilities: list[str],
    available: bool,
    reason: str = "",
):
    states = []


    for capability in capabilities:

        states.append(
            set_account_capability(
                provider=
                    provider,

                account_id=
                    account_id,

                capability=
                    capability,

                available=
                    available,

                reason=
                    reason,
            )
        )


    return states


# ---------------------------------------------------------------------------
# Remove Override
# ---------------------------------------------------------------------------

def clear_account_capability_override(
    provider: str,
    account_id: str,
    capability: str,
):
    account = get_account(
        provider,
        account_id,
    )


    if account is None:

        return False


    overrides = get_capability_overrides(
        account
    )


    if capability not in overrides:

        return False


    del overrides[
        capability
    ]


    account.metadata[
        "capability_overrides"
    ] = overrides


    save_account(
        account
    )


    return True


# ---------------------------------------------------------------------------
# Google Service Families
# ---------------------------------------------------------------------------

GOOGLE_GMAIL_CAPABILITIES = {
    "email.search",
    "email.send",
}


GOOGLE_CALENDAR_CAPABILITIES = {
    "calendar.read",
    "calendar.create",
    "calendar.write",
}


GOOGLE_TASK_CAPABILITIES = {
    "tasks.read",
    "tasks.create",
    "tasks.complete",
}


# ---------------------------------------------------------------------------
# Inherited Override
# ---------------------------------------------------------------------------

def _inherited_google_override(
    account,
    capability: str,
):
    """
    Allows one proven service-level failure to disable related writes.

    Example:
        calendar.read=False because Google returned notACalendarUser

    Then:
        calendar.create must also be unavailable.
    """

    overrides = get_capability_overrides(
        account
    )


    # -----------------------------------------------------------------------
    # Calendar Family
    # -----------------------------------------------------------------------

    if (
        capability
        in GOOGLE_CALENDAR_CAPABILITIES
    ):

        read_override = (
            overrides.get(
                "calendar.read"
            )
        )


        if (
            capability
            != "calendar.read"
            and isinstance(
                read_override,
                dict,
            )
            and read_override.get(
                "available"
            )
            is False
        ):

            return AccountCapabilityState(
                provider=
                    account.provider,

                account_id=
                    account.account_id,

                capability=
                    capability,

                available=
                    False,

                reason=(
                    read_override.get(
                        "reason"
                    )
                    or
                    "Google Calendar is unavailable for this account."
                ),

                source=
                    "inherited_account_override",
            )


    # -----------------------------------------------------------------------
    # Tasks Family
    # -----------------------------------------------------------------------

    if (
        capability
        in GOOGLE_TASK_CAPABILITIES
    ):

        read_override = (
            overrides.get(
                "tasks.read"
            )
        )


        if (
            capability
            != "tasks.read"
            and isinstance(
                read_override,
                dict,
            )
            and read_override.get(
                "available"
            )
            is False
        ):

            return AccountCapabilityState(
                provider=
                    account.provider,

                account_id=
                    account.account_id,

                capability=
                    capability,

                available=
                    False,

                reason=(
                    read_override.get(
                        "reason"
                    )
                    or
                    "Google Tasks is unavailable for this account."
                ),

                source=
                    "inherited_account_override",
            )


    return None


# ---------------------------------------------------------------------------
# Google Metadata Interpretation
# ---------------------------------------------------------------------------

def _google_capability_state(
    account,
    capability: str,
):
    """
    Interprets service metadata collected by the Google provider.
    """

    # -----------------------------------------------------------------------
    # Gmail
    # -----------------------------------------------------------------------

    if (
        capability
        in GOOGLE_GMAIL_CAPABILITIES
        and account.metadata.get(
            "gmail_available"
        )
        is False
    ):

        return AccountCapabilityState(
            provider=
                account.provider,

            account_id=
                account.account_id,

            capability=
                capability,

            available=
                False,

            reason=
                "Gmail is not enabled for this Google account.",

            source=
                "provider_metadata",
        )


    # -----------------------------------------------------------------------
    # Tasks
    # -----------------------------------------------------------------------

    if (
        capability
        in GOOGLE_TASK_CAPABILITIES
        and account.metadata.get(
            "tasks_available"
        )
        is False
    ):

        return AccountCapabilityState(
            provider=
                account.provider,

            account_id=
                account.account_id,

            capability=
                capability,

            available=
                False,

            reason=
                "Google Tasks is not available for this account.",

            source=
                "provider_metadata",
        )


    # -----------------------------------------------------------------------
    # Calendar
    # -----------------------------------------------------------------------

    if (
        capability
        in GOOGLE_CALENDAR_CAPABILITIES
        and account.metadata.get(
            "calendar_available"
        )
        is False
    ):

        return AccountCapabilityState(
            provider=
                account.provider,

            account_id=
                account.account_id,

            capability=
                capability,

            available=
                False,

            reason=
                "Google Calendar is not available for this account.",

            source=
                "provider_metadata",
        )


    return None


# ---------------------------------------------------------------------------
# Get Capability State
# ---------------------------------------------------------------------------

def get_account_capability_state(
    provider: str,
    account_id: str,
    capability: str,
):
    """
    Determines whether one capability is usable for one account.
    """

    account = get_account(
        provider,
        account_id,
    )


    if account is None:

        return AccountCapabilityState(
            provider=
                provider,

            account_id=
                account_id,

            capability=
                capability,

            available=
                False,

            reason=
                "Account is not registered.",

            source=
                "account_state",
        )


    if not account.connected:

        return AccountCapabilityState(
            provider=
                provider,

            account_id=
                account_id,

            capability=
                capability,

            available=
                False,

            reason=
                "Account is disconnected.",

            source=
                "account_state",
        )


    if not account.authenticated:

        return AccountCapabilityState(
            provider=
                provider,

            account_id=
                account_id,

            capability=
                capability,

            available=
                False,

            reason=
                "Account is not authenticated.",

            source=
                "account_state",
        )


    # -----------------------------------------------------------------------
    # Provider Definition
    # -----------------------------------------------------------------------

    registered = (
        get_integration_capability(
            provider,
            capability,
        )
    )


    if registered is None:

        return AccountCapabilityState(
            provider=
                provider,

            account_id=
                account_id,

            capability=
                capability,

            available=
                False,

            reason=
                "Provider does not expose this capability.",

            source=
                "provider_registry",
        )


    # -----------------------------------------------------------------------
    # Exact Explicit Override
    # -----------------------------------------------------------------------

    overrides = get_capability_overrides(
        account
    )


    override = (
        overrides.get(
            capability
        )
    )


    if isinstance(
        override,
        dict,
    ):

        return AccountCapabilityState(
            provider=
                provider,

            account_id=
                account_id,

            capability=
                capability,

            available=
                bool(
                    override.get(
                        "available",
                        False,
                    )
                ),

            reason=
                str(
                    override.get(
                        "reason",
                        "",
                    )
                ),

            source=
                "account_override",
        )


    # -----------------------------------------------------------------------
    # Provider-Specific Logic
    # -----------------------------------------------------------------------

    if (
        account.provider.lower()
        == "google"
    ):

        inherited = (
            _inherited_google_override(
                account,
                capability,
            )
        )


        if inherited is not None:

            return inherited


        metadata_state = (
            _google_capability_state(
                account,
                capability,
            )
        )


        if metadata_state is not None:

            return metadata_state


    # -----------------------------------------------------------------------
    # Default
    # -----------------------------------------------------------------------

    return AccountCapabilityState(
        provider=
            provider,

        account_id=
            account_id,

        capability=
            capability,

        available=
            True,

        reason=
            "Account is connected and provider capability is registered.",

        source=
            "default",
    )


# ---------------------------------------------------------------------------
# Supports Capability
# ---------------------------------------------------------------------------

def account_supports_capability(
    provider: str,
    account_id: str,
    capability: str,
):
    return get_account_capability_state(
        provider,
        account_id,
        capability,
    ).available


# ---------------------------------------------------------------------------
# List Account Capabilities
# ---------------------------------------------------------------------------

def list_account_capabilities(
    provider: str,
    account_id: str,
):
    capabilities = (
        list_provider_capabilities(
            provider
        )
    )


    return [
        get_account_capability_state(
            provider,
            account_id,
            capability.name,
        )

        for capability
        in capabilities
    ]


# ---------------------------------------------------------------------------
# Google Capability Probe
# ---------------------------------------------------------------------------

def probe_google_account_capabilities(
    account_id: str,
):
    """
    Performs safe read-only probes against Google service families.

    This function never creates, modifies, completes, sends, or deletes
    anything.

    Results are persisted as account capability metadata/overrides.
    """

    account = get_account(
        "google",
        account_id,
    )


    if account is None:

        raise RuntimeError(
            (
                "Google account does not exist: "
                f"{account_id}"
            )
        )


    results = {}


    # -----------------------------------------------------------------------
    # Gmail
    #
    # Authentication already probes this during connect_google_account().
    # -----------------------------------------------------------------------

    gmail_available = (
        account.metadata.get(
            "gmail_available"
        )
    )


    if gmail_available is False:

        set_account_capabilities(
            provider=
                "google",

            account_id=
                account_id,

            capabilities=[
                "email.search",
                "email.send",
            ],

            available=
                False,

            reason=
                "Gmail is not enabled for this Google account.",
        )


        results[
            "gmail"
        ] = False


    else:

        results[
            "gmail"
        ] = True


    # -----------------------------------------------------------------------
    # Calendar
    # -----------------------------------------------------------------------

    try:

        from .providers.google.calendar import (
            google_calendar_events,
        )


        google_calendar_events(
            account_id=
                account_id,

            max_results=
                1,
        )


        account = get_account(
            "google",
            account_id,
        )


        account.metadata[
            "calendar_available"
        ] = True


        save_account(
            account
        )


        results[
            "calendar"
        ] = True


    except Exception as error:

        reason = (
            "Google Calendar capability probe failed: "
            f"{error}"
        )


        account = get_account(
            "google",
            account_id,
        )


        account.metadata[
            "calendar_available"
        ] = False


        save_account(
            account
        )


        set_account_capabilities(
            provider=
                "google",

            account_id=
                account_id,

            capabilities=[
                "calendar.read",
                "calendar.create",
            ],

            available=
                False,

            reason=
                reason,
        )


        results[
            "calendar"
        ] = False


    # -----------------------------------------------------------------------
    # Tasks
    # -----------------------------------------------------------------------

    try:

        from .providers.google.tasks import (
            google_task_lists,
        )


        google_task_lists(
            account_id
        )


        account = get_account(
            "google",
            account_id,
        )


        account.metadata[
            "tasks_available"
        ] = True


        save_account(
            account
        )


        results[
            "tasks"
        ] = True


    except Exception as error:

        reason = (
            "Google Tasks capability probe failed: "
            f"{error}"
        )


        account = get_account(
            "google",
            account_id,
        )


        account.metadata[
            "tasks_available"
        ] = False


        save_account(
            account
        )


        set_account_capabilities(
            provider=
                "google",

            account_id=
                account_id,

            capabilities=[
                "tasks.read",
                "tasks.create",
                "tasks.complete",
            ],

            available=
                False,

            reason=
                reason,
        )


        results[
            "tasks"
        ] = False


    return results