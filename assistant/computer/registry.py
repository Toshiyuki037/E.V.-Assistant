from __future__ import annotations
from threading import RLock
from .models import DeviceCapability, DeviceDescriptor

_DEVICES: dict[str, DeviceDescriptor] = {}
_LOCK = RLock()

def register_device(device: DeviceDescriptor, *, overwrite: bool = False) -> DeviceDescriptor:
    if not device.device_id.strip():
        raise ValueError("device_id cannot be empty")
    with _LOCK:
        if device.device_id in _DEVICES and not overwrite:
            raise ValueError(f"Device already registered: {device.device_id}")
        _DEVICES[device.device_id] = device
    return device

def get_device(device_id: str) -> DeviceDescriptor | None:
    with _LOCK:
        return _DEVICES.get(device_id)

def list_devices(*, capability: DeviceCapability | str | None = None, enabled_only: bool = True) -> list[DeviceDescriptor]:
    with _LOCK:
        devices = list(_DEVICES.values())
    if enabled_only:
        devices = [d for d in devices if d.enabled]
    if capability is not None:
        devices = [d for d in devices if d.supports(capability)]
    return sorted(devices, key=lambda d: (not d.local, not d.trusted, d.name.lower()))

def clear_device_registry():
    with _LOCK:
        _DEVICES.clear()
