
"""
E.V.I.E. - Remote Device Message Authentication

Phase 13K

Uses HMAC-SHA256 for request integrity/authentication.

This is not the final Phase 17 credential architecture, but it prevents
unsigned remote control messages from being treated as valid device commands.
"""

from __future__ import annotations

import hashlib
import hmac
import json


def canonical_json_bytes(payload: dict) -> bytes:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def sign_payload(
    payload: dict,
    secret: str,
) -> str:
    key = str(secret).encode("utf-8")

    if not key:
        raise ValueError(
            "Remote device secret cannot be empty."
        )

    return hmac.new(
        key,
        canonical_json_bytes(payload),
        hashlib.sha256,
    ).hexdigest()


def verify_payload_signature(
    payload: dict,
    signature: str,
    secret: str,
) -> bool:
    expected = sign_payload(
        payload,
        secret,
    )

    return hmac.compare_digest(
        expected,
        str(signature or ""),
    )
