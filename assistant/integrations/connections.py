"""
E.V.I.E. - Integration Connections

Created: August 10, 2026
Author: Max Maehara

Purpose:
    Persists connected account metadata and connection state.

Security:
    Credentials are NOT stored here.

    Secrets live only in assistant.integrations.credentials.
"""

from __future__ import annotations

import json

from pathlib import Path

from .accounts import (
    IntegrationAccount,
    account_from_dict,
    account_to_dict,
)


# ---------------------------------------------------------------------------
# Storage Path
# ---------------------------------------------------------------------------

PROJECT_ROOT = (
    Path(
        __file__
    )
    .resolve()
    .parents[2]
)


RUNTIME_DIRECTORY = (
    PROJECT_ROOT
    / "runtime"
    / "integrations"
)


ACCOUNTS_FILE = (
    RUNTIME_DIRECTORY
    / "accounts.json"
)


# ---------------------------------------------------------------------------
# Ensure Runtime
# ---------------------------------------------------------------------------

def ensure_runtime_directory():
    RUNTIME_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )


# ---------------------------------------------------------------------------
# Load Accounts
# ---------------------------------------------------------------------------

def load_accounts():
    ensure_runtime_directory()


    if not ACCOUNTS_FILE.exists():

        return []


    try:

        payload = json.loads(
            ACCOUNTS_FILE.read_text(
                encoding="utf-8"
            )
        )

    except (
        json.JSONDecodeError,
        OSError,
    ):

        return []


    if not isinstance(
        payload,
        list,
    ):

        return []


    accounts = []


    for item in payload:

        if isinstance(
            item,
            dict,
        ):

            accounts.append(
                account_from_dict(
                    item
                )
            )


    return accounts


# ---------------------------------------------------------------------------
# Save Accounts
# ---------------------------------------------------------------------------

def save_accounts(
    accounts,
):
    ensure_runtime_directory()


    payload = [
        account_to_dict(
            account
        )

        for account
        in accounts
    ]


    ACCOUNTS_FILE.write_text(
        json.dumps(
            payload,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# Get Account
# ---------------------------------------------------------------------------

def get_account(
    provider: str,
    account_id: str,
):
    provider = (
        provider
        .strip()
        .lower()
    )


    account_id = (
        account_id
        .strip()
        .lower()
    )


    for account in load_accounts():

        if (
            account.provider.lower()
            == provider
            and account.account_id.lower()
            == account_id
        ):

            return account


    return None


# ---------------------------------------------------------------------------
# Upsert Account
# ---------------------------------------------------------------------------

def save_account(
    account: IntegrationAccount,
):
    accounts = (
        load_accounts()
    )


    replaced = False


    for index, existing in enumerate(
        accounts
    ):

        if (
            existing.provider.lower()
            == account.provider.lower()
            and existing.account_id.lower()
            == account.account_id.lower()
        ):

            accounts[
                index
            ] = account

            replaced = True

            break


    if not replaced:

        accounts.append(
            account
        )


    save_accounts(
        accounts
    )


    return account


# ---------------------------------------------------------------------------
# Remove Account
# ---------------------------------------------------------------------------

def remove_account(
    provider: str,
    account_id: str,
):
    accounts = (
        load_accounts()
    )


    remaining = [
        account

        for account
        in accounts

        if not (
            account.provider.lower()
            == provider.lower()
            and account.account_id.lower()
            == account_id.lower()
        )
    ]


    changed = (
        len(remaining)
        != len(accounts)
    )


    if changed:

        save_accounts(
            remaining
        )


    return changed


# ---------------------------------------------------------------------------
# List Provider Accounts
# ---------------------------------------------------------------------------

def list_provider_accounts(
    provider: str,
):
    provider = (
        provider
        .strip()
        .lower()
    )


    return [
        account

        for account
        in load_accounts()

        if account.provider.lower()
        == provider
    ]


# ---------------------------------------------------------------------------
# Standalone Test
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    print(
        "E.V.I.E. Integration Connections"
    )

    print(
        "-------------------------------"
    )


    test = IntegrationAccount(
        account_id="test-account",
        provider="mock",
        display_name="Phase 9 Test Account",
        connected=True,
        authenticated=True,
        scopes=[
            "calendar.read",
            "email.read",
        ],
    )


    save_account(
        test
    )


    print(
        "Saved:",
        get_account(
            "mock",
            "test-account",
        )
    )


    print(
        "Provider accounts:",
        list_provider_accounts(
            "mock"
        )
    )


    remove_account(
        "mock",
        "test-account",
    )


    print(
        "After removal:",
        get_account(
            "mock",
            "test-account",
        )
    )