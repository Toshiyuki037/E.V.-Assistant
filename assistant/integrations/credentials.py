"""
E.V.I.E. - Credential Store

Created: August 10, 2026
Author: Max Maehara

Purpose:
    Securely stores Phase 9 integration credentials outside normal
    memory, logs, prompts, Git, and configuration files.

Security:
    - tokens are never stored in memory.db
    - tokens are never stored in project knowledge
    - tokens are never written to normal logs
    - tokens are stored through the operating system credential backend
"""

from __future__ import annotations

import json

import keyring


SERVICE_NAME = (
    "EVIE_INTEGRATIONS"
)


# ---------------------------------------------------------------------------
# Credential Key
# ---------------------------------------------------------------------------

def credential_key(
    provider: str,
    account_id: str,
):
    return (
        f"{provider.strip().lower()}:"
        f"{account_id.strip().lower()}"
    )


# ---------------------------------------------------------------------------
# Store Credentials
# ---------------------------------------------------------------------------

def store_credentials(
    provider: str,
    account_id: str,
    credentials: dict,
):
    key = credential_key(
        provider,
        account_id,
    )


    payload = json.dumps(
        credentials,
        ensure_ascii=False,
    )


    keyring.set_password(
        SERVICE_NAME,
        key,
        payload,
    )


    return True


# ---------------------------------------------------------------------------
# Load Credentials
# ---------------------------------------------------------------------------

def load_credentials(
    provider: str,
    account_id: str,
):
    key = credential_key(
        provider,
        account_id,
    )


    payload = keyring.get_password(
        SERVICE_NAME,
        key,
    )


    if not payload:

        return None


    try:

        value = json.loads(
            payload
        )

    except json.JSONDecodeError:

        return None


    if not isinstance(
        value,
        dict,
    ):

        return None


    return value


# ---------------------------------------------------------------------------
# Delete Credentials
# ---------------------------------------------------------------------------

def delete_credentials(
    provider: str,
    account_id: str,
):
    key = credential_key(
        provider,
        account_id,
    )


    try:

        keyring.delete_password(
            SERVICE_NAME,
            key,
        )

    except keyring.errors.PasswordDeleteError:

        return False


    return True


# ---------------------------------------------------------------------------
# Check Credentials
# ---------------------------------------------------------------------------

def has_credentials(
    provider: str,
    account_id: str,
):
    return (
        load_credentials(
            provider,
            account_id,
        )
        is not None
    )


# ---------------------------------------------------------------------------
# Standalone Test
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    print(
        "E.V.I.E. Credential Store"
    )

    print(
        "--------------------------"
    )


    provider = "mock"

    account_id = "test-account"


    print(
        "Writing test credential..."
    )


    store_credentials(
        provider,
        account_id,
        {
            "access_token":
                "phase9-test-token"
        },
    )


    print(
        "Exists:",
        has_credentials(
            provider,
            account_id,
        ),
    )


    loaded = (
        load_credentials(
            provider,
            account_id,
        )
    )


    print(
        "Loaded:",
        bool(
            loaded
        ),
    )


    print(
        "Deleting..."
    )


    delete_credentials(
        provider,
        account_id,
    )


    print(
        "Exists after delete:",
        has_credentials(
            provider,
            account_id,
        ),
    )