"""
E.V.I.E. - Notion API Client

Phase 9

Read-only Notion API client.
"""

from __future__ import annotations

import requests

from .auth import (
    DEFAULT_ACCOUNT_ID,
    get_notion_token,
)


API_BASE_URL = (
    "https://api.notion.com/v1"
)

NOTION_VERSION = (
    "2026-03-11"
)


def notion_request(
    account_id: str = DEFAULT_ACCOUNT_ID,
    method: str = "GET",
    path: str = "",
    *,
    params: dict | None = None,
    json_body: dict | None = None,
):

    token = (
        get_notion_token(
            account_id
        )
    )


    url = (
        API_BASE_URL.rstrip("/")
        + "/"
        + path.lstrip("/")
    )


    headers = {
        "Authorization":
            f"Bearer {token}",

        "Accept":
            "application/json",

        "Notion-Version":
            NOTION_VERSION,
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
                "Notion API request failed "
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
            "Notion API returned invalid JSON."
        ) from error


def notion_get(
    account_id: str = DEFAULT_ACCOUNT_ID,
    path: str = "",
    *,
    params: dict | None = None,
):

    return notion_request(
        account_id=
            account_id,

        method=
            "GET",

        path=
            path,

        params=
            params,
    )


def notion_post(
    account_id: str = DEFAULT_ACCOUNT_ID,
    path: str = "",
    *,
    json_body: dict | None = None,
):

    return notion_request(
        account_id=
            account_id,

        method=
            "POST",

        path=
            path,

        json_body=
            json_body,
    )