"""
E.V.I.E. - Spotify API Client

Phase 9F
Last Edited: August 10, 2026

Purpose:
    Shared authenticated Spotify Web API request client.

Behavior:
    - attaches the current Spotify OAuth access token
    - supports GET / PUT / POST requests
    - preserves query parameters and JSON bodies
    - treats Spotify HTTP 204 responses as successful empty responses
    - safely handles successful responses with empty or non-JSON bodies
    - returns structured errors for failed Spotify requests

Important:
    Spotify playback-control endpoints commonly return HTTP 204
    No Content when the action succeeds.
"""

from __future__ import annotations

import requests

from .auth import (
    API_BASE_URL,
    get_spotify_access_token,
)


# ---------------------------------------------------------------------------
# Main Request
# ---------------------------------------------------------------------------

def spotify_request(
    account_id: str,
    method: str,
    path: str,
    params: dict | None = None,
    json_body: dict | None = None,
):
    """
    Executes one authenticated Spotify Web API request.

    Returns:
        dict/list
            Parsed Spotify JSON response.

        {}
            Successful request with no response body, including the
            common Spotify HTTP 204 No Content response.

    Raises:
        RuntimeError
            Spotify returned an unsuccessful HTTP status.
    """

    token = (
        get_spotify_access_token(
            account_id
        )
    )


    url = (
        API_BASE_URL
        + "/"
        + path.lstrip(
            "/"
        )
    )


    # -----------------------------------------------------------------------
    # Request Headers
    # -----------------------------------------------------------------------

    headers = {
        "Authorization":
            f"Bearer {token}",
    }


    # Content-Type is only necessary when a JSON body is actually sent.
    if json_body is not None:

        headers[
            "Content-Type"
        ] = "application/json"


    # -----------------------------------------------------------------------
    # Execute Request
    # -----------------------------------------------------------------------

    response = requests.request(
        method=
            str(
                method
            )
            .strip()
            .upper(),

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


    # -----------------------------------------------------------------------
    # Error Response
    # -----------------------------------------------------------------------

    if not response.ok:

        response_text = (
            response.text
            or ""
        ).strip()


        error_message = (
            "Spotify API request failed "
            f"with HTTP {response.status_code}"
        )


        if response_text:

            error_message += (
                ": "
                + response_text[
                    :1000
                ]
            )


        raise RuntimeError(
            error_message
        )


    # -----------------------------------------------------------------------
    # Spotify 204 No Content
    # -----------------------------------------------------------------------
    #
    # Playback-control endpoints such as:
    #
    #     pause
    #     resume
    #     next
    #     previous
    #     seek
    #     volume
    #     shuffle
    #     repeat
    #     queue
    #
    # commonly return HTTP 204 when successful.
    # -----------------------------------------------------------------------

    if (
        response.status_code
        == 204
    ):

        return {}


    # -----------------------------------------------------------------------
    # Empty Successful Body
    # -----------------------------------------------------------------------

    content = (
        response.content
        or b""
    )


    if not content.strip():

        return {}


    response_text = (
        response.text
        or ""
    ).strip()


    if not response_text:

        return {}


    # -----------------------------------------------------------------------
    # JSON Response
    # -----------------------------------------------------------------------

    try:

        return response.json()


    except (
        ValueError,
        requests.exceptions.JSONDecodeError,
    ):

        # -------------------------------------------------------------------
        # Successful Non-JSON Response
        # -------------------------------------------------------------------
        #
        # Never turn a successful Spotify command into a failure merely
        # because Spotify returned a body that was not JSON.
        # -------------------------------------------------------------------

        return {
            "status_code":
                response.status_code,

            "text":
                response_text,
        }


# ---------------------------------------------------------------------------
# GET
# ---------------------------------------------------------------------------

def spotify_get(
    account_id: str,
    path: str,
    params: dict | None = None,
):
    return spotify_request(
        account_id=
            account_id,

        method=
            "GET",

        path=
            path,

        params=
            params,
    )


# ---------------------------------------------------------------------------
# PUT
# ---------------------------------------------------------------------------

def spotify_put(
    account_id: str,
    path: str,
    params: dict | None = None,
    json_body: dict | None = None,
):
    return spotify_request(
        account_id=
            account_id,

        method=
            "PUT",

        path=
            path,

        params=
            params,

        json_body=
            json_body,
    )


# ---------------------------------------------------------------------------
# POST
# ---------------------------------------------------------------------------

def spotify_post(
    account_id: str,
    path: str,
    params: dict | None = None,
    json_body: dict | None = None,
):
    return spotify_request(
        account_id=
            account_id,

        method=
            "POST",

        path=
            path,

        params=
            params,

        json_body=
            json_body,
    )


# ---------------------------------------------------------------------------
# DELETE
# ---------------------------------------------------------------------------

def spotify_delete(
    account_id: str,
    path: str,
    params: dict | None = None,
    json_body: dict | None = None,
):
    """
    Included now so future Spotify capabilities do not require another
    API-client architecture change.
    """

    return spotify_request(
        account_id=
            account_id,

        method=
            "DELETE",

        path=
            path,

        params=
            params,

        json_body=
            json_body,
    )


# ---------------------------------------------------------------------------
# Standalone Test
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    print(
        "E.V.I.E. Spotify API Client"
    )

    print(
        "---------------------------"
    )


    print(
        "Spotify API base URL:",
        API_BASE_URL,
    )


    print(
        "Client loaded successfully."
    )