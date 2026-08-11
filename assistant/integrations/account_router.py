"""
E.V.I.E. - Integration Account Router

Created: August 10, 2026
Author: Max Maehara

Purpose:
    Resolves which connected Phase 9 account or accounts should satisfy
    an integration capability request.

Routing Modes:
    explicit_account
        Use one specifically requested account.

    single_best
        Select the best available connected account.

    all_available
        Return every connected account that supports the capability.

This layer performs routing only.

It does not execute provider functions.
"""

from __future__ import annotations

from dataclasses import (
    dataclass,
)

from .capabilities import (
    account_supports_capability,
    get_account_capability_state,
)

from .connections import (
    get_account,
    load_accounts,
)

from .registry import (
    load_default_integrations,
)


# ---------------------------------------------------------------------------
# Route
# ---------------------------------------------------------------------------

@dataclass
class RoutedAccount:
    provider: str

    account_id: str

    display_name: str

    email: str

    capability: str

    reason: str = ""


# ---------------------------------------------------------------------------
# Ensure Provider Definitions
# ---------------------------------------------------------------------------

def ensure_integrations_loaded():
    """
    Capability routing requires provider definitions to exist in the
    current Python process.
    """

    load_default_integrations(
        include_mock=False
    )


# ---------------------------------------------------------------------------
# Candidate Accounts
# ---------------------------------------------------------------------------

def get_capability_candidates(
    capability: str,
    provider: str | None = None,
):
    ensure_integrations_loaded()


    accounts = load_accounts()


    candidates = []


    for account in accounts:

        if provider:

            if (
                account.provider.lower()
                != provider.lower()
            ):

                continue


        if not account.connected:

            continue


        if not account.authenticated:

            continue


        state = (
            get_account_capability_state(
                account.provider,
                account.account_id,
                capability,
            )
        )


        if not state.available:

            continue


        candidates.append(
            RoutedAccount(
                provider=
                    account.provider,

                account_id=
                    account.account_id,

                display_name=
                    account.display_name,

                email=
                    account.email,

                capability=
                    capability,

                reason=
                    state.reason,
            )
        )


    return candidates


# ---------------------------------------------------------------------------
# Explicit Account
# ---------------------------------------------------------------------------

def route_explicit_account(
    capability: str,
    provider: str,
    account_id: str,
):
    ensure_integrations_loaded()


    account = get_account(
        provider,
        account_id,
    )


    if account is None:

        raise RuntimeError(
            (
                "Requested integration account "
                "does not exist: "
                f"{provider}:{account_id}"
            )
        )


    state = (
        get_account_capability_state(
            provider,
            account_id,
            capability,
        )
    )


    if not state.available:

        raise RuntimeError(
            (
                f"{provider}:{account_id} "
                f"cannot use {capability}. "
                f"{state.reason}"
            )
        )


    return [
        RoutedAccount(
            provider=
                account.provider,

            account_id=
                account.account_id,

            display_name=
                account.display_name,

            email=
                account.email,

            capability=
                capability,

            reason=
                state.reason,
        )
    ]


# ---------------------------------------------------------------------------
# Score Candidate
# ---------------------------------------------------------------------------

def score_candidate(
    candidate: RoutedAccount,
):
    """
    Simple deterministic routing score.

    This can later evolve to include:
        - personal vs school labels
        - provider preference
        - recent successful use
        - user preference
        - intent-aware routing
    """

    score = 0


    if candidate.email:

        score += 10


    if candidate.display_name:

        score += 5


    return score


# ---------------------------------------------------------------------------
# Route Accounts
# ---------------------------------------------------------------------------

def route_accounts(
    capability: str,
    mode: str = "all_available",
    provider: str | None = None,
    account_id: str | None = None,
):
    """
    Main Phase 9 account routing entry point.
    """

    mode = (
        mode
        .strip()
        .lower()
    )


    # -----------------------------------------------------------------------
    # Explicit Account
    # -----------------------------------------------------------------------

    if (
        mode
        == "explicit_account"
    ):

        if not provider:

            raise ValueError(
                "explicit_account routing requires provider."
            )


        if not account_id:

            raise ValueError(
                "explicit_account routing requires account_id."
            )


        return route_explicit_account(
            capability=
                capability,

            provider=
                provider,

            account_id=
                account_id,
        )


    # -----------------------------------------------------------------------
    # Candidates
    # -----------------------------------------------------------------------

    candidates = (
        get_capability_candidates(
            capability=
                capability,

            provider=
                provider,
        )
    )


    # -----------------------------------------------------------------------
    # All Available
    # -----------------------------------------------------------------------

    if (
        mode
        == "all_available"
    ):

        return candidates


    # -----------------------------------------------------------------------
    # Single Best
    # -----------------------------------------------------------------------

    if (
        mode
        == "single_best"
    ):

        if not candidates:

            return []


        candidates = sorted(
            candidates,
            key=
                score_candidate,
            reverse=True,
        )


        return [
            candidates[
                0
            ]
        ]


    raise ValueError(
        (
            "Unknown integration routing mode: "
            f"{mode}"
        )
    )