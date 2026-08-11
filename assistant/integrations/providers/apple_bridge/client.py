"""
E.V.I.E. - Apple Bridge Client

Created: August 10, 2026
Author: Max Maehara

Purpose:
    Provides the Windows-side client for E.V.I.E.'s trusted Apple
    bridge.

Architecture:
    The actual Apple APIs execute on a trusted Mac.

    E.V.I.E. communicates with that Mac through a small authenticated
    HTTP bridge.

Security:
    - bridge token is stored through E.V.I.E.'s secure credential store
    - bridge token is never stored in account metadata
    - bridge token is never printed
    - requests use explicit timeouts
"""

from __future__ import annotations

import json

from pathlib import Path

import requests

from assistant.integrations.credentials import (
    load_credentials,
    store_credentials,
)


PROVIDER = "apple_bridge"


PROJECT_ROOT = (
    Path(
        __file__
    )
    .resolve()
    .parents[4]
)


APPLE_RUNTIME_DIRECTORY = (
    PROJECT_ROOT
    / "runtime"
    / "integrations"
    / "apple_bridge"
)


CONFIG_FILE = (
    APPLE_RUNTIME_DIRECTORY
    / "config.json"
)


# ---------------------------------------------------------------------------
# Runtime
# ---------------------------------------------------------------------------

def ensure_apple_runtime():
    APPLE_RUNTIME_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

def config_available():
    return (
        CONFIG_FILE.exists()
        and CONFIG_FILE.is_file()
    )


def load_apple_bridge_config():
    if not config_available():

        raise FileNotFoundError(
            (
                "Apple bridge configuration was not found at: "
                f"{CONFIG_FILE}"
            )
        )


    payload = json.loads(
        CONFIG_FILE.read_text(
            encoding="utf-8"
        )
    )


    base_url = (
        str(
            payload.get(
                "base_url",
                ""
            )
        )
        .strip()
        .rstrip("/")
    )


    account_id = (
        str(
            payload.get(
                "account_id",
                "apple-local",
            )
        )
        .strip()
    )


    if not base_url:

        raise ValueError(
            "Apple bridge base_url is missing."
        )


    if not account_id:

        raise ValueError(
            "Apple bridge account_id is missing."
        )


    return {
        "base_url":
            base_url,

        "account_id":
            account_id,
    }


# ---------------------------------------------------------------------------
# Bridge Credential
# ---------------------------------------------------------------------------

def store_bridge_token(
    account_id: str,
    token: str,
):
    token = (
        str(
            token
        )
        .strip()
    )


    if not token:

        raise ValueError(
            "Apple bridge token cannot be empty."
        )


    return store_credentials(
        provider=
            PROVIDER,

        account_id=
            account_id,

        credentials={
            "bridge_token":
                token,
        },
    )


def load_bridge_token(
    account_id: str,
):
    credentials = load_credentials(
        PROVIDER,
        account_id,
    )


    if not credentials:

        return None


    token = credentials.get(
        "bridge_token"
    )


    if not token:

        return None


    return str(
        token
    )


# ---------------------------------------------------------------------------
# HTTP Request
# ---------------------------------------------------------------------------

def apple_bridge_request(
    method: str,
    path: str,
    params: dict | None = None,
    json_body: dict | None = None,
):
    config = load_apple_bridge_config()


    account_id = (
        config[
            "account_id"
        ]
    )


    token = load_bridge_token(
        account_id
    )


    if not token:

        raise RuntimeError(
            (
                "Apple bridge credential is not configured "
                f"for {account_id}."
            )
        )


    url = (
        config[
            "base_url"
        ]
        + "/"
        + path.lstrip("/")
    )


    try:

        response = requests.request(
            method=
                method.upper(),

            url=
                url,

            params=
                params,

            json=
                json_body,

            headers={
                "Authorization":
                    f"Bearer {token}",

                "Accept":
                    "application/json",
            },

            timeout=
                10,
        )


    except requests.RequestException as error:

        raise RuntimeError(
            (
                "Apple bridge could not be reached: "
                f"{error}"
            )
        ) from error


    if not response.ok:

        raise RuntimeError(
            (
                "Apple bridge request failed "
                f"with HTTP {response.status_code}: "
                f"{response.text[:500]}"
            )
        )


    if not response.content:

        return {}


    try:

        return response.json()


    except ValueError as error:

        raise RuntimeError(
            "Apple bridge returned invalid JSON."
        ) from error


# ---------------------------------------------------------------------------
# GET
# ---------------------------------------------------------------------------

def apple_bridge_get(
    path: str,
    params: dict | None = None,
):
    return apple_bridge_request(
        method=
            "GET",

        path=
            path,

        params=
            params,
    )


# ---------------------------------------------------------------------------
# POST
# ---------------------------------------------------------------------------

def apple_bridge_post(
    path: str,
    json_body: dict | None = None,
):
    return apple_bridge_request(
        method=
            "POST",

        path=
            path,

        json_body=
            json_body,
    )


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

def apple_bridge_health():
    return apple_bridge_get(
        "/health"
    )