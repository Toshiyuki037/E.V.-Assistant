from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

class DeviceKind(str, Enum):
    WINDOWS_PC = "windows_pc"
    SERVER = "server"
    RASPBERRY_PI = "raspberry_pi"
    PHONE = "phone"
    TABLET = "tablet"
    WEARABLE = "wearable"
    CAMERA_NODE = "camera_node"
    EMBEDDED_NODE = "embedded_node"
    UNKNOWN = "unknown"

class DeviceRisk(str, Enum):
    READ = "read"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class DeviceCapability(str, Enum):
    SYSTEM_STATE = "system_state"
    WINDOWS = "windows"
    APPLICATIONS = "applications"
    PROCESSES = "processes"
    FILESYSTEM = "filesystem"
    CLIPBOARD = "clipboard"
    NOTIFICATIONS = "notifications"
    AUDIO = "audio"
    MICROPHONE = "microphone"
    CAMERA = "camera"
    DISPLAY = "display"
    ACCESSIBILITY = "accessibility"
    BROWSER_DOM = "browser_dom"
    VISION = "vision"
    SETTINGS = "settings"
    SERVICES = "services"
    NETWORK = "network"
    STORAGE = "storage"
    GPU = "gpu"
    SENSORS = "sensors"

@dataclass
class DeviceDescriptor:
    device_id: str
    name: str
    kind: DeviceKind
    platform: str = ""
    hostname: str = ""
    capabilities: set[DeviceCapability] = field(default_factory=set)
    trusted: bool = False
    local: bool = False
    enabled: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def supports(self, capability: DeviceCapability | str) -> bool:
        try:
            normalized = capability if isinstance(capability, DeviceCapability) else DeviceCapability(str(capability))
        except ValueError:
            return False
        return normalized in self.capabilities

    def to_dict(self) -> dict[str, Any]:
        return {
            "device_id": self.device_id,
            "name": self.name,
            "kind": self.kind.value,
            "platform": self.platform,
            "hostname": self.hostname,
            "capabilities": sorted(c.value for c in self.capabilities),
            "trusted": self.trusted,
            "local": self.local,
            "enabled": self.enabled,
            "metadata": dict(self.metadata),
        }
