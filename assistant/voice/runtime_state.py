
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from time import monotonic


class VoiceRuntimeMode(str, Enum):
    ACTIVE = "active"
    STANDBY = "standby"
    PAUSED = "paused"
    SLEEPING = "sleeping"


@dataclass
class VoiceRuntimeState:
    mode: VoiceRuntimeMode = VoiceRuntimeMode.ACTIVE
    last_activity_at: float = 0.0

    def __post_init__(self):
        if not self.last_activity_at:
            self.last_activity_at = monotonic()

    def touch(self):
        self.last_activity_at = monotonic()

    def set_mode(self, mode: VoiceRuntimeMode):
        self.mode = mode
        self.touch()

    def idle_seconds(self) -> float:
        return max(0.0, monotonic() - self.last_activity_at)
