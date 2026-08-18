"""E.V.I.E. Phase 16 performance runtime."""
from .fast_path import RequestCostProfile, classify_request_cost, should_run_intelligent_memory
from .prewarm import PrewarmStatus, get_prewarm_status, start_background_prewarm, wait_for_prewarm
from .request_context import RequestPerformanceHints, current_performance_hints, performance_request_context

__all__ = [
    "PrewarmStatus", "RequestCostProfile", "RequestPerformanceHints",
    "classify_request_cost", "current_performance_hints", "get_prewarm_status",
    "performance_request_context", "should_run_intelligent_memory",
    "start_background_prewarm", "wait_for_prewarm",
]
