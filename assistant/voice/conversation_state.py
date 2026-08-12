
from __future__ import annotations

from collections import Counter, deque
from dataclasses import dataclass, field


@dataclass
class VoiceConversationState:
    """
    Phase-14 temporary conversational overlay.

    Long-term/project memory remains owned by the frozen memory phases.
    This object only manages live-session references/revisions/frequency.
    """
    max_history: int = 12
    history: deque[str] = field(default_factory=lambda: deque(maxlen=12))
    request_frequency: Counter = field(default_factory=Counter)
    pending_revision: str | None = None
    last_interrupted_prompt: str | None = None

    def remember_prompt(self, text: str):
        text = str(text or "").strip()
        if not text:
            return

        if self.history.maxlen != self.max_history:
            self.history = deque(self.history, maxlen=self.max_history)

        self.history.append(text)
        key = " ".join(text.lower().split())
        self.request_frequency[key] += 1

    def previous_prompt(self) -> str | None:
        if len(self.history) < 2:
            return None
        return list(self.history)[-2]

    def most_frequent_requests(self, limit: int = 5):
        return self.request_frequency.most_common(max(1, int(limit)))

    def safe_go_back_prompt(self) -> str:
        previous = self.previous_prompt()

        if previous:
            return (
                "Return to the conversational topic from before my most recent "
                f"request. The earlier user request was {previous!r}. "
                "Continue that topic conversationally. Do not repeat or "
                "re-execute any previous external action unless I explicitly "
                "request the action again."
            )

        return (
            "Return to the previous conversational topic if one exists. "
            "Do not repeat or re-execute any previous external action."
        )
