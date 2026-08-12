
"""
E.V.I.E. - Remote Device Interface Models

Phase 13K
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class RemoteDeviceDescriptor:
    device_id: str
    name: str
    kind: str
    base_url: str
    capabilities: list[str] = field(default_factory=list)
    trusted: bool = False
    enabled: bool = True
    last_seen_at: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "device_id": self.device_id,
            "name": self.name,
            "kind": self.kind,
            "base_url": self.base_url,
            "capabilities": list(self.capabilities),
            "trusted": self.trusted,
            "enabled": self.enabled,
            "last_seen_at": self.last_seen_at,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]):
        return cls(
            device_id=str(payload["device_id"]),
            name=str(payload.get("name", payload["device_id"])),
            kind=str(payload.get("kind", "remote_node")),
            base_url=str(payload["base_url"]),
            capabilities=[
                str(item)
                for item in payload.get("capabilities", [])
            ],
            trusted=bool(payload.get("trusted", False)),
            enabled=bool(payload.get("enabled", True)),
            last_seen_at=str(payload.get("last_seen_at", "")),
            metadata=dict(payload.get("metadata", {})),
        )


@dataclass
class RemoteActionRequest:
    request_id: str
    device_id: str
    action: str
    target: str = ""
    arguments: dict[str, Any] = field(default_factory=dict)
    approved: bool = False
    issued_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "device_id": self.device_id,
            "action": self.action,
            "target": self.target,
            "arguments": dict(self.arguments),
            "approved": self.approved,
            "issued_at": self.issued_at,
        }


@dataclass
class RemoteActionResult:
    request_id: str
    device_id: str
    success: bool
    result: Any = None
    verified: bool = False
    error: str = ""
    method: str = "remote"

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "device_id": self.device_id,
            "success": self.success,
            "result": self.result,
            "verified": self.verified,
            "error": self.error,
            "method": self.method,
        }
