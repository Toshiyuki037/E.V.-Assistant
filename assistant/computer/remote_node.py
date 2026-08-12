
"""
E.V.I.E. - Minimal Remote Node Contract

Phase 13K

This is transport-agnostic node logic. A later server/service wrapper can
expose these handlers through FastAPI/Flask/etc.

The handler delegates execution to the existing Phase 13J unified local
computer controller.
"""

from __future__ import annotations

from .control_controller import control_local_computer
from .remote_auth import verify_payload_signature


def build_node_health(
    *,
    device_id: str,
    name: str,
    kind: str,
):
    return {
        "ok": True,
        "device_id": str(device_id),
        "name": str(name),
        "kind": str(kind),
        "protocol": "evie-device-v1",
    }


def build_node_capabilities(
    capabilities: list[str],
):
    return {
        "capabilities": [
            str(item)
            for item in capabilities
        ]
    }


def handle_signed_remote_action(
    payload: dict,
    *,
    signature: str,
    secret: str,
    local_device_id: str,
):
    if not verify_payload_signature(
        payload,
        signature,
        secret,
    ):
        raise PermissionError(
            "Remote action signature verification failed."
        )

    if (
        str(payload.get("device_id", ""))
        != str(local_device_id)
    ):
        raise PermissionError(
            "Remote action was addressed to a different device."
        )

    action = str(
        payload.get(
            "action",
            "",
        )
    ).strip()

    if not action:
        raise ValueError(
            "Remote action is missing an action name."
        )

    result = control_local_computer(
        action,
        target=str(
            payload.get(
                "target",
                "",
            )
        ),
        arguments=dict(
            payload.get(
                "arguments",
                {},
            )
        ),
        approved=bool(
            payload.get(
                "approved",
                False,
            )
        ),
    )

    return {
        "success": bool(
            result.get(
                "success",
                False,
            )
        ),
        "verified": bool(
            result.get(
                "verified",
                False,
            )
        ),
        "result": result,
        "error": "",
    }
