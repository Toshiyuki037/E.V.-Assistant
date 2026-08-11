"""
E.V.I.E. - Spotify Authentication

Created: August 10, 2026
Author: Max Maehara

Purpose:
    Provides Spotify OAuth authentication for Phase 9F.

Architecture:
    - Authorization Code with PKCE
    - no client secret required
    - access / refresh tokens stored through E.V.I.E.'s secure
      credential store
    - account metadata stored separately
"""

from __future__ import annotations

import base64
import hashlib
import json
import secrets
import threading
import time
import webbrowser

from http.server import (
    BaseHTTPRequestHandler,
    HTTPServer,
)

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


PROVIDER = "spotify"


AUTHORIZE_URL = (
    "https://accounts.spotify.com/authorize"
)

TOKEN_URL = (
    "https://accounts.spotify.com/api/token"
)

API_BASE_URL = (
    "https://api.spotify.com/v1"
)


SPOTIFY_SCOPES = [
    "user-read-private",
    "user-read-email",
    "user-read-playback-state",
    "user-read-currently-playing",
    "user-read-recently-played",
    "user-modify-playback-state",
]


PROJECT_ROOT = (
    Path(
        __file__
    )
    .resolve()
    .parents[4]
)


SPOTIFY_RUNTIME_DIRECTORY = (
    PROJECT_ROOT
    / "runtime"
    / "integrations"
    / "spotify"
)


CONFIG_FILE = (
    SPOTIFY_RUNTIME_DIRECTORY
    / "config.json"
)


def ensure_spotify_runtime():
    SPOTIFY_RUNTIME_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )


def config_available():
    return (
        CONFIG_FILE.exists()
        and CONFIG_FILE.is_file()
    )


def load_spotify_config():
    if not config_available():

        raise FileNotFoundError(
            (
                "Spotify config was not found at: "
                f"{CONFIG_FILE}"
            )
        )


    payload = json.loads(
        CONFIG_FILE.read_text(
            encoding="utf-8"
        )
    )


    client_id = (
        str(
            payload.get(
                "client_id",
                "",
            )
        )
        .strip()
    )


    redirect_uri = (
        str(
            payload.get(
                "redirect_uri",
                "",
            )
        )
        .strip()
    )


    if not client_id:

        raise ValueError(
            "Spotify client_id is missing."
        )


    if not redirect_uri:

        raise ValueError(
            "Spotify redirect_uri is missing."
        )


    return {
        "client_id":
            client_id,

        "redirect_uri":
            redirect_uri,
    }


def _base64url(
    value: bytes,
):
    return (
        base64.urlsafe_b64encode(
            value
        )
        .decode(
            "ascii"
        )
        .rstrip(
            "="
        )
    )


def generate_code_verifier():
    return secrets.token_urlsafe(
        64
    )


def generate_code_challenge(
    verifier: str,
):
    digest = hashlib.sha256(
        verifier.encode(
            "ascii"
        )
    ).digest()


    return _base64url(
        digest
    )


def store_spotify_credentials(
    account_id: str,
    credentials: dict,
):
    return store_credentials(
        provider=
            PROVIDER,

        account_id=
            account_id,

        credentials=
            credentials,
    )


def load_spotify_credentials(
    account_id: str,
):
    return load_credentials(
        PROVIDER,
        account_id,
    )


def refresh_spotify_credentials(
    account_id: str,
    credentials: dict,
):
    config = load_spotify_config()


    refresh_token = (
        credentials.get(
            "refresh_token"
        )
    )


    if not refresh_token:

        return None


    response = requests.post(
        TOKEN_URL,

        data={
            "grant_type":
                "refresh_token",

            "refresh_token":
                refresh_token,

            "client_id":
                config[
                    "client_id"
                ],
        },

        timeout=30,
    )


    response.raise_for_status()


    updated = response.json()


    if (
        "refresh_token"
        not in updated
    ):

        updated[
            "refresh_token"
        ] = refresh_token


    updated[
        "expires_at"
    ] = (
        time.time()
        + int(
            updated.get(
                "expires_in",
                3600,
            )
        )
    )


    store_spotify_credentials(
        account_id,
        updated,
    )


    return updated


def get_spotify_access_token(
    account_id: str,
):
    credentials = (
        load_spotify_credentials(
            account_id
        )
    )


    if not credentials:

        raise RuntimeError(
            (
                "Spotify credentials were not found for "
                f"{account_id}."
            )
        )


    expires_at = float(
        credentials.get(
            "expires_at",
            0,
        )
        or 0
    )


    if (
        time.time()
        >= (
            expires_at
            - 60
        )
    ):

        credentials = (
            refresh_spotify_credentials(
                account_id,
                credentials,
            )
        )


    if not credentials:

        raise RuntimeError(
            "Spotify credentials could not be refreshed."
        )


    access_token = (
        credentials.get(
            "access_token"
        )
    )


    if not access_token:

        raise RuntimeError(
            "Spotify access token is missing."
        )


    return access_token


class _SpotifyCallbackHandler(
    BaseHTTPRequestHandler
):
    result = None


    def do_GET(
        self,
    ):
        parsed = urlparse(
            self.path
        )


        query = parse_qs(
            parsed.query
        )


        self.__class__.result = query


        self.send_response(
            200
        )

        self.send_header(
            "Content-Type",
            "text/plain; charset=utf-8",
        )

        self.end_headers()


        self.wfile.write(
            (
                b"E.V.I.E. Spotify authorization received. "
                b"You can close this window."
            )
        )


    def log_message(
        self,
        format,
        *args,
    ):
        return


def wait_for_callback(
    redirect_uri: str,
    timeout_seconds: int = 180,
):
    parsed = urlparse(
        redirect_uri
    )


    host = (
        parsed.hostname
        or "127.0.0.1"
    )


    port = (
        parsed.port
        or 8888
    )


    _SpotifyCallbackHandler.result = None


    server = HTTPServer(
        (
            host,
            port,
        ),
        _SpotifyCallbackHandler,
    )


    thread = threading.Thread(
        target=
            server.handle_request,

        daemon=
            True,
    )


    thread.start()


    thread.join(
        timeout=
            timeout_seconds
    )


    server.server_close()


    result = (
        _SpotifyCallbackHandler.result
    )


    if result is None:

        raise TimeoutError(
            "Spotify authorization timed out."
        )


    return result


def get_spotify_profile(
    access_token: str,
):
    response = requests.get(
        (
            f"{API_BASE_URL}"
            "/me"
        ),

        headers={
            "Authorization":
                f"Bearer {access_token}",
        },

        timeout=30,
    )


    response.raise_for_status()


    return response.json()


def connect_spotify_account():
    ensure_spotify_runtime()


    config = load_spotify_config()


    verifier = (
        generate_code_verifier()
    )


    challenge = (
        generate_code_challenge(
            verifier
        )
    )


    state = secrets.token_urlsafe(
        32
    )


    authorization_url = (
        AUTHORIZE_URL
        + "?"
        + urlencode(
            {
                "client_id":
                    config[
                        "client_id"
                    ],

                "response_type":
                    "code",

                "redirect_uri":
                    config[
                        "redirect_uri"
                    ],

                "scope":
                    " ".join(
                        SPOTIFY_SCOPES
                    ),

                "state":
                    state,

                "code_challenge_method":
                    "S256",

                "code_challenge":
                    challenge,

                "show_dialog":
                    "true",
            }
        )
    )


    print(
        (
            "Please authorize Spotify in your browser."
        )
    )


    webbrowser.open(
        authorization_url
    )


    callback = wait_for_callback(
        config[
            "redirect_uri"
        ]
    )


    callback_state = (
        callback.get(
            "state",
            [""],
        )[
            0
        ]
    )


    if callback_state != state:

        raise RuntimeError(
            "Spotify OAuth state mismatch."
        )


    if "error" in callback:

        raise RuntimeError(
            (
                "Spotify authorization failed: "
                f"{callback['error'][0]}"
            )
        )


    code = (
        callback.get(
            "code",
            [""],
        )[
            0
        ]
    )


    if not code:

        raise RuntimeError(
            "Spotify authorization code was not returned."
        )


    token_response = requests.post(
        TOKEN_URL,

        data={
            "client_id":
                config[
                    "client_id"
                ],

            "grant_type":
                "authorization_code",

            "code":
                code,

            "redirect_uri":
                config[
                    "redirect_uri"
                ],

            "code_verifier":
                verifier,
        },

        timeout=30,
    )


    token_response.raise_for_status()


    credentials = (
        token_response.json()
    )


    credentials[
        "expires_at"
    ] = (
        time.time()
        + int(
            credentials.get(
                "expires_in",
                3600,
            )
        )
    )


    profile = get_spotify_profile(
        credentials[
            "access_token"
        ]
    )


    spotify_id = (
        str(
            profile.get(
                "id",
                "",
            )
        )
        .strip()
    )


    if not spotify_id:

        raise RuntimeError(
            "Spotify profile ID was not returned."
        )


    account_id = spotify_id


    store_spotify_credentials(
        account_id,
        credentials,
    )


    display_name = (
        str(
            profile.get(
                "display_name",
                "",
            )
        )
        .strip()
        or spotify_id
    )


    email = (
        str(
            profile.get(
                "email",
                "",
            )
        )
        .strip()
    )


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
            SPOTIFY_SCOPES
        ),

        metadata={
            "spotify_id":
                spotify_id,

            "country":
                profile.get(
                    "country",
                    "",
                ),

            "product":
                profile.get(
                    "product",
                    "",
                ),
        },
    )


    save_account(
        account
    )


    return account


def disconnect_spotify_account(
    account_id: str,
):
    account = get_account(
        PROVIDER,
        account_id,
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


if __name__ == "__main__":

    print(
        "E.V.I.E. Spotify Authentication"
    )

    print(
        "-------------------------------"
    )


    print(
        "Config:",
        CONFIG_FILE,
    )


    print(
        "Available:",
        config_available(),
    )