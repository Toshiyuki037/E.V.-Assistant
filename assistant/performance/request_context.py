"""Per-request performance hints using ContextVars."""
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass

@dataclass(frozen=True)
class RequestPerformanceHints:
    allow_long_term_memory: bool = True
    allow_project_knowledge: bool = True
    reason: str = "default"

_HINTS = ContextVar("evie_performance_hints", default=RequestPerformanceHints())

def current_performance_hints():
    return _HINTS.get()

@contextmanager
def performance_request_context(*, allow_long_term_memory=True, allow_project_knowledge=True, reason="request"):
    token = _HINTS.set(RequestPerformanceHints(
        allow_long_term_memory=bool(allow_long_term_memory),
        allow_project_knowledge=bool(allow_project_knowledge),
        reason=str(reason or "request"),
    ))
    try:
        yield _HINTS.get()
    finally:
        _HINTS.reset(token)
