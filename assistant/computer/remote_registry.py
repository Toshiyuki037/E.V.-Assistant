
"""
E.V.I.E. - Remote Device Registry

Phase 13K

Persistent JSON registry for trusted remote E.V.I.E. nodes.

Secrets are intentionally NOT stored in the registry.
"""

from __future__ import annotations

import json
from pathlib import Path

from .remote_models import RemoteDeviceDescriptor


DEFAULT_REMOTE_REGISTRY = (
    Path("runtime")
    / "computer"
    / "remote_devices.json"
)


def _registry_path(
    path: str | Path | None = None,
) -> Path:
    return Path(
        path
        or DEFAULT_REMOTE_REGISTRY
    ).resolve(
        strict=False
    )


def load_remote_devices(
    path: str | Path | None = None,
) -> list[RemoteDeviceDescriptor]:
    target = _registry_path(
        path
    )

    if not target.exists():
        return []

    payload = json.loads(
        target.read_text(
            encoding="utf-8"
        )
    )

    return [
        RemoteDeviceDescriptor.from_dict(
            item
        )
        for item in payload
    ]


def save_remote_devices(
    devices: list[RemoteDeviceDescriptor],
    path: str | Path | None = None,
):
    target = _registry_path(
        path
    )

    target.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    target.write_text(
        json.dumps(
            [
                device.to_dict()
                for device in devices
            ],
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def register_remote_device(
    device: RemoteDeviceDescriptor,
    *,
    path: str | Path | None = None,
) -> RemoteDeviceDescriptor:
    devices = load_remote_devices(
        path
    )

    existing_index = next(
        (
            index
            for index, item in enumerate(devices)
            if item.device_id == device.device_id
        ),
        None,
    )

    if existing_index is None:
        devices.append(
            device
        )
    else:
        devices[existing_index] = device

    save_remote_devices(
        devices,
        path,
    )

    return device


def get_remote_device(
    device_id: str,
    *,
    path: str | Path | None = None,
) -> RemoteDeviceDescriptor | None:
    wanted = str(device_id)

    for device in load_remote_devices(
        path
    ):
        if device.device_id == wanted:
            return device

    return None


def remove_remote_device(
    device_id: str,
    *,
    path: str | Path | None = None,
) -> bool:
    devices = load_remote_devices(
        path
    )

    remaining = [
        item
        for item in devices
        if item.device_id != str(device_id)
    ]

    changed = (
        len(remaining)
        != len(devices)
    )

    if changed:
        save_remote_devices(
            remaining,
            path,
        )

    return changed
