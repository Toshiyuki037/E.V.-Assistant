"""
E.V.I.E. - GitHub REST API Client

Phase 9

Read-only GitHub REST client.
"""

from __future__ import annotations

import requests

from .auth import (
    DEFAULT_ACCOUNT_ID,
    get_github_token,
)


API_BASE_URL = (
    "https://api.github.com"
)

API_VERSION = (
    "2026-03-10"
)


# ---------------------------------------------------------------------------
# Generic Request
# ---------------------------------------------------------------------------

def github_request(
    account_id: str = DEFAULT_ACCOUNT_ID,
    method: str = "GET",
    path: str = "",
    *,
    params: dict | None = None,
):
    token = (
        get_github_token(
            account_id
        )
    )

    url = (
        API_BASE_URL.rstrip("/")
        + "/"
        + path.lstrip("/")
    )

    response = requests.request(
        method=
            method.upper(),

        url=
            url,

        headers={
            "Accept":
                "application/vnd.github+json",

            "Authorization":
                f"Bearer {token}",

            "X-GitHub-Api-Version":
                API_VERSION,

            "User-Agent":
                "EVIE-Assistant",
        },

        params=
            params,

        timeout=
            30,
    )

    if not response.ok:

        raise RuntimeError(
            (
                "GitHub API request failed "
                f"with HTTP {response.status_code}: "
                f"{response.text[:1500]}"
            )
        )

    if (
        response.status_code
        == 204
    ):

        return {}

    if not (
        response.content
        or b""
    ).strip():

        return {}

    try:

        return response.json()

    except ValueError as error:

        raise RuntimeError(
            "GitHub API returned invalid JSON."
        ) from error


# ---------------------------------------------------------------------------
# GET
# ---------------------------------------------------------------------------

def github_get(
    account_id: str = DEFAULT_ACCOUNT_ID,
    path: str = "",
    *,
    params: dict | None = None,
):
    return github_request(
        account_id=
            account_id,

        method=
            "GET",

        path=
            path,

        params=
            params,
    )