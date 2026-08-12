from __future__ import annotations
import platform
import socket
from .models import DeviceCapability, DeviceDescriptor, DeviceKind

LOCAL_WINDOWS_DEVICE_ID = "local-windows"

def build_local_windows_device() -> DeviceDescriptor:
    hostname = socket.gethostname()
    return DeviceDescriptor(
        device_id=LOCAL_WINDOWS_DEVICE_ID,
        name=hostname or "Local Windows PC",
        kind=DeviceKind.WINDOWS_PC,
        platform=platform.platform(),
        hostname=hostname,
        capabilities={
            DeviceCapability.SYSTEM_STATE, DeviceCapability.WINDOWS,
            DeviceCapability.APPLICATIONS, DeviceCapability.PROCESSES,
            DeviceCapability.FILESYSTEM, DeviceCapability.CLIPBOARD,
            DeviceCapability.NOTIFICATIONS, DeviceCapability.AUDIO,
            DeviceCapability.MICROPHONE, DeviceCapability.CAMERA,
            DeviceCapability.DISPLAY, DeviceCapability.ACCESSIBILITY,
            DeviceCapability.VISION, DeviceCapability.SETTINGS,
            DeviceCapability.NETWORK, DeviceCapability.STORAGE,
        },
        trusted=True,
        local=True,
        enabled=True,
        metadata={"phase": "13A", "control_backend": "pending"},
    )
