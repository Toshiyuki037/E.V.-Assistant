
"""
E.V.I.E. - Remote Device Controller

Phase 13K
"""

from __future__ import annotations

from datetime import datetime, timezone
import uuid

from .remote_models import (
    RemoteActionRequest,
    RemoteActionResult,
    RemoteDeviceDescriptor,
)
from .remote_registry import (
    get_remote_device,
    load_remote_devices,
    register_remote_device,
    remove_remote_device,
)
from .remote_transport import (
    get_json,
    post_signed_json,
)


def _now() -> str:
    return datetime.now(
        timezone.utc
    ).isoformat()


def register_local_remote_device(
    *,
    device_id: str,
    name: str,
    kind: str,
    base_url: str,
    capabilities: list[str] | None = None,
    trusted: bool = False,
    enabled: bool = True,
    registry_path=None,
):
    device = RemoteDeviceDescriptor(
        device_id=str(device_id),
        name=str(name),
        kind=str(kind),
        base_url=str(base_url),
        capabilities=[
            str(item)
            for item in (
                capabilities
                or []
            )
        ],
        trusted=bool(trusted),
        enabled=bool(enabled),
    )

    return register_remote_device(
        device,
        path=registry_path,
    ).to_dict()


def list_local_remote_devices(
    *,
    registry_path=None,
):
    return [
        device.to_dict()
        for device in load_remote_devices(
            registry_path
        )
    ]


def remove_local_remote_device(
    device_id: str,
    *,
    registry_path=None,
):
    return remove_remote_device(
        device_id,
        path=registry_path,
    )


def probe_remote_device(
    device_id: str,
    *,
    registry_path=None,
    timeout: float = 5.0,
):
    device = get_remote_device(
        device_id,
        path=registry_path,
    )

    if device is None:
        raise LookupError(
            f"Unknown remote device: {device_id}"
        )

    if not device.enabled:
        raise PermissionError(
            f"Remote device is disabled: {device_id}"
        )

    health = get_json(
        device.base_url,
        "/evie/v1/health",
        timeout=timeout,
    )

    capabilities = get_json(
        device.base_url,
        "/evie/v1/capabilities",
        timeout=timeout,
    )

    device.last_seen_at = _now()

    advertised = [
        str(item)
        for item in capabilities.get(
            "capabilities",
            [],
        )
    ]

    if advertised:
        device.capabilities = advertised

    register_remote_device(
        device,
        path=registry_path,
    )

    return {
        "device": device.to_dict(),
        "health": health,
        "capabilities": capabilities,
    }


def execute_remote_device_action(
    device_id: str,
    action: str,
    *,
    target: str = "",
    arguments: dict | None = None,
    approved: bool = False,
    secret: str,
    registry_path=None,
    timeout: float = 10.0,
):
    device = get_remote_device(
        device_id,
        path=registry_path,
    )

    if device is None:
        raise LookupError(
            f"Unknown remote device: {device_id}"
        )

    if not device.enabled:
        raise PermissionError(
            f"Remote device is disabled: {device_id}"
        )

    if not device.trusted:
        raise PermissionError(
            (
                "Remote device is not trusted for control: "
                f"{device_id}"
            )
        )

    action_name = str(action)

    if (
        device.capabilities
        and action_name not in device.capabilities
    ):
        raise PermissionError(
            (
                f"Remote device {device_id} does not advertise "
                f"capability {action_name!r}."
            )
        )

    envelope = RemoteActionRequest(
        request_id=(
            "remote_"
            + uuid.uuid4().hex
        ),
        device_id=device.device_id,
        action=action_name,
        target=str(target or ""),
        arguments=dict(
            arguments
            or {}
        ),
        approved=bool(approved),
        issued_at=_now(),
    )

    response = post_signed_json(
        device.base_url,
        "/evie/v1/action",
        envelope.to_dict(),
        secret=secret,
        timeout=timeout,
    )

    result = RemoteActionResult(
        request_id=envelope.request_id,
        device_id=device.device_id,
        success=bool(
            response.get(
                "success",
                False,
            )
        ),
        result=response.get(
            "result"
        ),
        verified=bool(
            response.get(
                "verified",
                False,
            )
        ),
        error=str(
            response.get(
                "error",
                "",
            )
        ),
        method="remote",
    )

    return result.to_dict()
