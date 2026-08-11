"""
E.V.I.E. - Charles Schwab Authentication

Created: August 10, 2026
Author: Max Maehara

Purpose:
    Handles Charles Schwab OAuth authentication for E.V.I.E.

Configuration:
    Static Schwab application credentials are loaded from:

        runtime/integrations/schwab/config.json

    Expected format:

        {
            "client_id": "...",
            "client_secret": "...",
            "callback_url": "https://127.0.0.1",
            "account_id": "primary"
        }

Security:
    - config.json MUST be excluded from Git.
    - OAuth access and refresh tokens are stored through
      E.V.I.E.'s credential store.
    - OAuth tokens are not stored in accounts.json.
"""

from __future__ import annotations

import base64
import json
import secrets
import time
import webbrowser

from pathlib import Path

from urllib.parse import (
    parse_qs,
    urlencode,
    urlparse,
)

import requests

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

PROVIDER = "schwab"

DEFAULT_ACCOUNT_ID = "primary"


# ---------------------------------------------------------------------------
# Schwab OAuth URLs
# ---------------------------------------------------------------------------

AUTHORIZE_URL = (
    "https://api.schwabapi.com/v1/oauth/authorize"
)

TOKEN_URL = (
    "https://api.schwabapi.com/v1/oauth/token"
)


# ---------------------------------------------------------------------------
# Project Root
# ---------------------------------------------------------------------------

PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[4]
)


# ---------------------------------------------------------------------------
# Configuration Path
# ---------------------------------------------------------------------------

SCHWAB_CONFIG_PATH = (
    PROJECT_ROOT
    / "runtime"
    / "integrations"
    / "schwab"
    / "config.json"
)


# ---------------------------------------------------------------------------
# Load Schwab App Configuration
# ---------------------------------------------------------------------------

def load_schwab_app_config():
    """
    Loads the static Schwab developer application configuration.

    The Client ID and Client Secret live in a local Git-ignored
    configuration file.

    OAuth access/refresh tokens are NOT stored here.
    """

    if not SCHWAB_CONFIG_PATH.exists():

        raise RuntimeError(
            (
                "Schwab configuration file was not found:\n"
                f"{SCHWAB_CONFIG_PATH}"
            )
        )


    try:

        with SCHWAB_CONFIG_PATH.open(
            "r",
            encoding="utf-8",
        ) as file:

            config = json.load(
                file
            )


    except json.JSONDecodeError as error:

        raise RuntimeError(
            (
                "Schwab config.json contains invalid JSON: "
                f"{error}"
            )
        ) from error


    if not isinstance(
        config,
        dict,
    ):

        raise RuntimeError(
            "Schwab config.json must contain a JSON object."
        )


    client_id = (
        str(
            config.get(
                "client_id",
                "",
            )
        )
        .strip()
    )


    client_secret = (
        str(
            config.get(
                "client_secret",
                "",
            )
        )
        .strip()
    )


    callback_url = (
        str(
            config.get(
                "callback_url",
                "",
            )
        )
        .strip()
    )


    account_id = (
        str(
            config.get(
                "account_id",
                DEFAULT_ACCOUNT_ID,
            )
        )
        .strip()
        or DEFAULT_ACCOUNT_ID
    )


    if not client_id:

        raise RuntimeError(
            (
                "Schwab client_id is missing "
                "from config.json."
            )
        )


    if not client_secret:

        raise RuntimeError(
            (
                "Schwab client_secret is missing "
                "from config.json."
            )
        )


    if not callback_url:

        raise RuntimeError(
            (
                "Schwab callback_url is missing "
                "from config.json."
            )
        )


    return {
        "app_key":
            client_id,

        "app_secret":
            client_secret,

        "callback_url":
            callback_url,

        "account_id":
            account_id,
    }


# ---------------------------------------------------------------------------
# Configuration Status
# ---------------------------------------------------------------------------

def schwab_app_configured():
    """
    Returns True when a complete Schwab application configuration
    can be loaded.
    """

    try:

        load_schwab_app_config()

        return True


    except Exception:

        return False


# ---------------------------------------------------------------------------
# Basic Authentication Header
# ---------------------------------------------------------------------------

def _basic_auth_header(
    app_key: str,
    app_secret: str,
):
    """
    Creates the HTTP Basic authorization value required by the
    Schwab token endpoint.
    """

    raw = (
        f"{app_key}:{app_secret}"
        .encode(
            "utf-8"
        )
    )


    encoded = (
        base64.b64encode(
            raw
        )
        .decode(
            "ascii"
        )
    )


    return (
        f"Basic {encoded}"
    )


# ---------------------------------------------------------------------------
# Authorization URL
# ---------------------------------------------------------------------------

def build_schwab_authorization_url():
    """
    Creates a new Schwab OAuth authorization URL and CSRF state value.
    """

    config = (
        load_schwab_app_config()
    )


    state = (
        secrets.token_urlsafe(
            32
        )
    )


    query = urlencode(
        {
            "client_id":
                config[
                    "app_key"
                ],

            "redirect_uri":
                config[
                    "callback_url"
                ],

            "response_type":
                "code",

            "state":
                state,
        }
    )


    url = (
        AUTHORIZE_URL
        + "?"
        + query
    )


    return {
        "url":
            url,

        "state":
            state,

        "account_id":
            config[
                "account_id"
            ],
    }


# ---------------------------------------------------------------------------
# Parse Schwab Redirect
# ---------------------------------------------------------------------------

def parse_schwab_redirect(
    redirected_url: str,
):
    """
    Extracts the OAuth authorization code and state from the final
    Schwab redirect URL.
    """

    redirected_url = (
        str(
            redirected_url
        )
        .strip()
    )


    if not redirected_url:

        raise RuntimeError(
            "No Schwab callback URL was provided."
        )


    parsed = urlparse(
        redirected_url
    )


    query = parse_qs(
        parsed.query
    )


    oauth_error = (
        query.get(
            "error",
            [""],
        )[0]
    )


    if oauth_error:

        description = (
            query.get(
                "error_description",
                [""],
            )[0]
        )


        message = (
            "Schwab authorization failed: "
            f"{oauth_error}"
        )


        if description:

            message += (
                f" - {description}"
            )


        raise RuntimeError(
            message
        )


    code = (
        query.get(
            "code",
            [""],
        )[0]
    )


    state = (
        query.get(
            "state",
            [""],
        )[0]
    )


    if not code:

        raise RuntimeError(
            (
                "The Schwab callback URL did not contain "
                "an authorization code."
            )
        )


    return {
        "code":
            code,

        "state":
            state,
    }


# ---------------------------------------------------------------------------
# Store OAuth Credentials
# ---------------------------------------------------------------------------

def _store_oauth_credentials(
    account_id: str,
    credentials: dict,
):
    """
    Adds local expiration metadata and stores OAuth credentials using
    E.V.I.E.'s credential backend.
    """

    credentials = dict(
        credentials
    )


    expires_in = int(
        credentials.get(
            "expires_in",
            1800,
        )
        or 1800
    )


    credentials[
        "obtained_at"
    ] = time.time()


    credentials[
        "expires_at"
    ] = (
        time.time()
        + expires_in
    )


    store_credentials(
        provider=
            PROVIDER,

        account_id=
            account_id,

        credentials=
            credentials,
    )


    return credentials


# ---------------------------------------------------------------------------
# Exchange Authorization Code
# ---------------------------------------------------------------------------

def exchange_schwab_code(
    code: str,
    account_id: str | None = None,
):
    """
    Exchanges the temporary Schwab authorization code for OAuth tokens.
    """

    config = (
        load_schwab_app_config()
    )


    if account_id is None:

        account_id = (
            config[
                "account_id"
            ]
        )


    response = requests.post(
        TOKEN_URL,

        headers={
            "Authorization":
                _basic_auth_header(
                    config[
                        "app_key"
                    ],
                    config[
                        "app_secret"
                    ],
                ),

            "Content-Type":
                "application/x-www-form-urlencoded",

            "Accept":
                "application/json",
        },

        data={
            "grant_type":
                "authorization_code",

            "code":
                code,

            "redirect_uri":
                config[
                    "callback_url"
                ],
        },

        timeout=
            30,
    )


    if not response.ok:

        raise RuntimeError(
            (
                "Schwab token exchange failed "
                f"with HTTP {response.status_code}: "
                f"{response.text[:1000]}"
            )
        )


    try:

        credentials = (
            response.json()
        )


    except ValueError as error:

        raise RuntimeError(
            (
                "Schwab token endpoint returned "
                "an invalid JSON response."
            )
        ) from error


    if not credentials.get(
        "access_token"
    ):

        raise RuntimeError(
            (
                "Schwab token response did not contain "
                "an access token."
            )
        )


    return _store_oauth_credentials(
        account_id=
            account_id,

        credentials=
            credentials,
    )


# ---------------------------------------------------------------------------
# Refresh OAuth Credentials
# ---------------------------------------------------------------------------

def refresh_schwab_credentials(
    account_id: str = DEFAULT_ACCOUNT_ID,
):
    """
    Refreshes the current Schwab OAuth access token.
    """

    config = (
        load_schwab_app_config()
    )


    credentials = load_credentials(
        PROVIDER,
        account_id,
    )


    if not credentials:

        raise RuntimeError(
            (
                "Schwab OAuth credentials were not found "
                f"for account '{account_id}'."
            )
        )


    refresh_token = (
        credentials.get(
            "refresh_token"
        )
    )


    if not refresh_token:

        raise RuntimeError(
            (
                "Schwab refresh token is unavailable. "
                "Reconnect the Schwab account."
            )
        )


    response = requests.post(
        TOKEN_URL,

        headers={
            "Authorization":
                _basic_auth_header(
                    config[
                        "app_key"
                    ],
                    config[
                        "app_secret"
                    ],
                ),

            "Content-Type":
                "application/x-www-form-urlencoded",

            "Accept":
                "application/json",
        },

        data={
            "grant_type":
                "refresh_token",

            "refresh_token":
                refresh_token,
        },

        timeout=
            30,
    )


    if not response.ok:

        raise RuntimeError(
            (
                "Schwab token refresh failed "
                f"with HTTP {response.status_code}: "
                f"{response.text[:1000]}"
            )
        )


    try:

        updated = (
            response.json()
        )


    except ValueError as error:

        raise RuntimeError(
            (
                "Schwab token refresh returned "
                "an invalid JSON response."
            )
        ) from error


    # Schwab may not always return a replacement refresh token.
    # Preserve the existing one if necessary.

    if not updated.get(
        "refresh_token"
    ):

        updated[
            "refresh_token"
        ] = refresh_token


    if not updated.get(
        "access_token"
    ):

        raise RuntimeError(
            (
                "Schwab refresh response did not contain "
                "an access token."
            )
        )


    return _store_oauth_credentials(
        account_id=
            account_id,

        credentials=
            updated,
    )


# ---------------------------------------------------------------------------
# Get Access Token
# ---------------------------------------------------------------------------

def get_schwab_access_token(
    account_id: str = DEFAULT_ACCOUNT_ID,
):
    """
    Returns a valid Schwab access token.

    Refreshes automatically when the current token is near expiration.
    """

    credentials = load_credentials(
        PROVIDER,
        account_id,
    )


    if not credentials:

        raise RuntimeError(
            (
                "Schwab is not authenticated. "
                "Run connect_schwab_account()."
            )
        )


    expires_at = float(
        credentials.get(
            "expires_at",
            0,
        )
        or 0
    )


    # Refresh one minute early.

    if (
        not expires_at
        or time.time()
        >= (
            expires_at
            - 60
        )
    ):

        credentials = (
            refresh_schwab_credentials(
                account_id
            )
        )


    access_token = (
        credentials.get(
            "access_token"
        )
    )


    if not access_token:

        raise RuntimeError(
            "Schwab access token is missing."
        )


    return access_token


# ---------------------------------------------------------------------------
# Authentication Status
# ---------------------------------------------------------------------------

def schwab_authenticated(
    account_id: str = DEFAULT_ACCOUNT_ID,
):
    """
    Checks whether OAuth credentials currently exist.

    Does not make a brokerage API request.
    """

    credentials = load_credentials(
        PROVIDER,
        account_id,
    )


    return bool(
        credentials
        and credentials.get(
            "access_token"
        )
    )


# ---------------------------------------------------------------------------
# Connect Schwab Account
# ---------------------------------------------------------------------------

def connect_schwab_account():
    """
    Starts Schwab OAuth.

    Schwab redirects to the configured HTTPS callback URL.

    Because E.V.I.E. currently uses https://127.0.0.1 without a local
    HTTPS listener, the browser may display a connection error after
    successful authorization.

    The user copies the complete final URL from the browser address bar
    and pastes it into the terminal.
    """

    config = (
        load_schwab_app_config()
    )


    authorization = (
        build_schwab_authorization_url()
    )


    print()
    print(
        "E.V.I.E. - Schwab Authorization"
    )

    print(
        "--------------------------------"
    )

    print()

    print(
        "Opening Charles Schwab..."
    )

    print()

    print(
        (
            "After signing in, authorize E.V.I.E. "
            "to access the Schwab account."
        )
    )

    print()

    print(
        (
            "The final https://127.0.0.1 page may fail "
            "to load. That is expected."
        )
    )

    print()

    print(
        (
            "When it redirects, copy the COMPLETE URL "
            "from the browser address bar."
        )
    )

    print()


    opened = webbrowser.open(
        authorization[
            "url"
        ]
    )


    if not opened:

        print(
            "Browser did not open automatically."
        )

        print()

        print(
            "Open this URL manually:"
        )

        print()

        print(
            authorization[
                "url"
            ]
        )

        print()


    redirected_url = input(
        (
            "Paste the complete Schwab callback URL here:\n"
            "> "
        )
    )


    parsed = (
        parse_schwab_redirect(
            redirected_url
        )
    )


    expected_state = (
        authorization[
            "state"
        ]
    )


    returned_state = (
        parsed.get(
            "state",
            "",
        )
    )


    if not returned_state:

        raise RuntimeError(
            (
                "Schwab callback did not contain the "
                "expected OAuth state."
            )
        )


    if (
        returned_state
        != expected_state
    ):

        raise RuntimeError(
            (
                "Schwab OAuth state mismatch. "
                "Authorization was cancelled for security."
            )
        )


    account_id = (
        config[
            "account_id"
        ]
    )


    exchange_schwab_code(
        code=
            parsed[
                "code"
            ],

        account_id=
            account_id,
    )


    account = IntegrationAccount(
        account_id=
            account_id,

        provider=
            PROVIDER,

        display_name=
            "Charles Schwab",

        email=
            "",

        connected=
            True,

        authenticated=
            True,

        scopes=[
            "accounts.read",
            "market.read",
        ],

        metadata={
            "auth_type":
                "oauth2_authorization_code",

            "read_only":
                True,

            "callback_url":
                config[
                    "callback_url"
                ],
        },
    )


    save_account(
        account
    )


    return account


# ---------------------------------------------------------------------------
# Disconnect Schwab
# ---------------------------------------------------------------------------

def disconnect_schwab_account(
    account_id: str = DEFAULT_ACCOUNT_ID,
):
    """
    Removes locally stored Schwab OAuth credentials and marks the
    integration disconnected.

    The developer Client ID / Client Secret configuration is preserved.
    """

    deleted = delete_credentials(
        PROVIDER,
        account_id,
    )


    account = get_account(
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
        "provider":
            PROVIDER,

        "account_id":
            account_id,

        "credentials_deleted":
            deleted,

        "connected":
            False,
    }


# ---------------------------------------------------------------------------
# Standalone Status Test
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    print(
        "E.V.I.E. Schwab Authentication"
    )

    print(
        "------------------------------"
    )

    print()


    try:

        config = (
            load_schwab_app_config()
        )


        print(
            "Configuration: OK"
        )

        print(
            "Client ID present:",
            bool(
                config[
                    "app_key"
                ]
            ),
        )

        print(
            "Client Secret present:",
            bool(
                config[
                    "app_secret"
                ]
            ),
        )

        print(
            "Callback URL:",
            config[
                "callback_url"
            ],
        )

        print(
            "Account ID:",
            config[
                "account_id"
            ],
        )

        print(
            "Authenticated:",
            schwab_authenticated(
                config[
                    "account_id"
                ]
            ),
        )


    except Exception as error:

        print(
            "Configuration: ERROR"
        )

        print(
            str(
                error
            )
        )