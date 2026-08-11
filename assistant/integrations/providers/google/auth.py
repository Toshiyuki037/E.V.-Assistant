"""
E.V.I.E. - Google Authentication

Created: August 10, 2026
Last Edited: August 10, 2026
Author: Max Maehara

Purpose:
    Provides Google OAuth authentication for Phase 9.

Architecture:
    Google identity discovery is independent of Gmail.

    This allows E.V.I.E. to connect Google accounts that provide
    Calendar / People access even when Gmail is disabled, such as
    institutional Google Workspace accounts that use Outlook for mail.

Security:
    - OAuth client configuration stays under ignored runtime storage
    - access / refresh credentials are stored through E.V.I.E.'s
      OS-backed credential store
    - tokens are never written to token.json
    - tokens are never stored in memory.db
    - tokens are never stored in project knowledge
    - tokens are never printed by this module

Compatibility:
    E.V.I.E. currently uses the Google account email as account_id.

    Google OpenID Connect's stable "sub" identifier is also preserved
    in account metadata for future stable identity resolution.
"""

from __future__ import annotations

import json

from pathlib import Path

from google.auth.transport.requests import (
    AuthorizedSession,
    Request,
)

from google.oauth2.credentials import (
    Credentials,
)

from google_auth_oauthlib.flow import (
    InstalledAppFlow,
)

from googleapiclient.discovery import (
    build,
)

from googleapiclient.errors import (
    HttpError,
)

from assistant.integrations.accounts import (
    IntegrationAccount,
)

from assistant.integrations.connections import (
    get_account,
    save_account,
)

from assistant.integrations.credentials import (
    delete_credentials,
    load_credentials,
    store_credentials,
)


# ---------------------------------------------------------------------------
# Provider
# ---------------------------------------------------------------------------

PROVIDER = "google"


# ---------------------------------------------------------------------------
# OAuth Scopes
# ---------------------------------------------------------------------------

GOOGLE_SCOPES = [
    "openid",

    "https://www.googleapis.com/auth/userinfo.email",

    "https://www.googleapis.com/auth/userinfo.profile",

    # Gmail
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",

    # Calendar
    "https://www.googleapis.com/auth/calendar.events",

    # Contacts
    "https://www.googleapis.com/auth/contacts.readonly",

    # Tasks
    "https://www.googleapis.com/auth/tasks",
]


# ---------------------------------------------------------------------------
# OpenID Connect
# ---------------------------------------------------------------------------

GOOGLE_USERINFO_ENDPOINT = (
    "https://openidconnect.googleapis.com/v1/userinfo"
)


# ---------------------------------------------------------------------------
# Runtime Paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = (
    Path(
        __file__
    )
    .resolve()
    .parents[4]
)


GOOGLE_RUNTIME_DIRECTORY = (
    PROJECT_ROOT
    / "runtime"
    / "integrations"
    / "google"
)


CLIENT_SECRET_FILE = (
    GOOGLE_RUNTIME_DIRECTORY
    / "client_secret.json"
)


# ---------------------------------------------------------------------------
# Runtime Directory
# ---------------------------------------------------------------------------

def ensure_google_runtime():
    GOOGLE_RUNTIME_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )


# ---------------------------------------------------------------------------
# Client Secret
# ---------------------------------------------------------------------------

def client_secret_available():
    return (
        CLIENT_SECRET_FILE.exists()
        and CLIENT_SECRET_FILE.is_file()
    )


# ---------------------------------------------------------------------------
# Credential Serialization
# ---------------------------------------------------------------------------

def credentials_to_dict(
    credentials: Credentials,
):
    """
    Converts Google Credentials into a dictionary suitable for
    E.V.I.E.'s secure OS credential store.
    """

    return json.loads(
        credentials.to_json()
    )


# ---------------------------------------------------------------------------
# Credential Reconstruction
# ---------------------------------------------------------------------------

def credentials_from_dict(
    data: dict,
):
    """
    Restores Google Credentials from securely stored credential data.

    The scopes stored by Google are preferred when available so older
    credentials can still be inspected during migration.
    """

    stored_scopes = (
        data.get(
            "scopes"
        )
        or GOOGLE_SCOPES
    )


    return Credentials.from_authorized_user_info(
        data,
        stored_scopes,
    )


# ---------------------------------------------------------------------------
# Store Google Credentials
# ---------------------------------------------------------------------------

def store_google_credentials(
    account_id: str,
    credentials: Credentials,
):
    return store_credentials(
        provider=PROVIDER,
        account_id=account_id,
        credentials=credentials_to_dict(
            credentials
        ),
    )


# ---------------------------------------------------------------------------
# Load Google Credentials
# ---------------------------------------------------------------------------

def load_google_credentials(
    account_id: str,
):
    stored = load_credentials(
        PROVIDER,
        account_id,
    )


    if not stored:

        return None


    try:

        return credentials_from_dict(
            stored
        )

    except Exception:

        return None


# ---------------------------------------------------------------------------
# Ensure Valid Credentials
# ---------------------------------------------------------------------------

def ensure_valid_credentials(
    account_id: str,
):
    """
    Loads Google credentials and refreshes them when necessary.

    Refreshed credentials are written back to the secure credential
    store.
    """

    credentials = load_google_credentials(
        account_id
    )


    if credentials is None:

        return None


    if credentials.valid:

        return credentials


    if (
        credentials.expired
        and credentials.refresh_token
    ):

        credentials.refresh(
            Request()
        )


        store_google_credentials(
            account_id,
            credentials,
        )


        return credentials


    return None


# ---------------------------------------------------------------------------
# Google Identity
# ---------------------------------------------------------------------------

def get_google_identity(
    credentials: Credentials,
):
    """
    Retrieves the authenticated Google identity through Google's
    OpenID Connect UserInfo endpoint.

    This intentionally does NOT depend on Gmail.
    """

    session = AuthorizedSession(
        credentials
    )


    response = session.get(
        GOOGLE_USERINFO_ENDPOINT,
        timeout=30,
    )


    response.raise_for_status()


    identity = response.json()


    if not isinstance(
        identity,
        dict,
    ):

        raise RuntimeError(
            "Google identity response was invalid."
        )


    email = (
        str(
            identity.get(
                "email",
                "",
            )
        )
        .strip()
    )


    subject = (
        str(
            identity.get(
                "sub",
                "",
            )
        )
        .strip()
    )


    if not email:

        raise RuntimeError(
            (
                "Google did not return an email address "
                "for the authenticated account."
            )
        )


    if not subject:

        raise RuntimeError(
            (
                "Google did not return a stable OpenID "
                "subject identifier."
            )
        )


    return {
        "sub":
            subject,

        "email":
            email,

        "email_verified":
            bool(
                identity.get(
                    "email_verified",
                    False,
                )
            ),

        "name":
            str(
                identity.get(
                    "name",
                    "",
                )
            ),

        "given_name":
            str(
                identity.get(
                    "given_name",
                    "",
                )
            ),

        "family_name":
            str(
                identity.get(
                    "family_name",
                    "",
                )
            ),

        "picture":
            str(
                identity.get(
                    "picture",
                    "",
                )
            ),

        "hosted_domain":
            str(
                identity.get(
                    "hd",
                    "",
                )
            ),
    }


# ---------------------------------------------------------------------------
# Gmail Availability Probe
# ---------------------------------------------------------------------------

def check_gmail_available(
    credentials: Credentials,
):
    """
    Determines whether Gmail is enabled for the authenticated account.

    Gmail being unavailable must NOT prevent the Google account from
    connecting.

    Some Google Workspace accounts use Google identity / Calendar /
    People while institutional email is provided by another system.
    """

    try:

        service = build(
            "gmail",
            "v1",
            credentials=credentials,
            cache_discovery=False,
        )


        profile = (
            service.users()
            .getProfile(
                userId="me"
            )
            .execute()
        )


        return {
            "available":
                True,

            "email":
                (
                    profile.get(
                        "emailAddress",
                        ""
                    )
                    or ""
                ),
        }


    except HttpError as error:

        status_code = getattr(
            error.resp,
            "status",
            None,
        )


        return {
            "available":
                False,

            "status_code":
                status_code,

            "reason":
                "gmail_unavailable",
        }


    except Exception:

        return {
            "available":
                False,

            "status_code":
                None,

            "reason":
                "gmail_probe_failed",
        }


# ---------------------------------------------------------------------------
# Connect Google Account
# ---------------------------------------------------------------------------

def connect_google_account():
    """
    Runs Google's installed-application OAuth flow.

    Identity discovery uses OpenID Connect and therefore works even
    when Gmail is not enabled for the Google account.

    Account metadata is persisted separately from credentials.
    """

    ensure_google_runtime()


    if not client_secret_available():

        raise FileNotFoundError(
            (
                "Google OAuth client file was not found at: "
                f"{CLIENT_SECRET_FILE}"
            )
        )


    flow = InstalledAppFlow.from_client_secrets_file(
        str(
            CLIENT_SECRET_FILE
        ),
        GOOGLE_SCOPES,
    )


    credentials = flow.run_local_server(
        port=0,

        prompt="select_account",

        access_type="offline",
    )


    # -----------------------------------------------------------------------
    # Discover Google Identity
    # -----------------------------------------------------------------------

    identity = get_google_identity(
        credentials
    )


    email = (
        identity[
            "email"
        ]
        .strip()
        .lower()
    )


    # -----------------------------------------------------------------------
    # Preserve Existing E.V.I.E. Account-ID Architecture
    # -----------------------------------------------------------------------

    account_id = email


    # -----------------------------------------------------------------------
    # Probe Optional Gmail Capability
    # -----------------------------------------------------------------------

    gmail_status = (
        check_gmail_available(
            credentials
        )
    )


    # -----------------------------------------------------------------------
    # Secure Credential Persistence
    # -----------------------------------------------------------------------

    store_google_credentials(
        account_id,
        credentials,
    )


    # -----------------------------------------------------------------------
    # Display Name
    # -----------------------------------------------------------------------

    display_name = (
        identity.get(
            "name"
        )
        or email
    )


    # -----------------------------------------------------------------------
    # Account Metadata
    # -----------------------------------------------------------------------

    account = IntegrationAccount(
        account_id=
            account_id,

        provider=
            PROVIDER,

        display_name=
            display_name,

        email=
            email,

        connected=
            True,

        authenticated=
            True,

        scopes=list(
            GOOGLE_SCOPES
        ),

        metadata={
            # ---------------------------------------------------------------
            # Authentication
            # ---------------------------------------------------------------

            "auth_type":
                "oauth2_installed_app",

            # ---------------------------------------------------------------
            # Stable Google Identity
            # ---------------------------------------------------------------

            "google_sub":
                identity.get(
                    "sub"
                ),

            "email_verified":
                identity.get(
                    "email_verified",
                    False,
                ),

            "hosted_domain":
                identity.get(
                    "hosted_domain",
                    "",
                ),

            # ---------------------------------------------------------------
            # Optional Identity Information
            # ---------------------------------------------------------------

            "given_name":
                identity.get(
                    "given_name",
                    "",
                ),

            "family_name":
                identity.get(
                    "family_name",
                    "",
                ),

            "picture":
                identity.get(
                    "picture",
                    "",
                ),

            # ---------------------------------------------------------------
            # Service Availability
            # ---------------------------------------------------------------

            "gmail_available":
                bool(
                    gmail_status.get(
                        "available",
                        False,
                    )
                ),
        },
    )


    save_account(
        account
    )


    return account


# ---------------------------------------------------------------------------
# Get Connected Google Account
# ---------------------------------------------------------------------------

def get_google_account(
    account_id: str,
):
    return get_account(
        PROVIDER,
        account_id,
    )


# ---------------------------------------------------------------------------
# Disconnect Google Account
# ---------------------------------------------------------------------------

def disconnect_google_account(
    account_id: str,
):
    """
    Removes locally stored Google credentials and marks the integration
    account disconnected.

    Remote Google token revocation can be added later as a separate
    Phase 9 lifecycle operation.
    """

    account = get_google_account(
        account_id
    )


    deleted = delete_credentials(
        PROVIDER,
        account_id,
    )


    if account is not None:

        account.connected = False

        account.authenticated = False


        save_account(
            account
        )


    return {
        "account_id":
            account_id,

        "credentials_deleted":
            deleted,

        "connected":
            False,
    }


# ---------------------------------------------------------------------------
# Build Google API Service
# ---------------------------------------------------------------------------

def build_google_service(
    account_id: str,
    service_name: str,
    version: str,
):
    """
    Builds an authenticated Google API client using securely stored
    account credentials.
    """

    credentials = ensure_valid_credentials(
        account_id
    )


    if credentials is None:

        raise RuntimeError(
            (
                "Google account is not authenticated: "
                f"{account_id}"
            )
        )


    return build(
        service_name,
        version,
        credentials=credentials,
        cache_discovery=False,
    )


# ---------------------------------------------------------------------------
# Account Capability Information
# ---------------------------------------------------------------------------

def get_google_service_status(
    account_id: str,
):
    """
    Returns non-secret service availability metadata for a connected
    Google account.
    """

    account = get_google_account(
        account_id
    )


    if account is None:

        return {
            "connected":
                False,

            "account_id":
                account_id,
        }


    return {
        "connected":
            account.connected,

        "authenticated":
            account.authenticated,

        "account_id":
            account.account_id,

        "email":
            account.email,

        "gmail_available":
            bool(
                account.metadata.get(
                    "gmail_available",
                    False,
                )
            ),

        "hosted_domain":
            account.metadata.get(
                "hosted_domain",
                "",
            ),
    }


# ---------------------------------------------------------------------------
# Standalone Diagnostic
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    print(
        "E.V.I.E. Google Authentication"
    )

    print(
        "------------------------------"
    )


    print(
        "Client secret:",
        CLIENT_SECRET_FILE,
    )


    print(
        "Available:",
        client_secret_available(),
    )


    print()

    print(
        "Identity method: OpenID Connect"
    )