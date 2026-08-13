"""E.V.I.E. Phase 15B — Diagnostic report formatting."""
from __future__ import annotations
from .health import run_quick_health_check, overall_health_status

def format_health_report(results=None):
    results = results or run_quick_health_check()
    lines = ["E.V.I.E. SYSTEM HEALTH", ""]
    for result in results:
        lines.append(f"{result.component:<30} {result.status}")
        if result.detail:
            lines.append(f"  {result.detail}")
    lines.extend(["", f"Overall: {overall_health_status(results)}"])
    return "\n".join(lines)
