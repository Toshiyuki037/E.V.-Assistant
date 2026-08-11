"""
E.V.I.E. - Charles Schwab API Client

Phase 9

This file deliberately contains all Schwab production base URLs in one
place so provider endpoint changes do not affect the rest of E.V.I.E.
"""

from __future__ import annotations

import requests

from .auth import (
    DEFAULT_ACCOUNT_ID,
    get_schwab_access_token,
)


TRADER_BASE_URL = (
    "https://api.schwabapi.com/trader/v1"
)


MARKET_BASE_URL = (
    "https://api.schwabapi.com/marketdata/v1"
)


# ---------------------------------------------------------------------------
# Generic Request
# ---------------------------------------------------------------------------

def schwab_request(
    account_id: str,
    method: str,
    path: str,
    *,
    api: str = "trader",
    params: dict | None = None,
    json_body=None,
):
    token = (
        get_schwab_access_token(
            account_id
        )
    )


    if api == "market":

        base_url = (
            MARKET_BASE_URL
        )


    elif api == "trader":

        base_url = (
            TRADER_BASE_URL
        )


    else:

        raise ValueError(
            (
                "Unknown Schwab API family: "
                f"{api}"
            )
        )


    url = (
        base_url
        + "/"
        + path.lstrip(
            "/"
        )
    )


    headers = {
        "Authorization":
            f"Bearer {token}",

        "Accept":
            "application/json",
    }


    if json_body is not None:

        headers[
            "Content-Type"
        ] = "application/json"


    response = requests.request(
        method=
            method.upper(),

        url=
            url,

        headers=
            headers,

        params=
            params,

        json=
            json_body,

        timeout=
            30,
    )


    if not response.ok:

        raise RuntimeError(
            (
                "Schwab API request failed "
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


    except ValueError:

        return {
            "status_code":
                response.status_code,

            "text":
                (
                    response.text
                    or ""
                ),
        }


# ---------------------------------------------------------------------------
# GET
# ---------------------------------------------------------------------------

def schwab_get(
    account_id: str = DEFAULT_ACCOUNT_ID,
    path: str = "",
    *,
    api: str = "trader",
    params: dict | None = None,
):
    return schwab_request(
        account_id=
            account_id,

        method=
            "GET",

        path=
            path,

        api=
            api,

        params=
            params,
    )