"""
E.V.I.E. - Process/Application Models

Phase 13C
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ProcessInfo:
    pid: int
    name: str
    executable: str = ""
    username: str = ""
    status: str = ""
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    memory_rss: int = 0
    create_time: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "pid": self.pid,
            "name": self.name,
            "executable": self.executable,
            "username": self.username,
            "status": self.status,
            "cpu_percent": self.cpu_percent,
            "memory_percent": self.memory_percent,
            "memory_rss": self.memory_rss,
            "create_time": self.create_time,
        }


@dataclass
class ApplicationLaunchResult:
    requested: str
    executable: str
    pid: int | None
    success: bool
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "requested": self.requested,
            "executable": self.executable,
            "pid": self.pid,
            "success": self.success,
            "message": self.message,
        }
