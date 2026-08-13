"""
E.V.I.E. - Phase 15 System Integration

Live runtime entry point for:
    - self-awareness
    - quick health
    - diagnostic snapshots
    - deep diagnostics
    - performance health
    - maintenance
    - certification
    - bounded self-repair preparation

Voice-routing goals:
    - filler words do not prevent deterministic command routing
    - common STT slips can be normalized conservatively
    - health answers explicitly say what is healthy and what is not
"""

from __future__ import annotations

import re

from .certification import (
    format_certification_report,
)

from .deep_diagnostics import (
    format_deep_diagnostic_report,
)

from .diagnostic_state import (
    format_diagnostic_snapshot,
)

from .health import (
    run_quick_health_check,
    overall_health_status,
)

from .maintenance import (
    list_maintenance_actions,
    run_maintenance_action,
)

from .performance import (
    format_performance_report,
)

from .self_awareness import (
    get_capability_status,
    get_self_awareness,
)

from .self_repair_bridge import (
    build_repair_request,
    render_repair_prompt,
)


# ---------------------------------------------------------------------------
# Voice / Natural-Language Normalization
# ---------------------------------------------------------------------------

_FILLER_PREFIXES = (
    "um",
    "uh",
    "erm",
    "hmm",
    "well",
    "okay",
    "ok",
    "so",
    "like",
    "hey",
    "evie",
    "eve",
    "e.v.i.e",
)

_FILLER_SUFFIXES = (
    "please",
    "for me",
)

# Conservative STT aliases only for highly recognizable system commands.
_STT_COMMAND_ALIASES = {
    "what vision are you":
        "what version are you",

    "what vision is evie":
        "what version is evie",

    "what vision is eve":
        "what version is evie",

    "are you helpy":
        "are you healthy",
}


def _strip_edge_fillers(
    text: str,
):
    """
    Remove conversational filler only from the beginning/end of a command.

    Filler words inside the semantic content are preserved so routing does
    not accidentally rewrite ordinary conversation.
    """

    value = (
        str(
            text
            or ""
        )
        .strip()
    )

    changed = True

    while (
        value
        and changed
    ):

        changed = False

        lower = (
            value.lower()
        )

        for filler in _FILLER_PREFIXES:

            match = re.match(
                rf"^\s*{re.escape(filler)}(?:\s*[,.:;!?-]\s*|\s+)",
                lower,
            )

            if match:

                value = (
                    value[
                        match.end():
                    ]
                    .strip()
                )

                changed = True

                break


    changed = True

    while (
        value
        and changed
    ):

        changed = False

        lower = (
            value.lower()
        )

        for filler in _FILLER_SUFFIXES:

            match = re.search(
                rf"(?:\s*[,.:;!?-]\s*|\s+){re.escape(filler)}\s*$",
                lower,
            )

            if match:

                value = (
                    value[
                        :match.start()
                    ]
                    .strip()
                )

                changed = True

                break


    return value


def _normalize(
    text: str,
) -> str:

    value = (
        " ".join(
            str(
                text
                or ""
            )
            .strip()
            .lower()
            .split()
        )
        .rstrip(
            ".!?"
        )
    )

    value = (
        _strip_edge_fillers(
            value
        )
    )

    value = (
        " ".join(
            value.split()
        )
        .strip()
        .rstrip(
            ".!?"
        )
    )

    value = (
        _STT_COMMAND_ALIASES.get(
            value,
            value,
        )
    )

    return value


# ---------------------------------------------------------------------------
# Standard Results
# ---------------------------------------------------------------------------

def _result(
    response: str,
    *,
    follow_up: str = "",
    metadata: dict | None = None,
):
    return {
        "handled":
            True,

        "response":
            response,

        "follow_up":
            follow_up,

        "metadata":
            dict(
                metadata
                or {}
            ),
    }


def _not_handled():
    return {
        "handled":
            False,

        "response":
            "",

        "follow_up":
            "",

        "metadata":
            {},
    }


# ---------------------------------------------------------------------------
# Health Formatting
# ---------------------------------------------------------------------------

def _format_quick_health():
    results = (
        run_quick_health_check()
    )

    overall = (
        overall_health_status(
            results
        )
    )

    healthy = [
        result
        for result
        in results
        if result.status
        == "HEALTHY"
    ]

    unhealthy = [
        result
        for result
        in results
        if result.status
        != "HEALTHY"
    ]

    lines = [
        f"Overall system health: {overall}.",
        "",
    ]


    if healthy:

        lines.append(
            "Healthy systems:"
        )

        for item in healthy:

            detail = (
                item.detail.strip()
                if item.detail
                else "Healthy."
            )

            lines.append(
                (
                    f"- {item.component}: "
                    f"{detail}"
                )
            )


    if unhealthy:

        lines.extend(
            [
                "",
                "Systems needing attention:",
            ]
        )

        for item in unhealthy:

            lines.append(
                (
                    f"- {item.component}: "
                    f"{item.status}. "
                    f"{item.detail}"
                )
            )

    else:

        lines.extend(
            [
                "",
                "No quick-health component currently needs attention.",
            ]
        )


    return "\n".join(
        lines
    )


def _format_capabilities():
    result = (
        get_self_awareness(
            "capabilities"
        )
    )

    capabilities = (
        result.data.get(
            "capabilities",
            {}
        )
    )

    lines = [
        "My currently supported core capabilities include:"
    ]

    for name in sorted(
        capabilities
    ):

        description = (
            capabilities[
                name
            ]
            .get(
                "description",
                "",
            )
        )

        lines.append(
            f"- {name}: {description}"
        )

    return "\n".join(
        lines
    )


def _format_integrations():
    result = (
        get_self_awareness(
            "integrations"
        )
    )

    integrations = (
        result.data.get(
            "integrations",
            {}
        )
    )

    lines = [
        "Configured integration families:"
    ]

    for provider in sorted(
        integrations
    ):

        lines.append(
            (
                f"- {provider}: "
                + ", ".join(
                    integrations[
                        provider
                    ]
                )
            )
        )

    return "\n".join(
        lines
    )


# ---------------------------------------------------------------------------
# Maintenance
# ---------------------------------------------------------------------------

def _maintenance_response(
    action: str,
    **kwargs,
):
    result = (
        run_maintenance_action(
            action,
            **kwargs,
        )
    )

    health = ""

    if (
        result.before_health
        or result.after_health
    ):

        health = (
            f" Health: "
            f"{result.before_health or 'unknown'}"
            f" -> "
            f"{result.after_health or 'unknown'}."
        )

    return _result(
        (
            f"{'Completed' if result.success else 'Could not complete'} "
            f"{result.action}. "
            f"{result.detail}"
            f"{health}"
        ).strip(),
        metadata={
            "maintenance":
                result.__dict__,
        },
    )


# ---------------------------------------------------------------------------
# Repair Preparation
# ---------------------------------------------------------------------------

def _extract_component(
    text: str,
):
    normalized = (
        _normalize(
            text
        )
    )

    explicit = re.search(
        r"(?:prepare|diagnose|repair|fix)\s+(?:component\s+)?([a-z0-9_.-]+)",
        normalized,
    )

    if explicit:

        return (
            explicit.group(
                1
            )
            .replace(
                "-",
                ".",
            )
        )


    aliases = {
        "calendar":
            "integrations.capabilities",

        "google calendar":
            "integrations.capabilities",

        "gmail":
            "integrations.capabilities",

        "google tasks":
            "integrations.capabilities",

        "spotify":
            "integrations.capabilities",

        "schwab":
            "integrations.capabilities",

        "weather":
            "integrations.capabilities",

        "notion":
            "integrations.capabilities",

        "github":
            "integrations.capabilities",

        "tts":
            "voice.tts",

        "speech synthesis":
            "voice.tts",

        "stt":
            "voice.stt",

        "speech recognition":
            "voice.stt",

        "wake":
            "voice.wake",

        "voice identity":
            "voice.identity",

        "memory":
            "memory.database",

        "embeddings":
            "memory.embeddings",

        "reranker":
            "memory.reranker",

        "agent":
            "agent.runtime",

        "computer control":
            "computer.control",

        "browser":
            "browser",

        "vision":
            "vision",

        "telemetry":
            "telemetry",
    }


    for phrase, component in aliases.items():

        if phrase in normalized:

            return component


    return ""


# ---------------------------------------------------------------------------
# Live Phase 15 Router
# ---------------------------------------------------------------------------

def handle_system_message(
    user_text: str,
):
    text = (
        _normalize(
            user_text
        )
    )

    if not text:

        return _not_handled()


    # -----------------------------------------------------------------------
    # Identity / Version / Phase
    # -----------------------------------------------------------------------

    if (
        text
        in {
            "what version are you",
            "what version are you running",
            "what version is evie",
            "what version is e.v.i.e",
            "what is your version",
        }
        or "current version" in text
    ):

        awareness = (
            get_self_awareness(
                "version"
            )
        )

        return _result(
            awareness.summary
        )


    if (
        "what phase are you" in text
        or "what phase is evie" in text
        or "which phases are complete" in text
        or "what phases are complete" in text
    ):

        awareness = (
            get_self_awareness(
                "phases"
            )
        )

        return _result(
            awareness.summary
        )


    if text in {
        "who are you",
        "what are you",
        "identify yourself",
    }:

        awareness = (
            get_self_awareness(
                "identity"
            )
        )

        return _result(
            awareness.summary
        )


    # -----------------------------------------------------------------------
    # Capabilities / Integrations / Limitations
    # -----------------------------------------------------------------------

    if (
        text
        in {
            "what can you do",
            "what are your capabilities",
            "list your capabilities",
            "show your capabilities",
        }
        or "what capabilities do you have" in text
    ):

        return _result(
            _format_capabilities()
        )


    capability_match = re.match(
        r"(?:can you|do you support)\s+(.+)",
        text,
    )

    if capability_match:

        requested = (
            capability_match.group(
                1
            )
            .strip()
        )

        result = (
            get_capability_status(
                requested
            )
        )

        if result.success:

            return _result(
                result.summary
            )


    if (
        "what integrations" in text
        or "which integrations" in text
        or "what services are connected" in text
    ):

        return _result(
            _format_integrations()
        )


    if (
        "what can't you do" in text
        or "what cant you do" in text
        or "what are your limitations" in text
        or "known limitations" in text
    ):

        awareness = (
            get_self_awareness(
                "limitations"
            )
        )

        return _result(
            awareness.summary
        )


    # -----------------------------------------------------------------------
    # Health / Failure Awareness
    # -----------------------------------------------------------------------

    if text in {
        "are you healthy",
        "system status",
        "health status",
        "check your health",
        "check system health",
        "how are your systems",
        "is everything working",
        "are all systems healthy",
    }:

        return _result(
            _format_quick_health()
        )


    if (
        "what's broken" in text
        or "whats broken" in text
        or "what is broken" in text
        or "what's wrong with you" in text
        or "whats wrong with you" in text
        or "what is wrong with you" in text
        or "what is failing" in text
        or "what's failing" in text
        or "whats failing" in text
    ):

        return _result(
            format_diagnostic_snapshot()
        )


    # -----------------------------------------------------------------------
    # Diagnostics
    # -----------------------------------------------------------------------

    if (
        "run a deep diagnostic" in text
        or "run deep diagnostic" in text
        or "deep diagnostic" == text
        or "deep diagnostics" == text
    ):

        return _result(
            format_deep_diagnostic_report()
        )


    if (
        "run a diagnostic" in text
        or "run diagnostic" in text
        or "diagnostic snapshot" in text
        or text == "diagnostics"
    ):

        return _result(
            format_diagnostic_snapshot()
        )


    # -----------------------------------------------------------------------
    # Performance
    # -----------------------------------------------------------------------

    if (
        "why are you slow" in text
        or "why are you so slow" in text
        or "what is your bottleneck" in text
        or "what's your bottleneck" in text
        or "whats your bottleneck" in text
        or "performance health" in text
        or "show performance" in text
        or "show your performance" in text
    ):

        return _result(
            format_performance_report()
        )


    # -----------------------------------------------------------------------
    # Certification
    # -----------------------------------------------------------------------

    if (
        "run system certification" in text
        or "run certification" in text
        or "certification status" in text
        or "are you certified" in text
    ):

        return _result(
            format_certification_report()
        )


    # -----------------------------------------------------------------------
    # Safe Maintenance
    # -----------------------------------------------------------------------

    maintenance_routes = {
        "clear stale agent state":
            "clear_stale_agent_state",

        "clear pending integration selection":
            "clear_pending_integration_selection",

        "clear failure history":
            "clear_failure_history",

        "reload tool registry":
            "reload_tool_registry",

        "reload your tool registry":
            "reload_tool_registry",

        "reload integration registry":
            "reload_integration_registry",

        "reload your integration registry":
            "reload_integration_registry",

        "rebuild missing embeddings":
            "rebuild_missing_embeddings",

        "rebuild missing memory embeddings":
            "rebuild_missing_embeddings",

        "run memory consolidation":
            "run_memory_consolidation",

        "consolidate memory":
            "run_memory_consolidation",

        "ensure runtime directories":
            "ensure_runtime_directories",
    }


    for phrase, action in maintenance_routes.items():

        if phrase in text:

            return _maintenance_response(
                action
            )


    if (
        "prune telemetry" in text
        or "clean old telemetry" in text
    ):

        return _maintenance_response(
            "prune_telemetry"
        )


    if (
        "what maintenance actions" in text
        or "list maintenance actions" in text
    ):

        actions = (
            list_maintenance_actions()
        )

        return _result(
            (
                "Available maintenance actions:\n- "
                + "\n- ".join(
                    actions
                )
            )
        )


    # -----------------------------------------------------------------------
    # Phase 15I/J - Repair Preparation Only
    # -----------------------------------------------------------------------

    if (
        text.startswith(
            "prepare repair"
        )
        or text.startswith(
            "prepare a repair"
        )
        or text.startswith(
            "prepare self repair"
        )
        or text.startswith(
            "diagnose component"
        )
    ):

        component = (
            _extract_component(
                text
            )
        )

        if not component:

            return _result(
                (
                    "I can prepare a bounded repair request, "
                    "but I need the component name."
                )
            )


        request = (
            build_repair_request(
                component
            )
        )


        if not request.found:

            return _result(
                (
                    f"No architecture ownership record exists "
                    f"for {component}."
                )
            )


        return _result(
            render_repair_prompt(
                request
            ),
            metadata={
                "repair_component":
                    component,

                "repair_ready":
                    True,
            },
        )


    return _not_handled()
