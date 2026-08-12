
"""
E.V.I.E. - Remote Device HTTP Transport

Phase 13K

Small JSON-over-HTTP transport.

The remote node contract is:

GET  /evie/v1/health
GET  /evie/v1/capabilities
POST /evie/v1/action

Requests are HMAC signed. The secret is supplied at runtime and is not stored
inside the remote device registry.
"""

from __future__ import annotations

import json
from urllib import request as urllib_request
from urllib.error import HTTPError, URLError

from .remote_auth import sign_payload


class RemoteTransportError(RuntimeError):
    pass


def _join_url(
    base_url: str,
    path: str,
) -> str:
    return (
        str(base_url).rstrip("/")
        + "/"
        + str(path).lstrip("/")
    )


def _read_json_response(response) -> dict:
    body = response.read()

    if not body:
        return {}

    return json.loads(
        body.decode("utf-8")
    )


def get_json(
    base_url: str,
    path: str,
    *,
    timeout: float = 5.0,
) -> dict:
    url = _join_url(
        base_url,
        path,
    )

    req = urllib_request.Request(
        url,
        method="GET",
        headers={
            "Accept": "application/json",
        },
    )

    try:
        with urllib_request.urlopen(
            req,
            timeout=float(timeout),
        ) as response:
            return _read_json_response(
                response
            )

    except (
        HTTPError,
        URLError,
        TimeoutError,
    ) as error:
        raise RemoteTransportError(
            f"Remote GET failed for {url}: {error}"
        ) from error


def post_signed_json(
    base_url: str,
    path: str,
    payload: dict,
    *,
    secret: str,
    timeout: float = 10.0,
) -> dict:
    url = _join_url(
        base_url,
        path,
    )

    encoded = json.dumps(
        payload,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")

    signature = sign_payload(
        payload,
        secret,
    )

    req = urllib_request.Request(
        url,
        data=encoded,
        method="POST",
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-EVIE-Signature": signature,
        },
    )

    try:
        with urllib_request.urlopen(
            req,
            timeout=float(timeout),
        ) as response:
            return _read_json_response(
                response
            )

    except (
        HTTPError,
        URLError,
        TimeoutError,
    ) as error:
        raise RemoteTransportError(
            f"Remote POST failed for {url}: {error}"
        ) from error
