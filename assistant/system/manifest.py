"""E.V.I.E. Phase 15A — authoritative system manifest."""
from __future__ import annotations
from copy import deepcopy
from typing import Any

EVIE_VERSION = "1.0.0"

SYSTEM_MANIFEST: dict[str, Any] = {
    "name": "E.V.I.E.",
    "version": EVIE_VERSION,
    "release": "Version 1 Foundation",
    "platform": "Windows",
    "python": "3.11",
    "purpose": "Personal engineering AI assistant for voice, memory, research, coding, connected services, controlled computer operation, and multi-step workflows.",
    "completed_phases": list(range(1, 15)),
    "current_phase": 15,
    "capabilities": {
        "conversation": {"supported": True, "description": "Text and voice conversation."},
        "voice_input": {"supported": True, "description": "Streaming STT, VAD, and partial transcription."},
        "voice_output": {"supported": True, "description": "Custom F5-TTS voice synthesis."},
        "wake_system": {"supported": True, "description": "Wake, standby, and session timeout behavior."},
        "voice_identity": {"supported": True, "description": "Voiceprint verification as one authentication signal."},
        "memory": {"supported": True, "description": "Persistent selective memory with semantic retrieval, reranking, update, forget, and consolidation."},
        "computer_awareness": {"supported": True, "description": "Local workspace and computer context."},
        "local_knowledge": {"supported": True, "description": "Local files, repositories, documents, and project knowledge."},
        "vision": {"supported": True, "description": "Screen and image interpretation."},
        "computer_control": {"supported": True, "description": "Risk-aware controlled computer actions."},
        "agent": {"supported": True, "description": "Multi-step planning, execution, verification, and recovery."},
        "browser": {"supported": True, "description": "Structured browser interaction and web research."},
        "connected_services": {"supported": True, "description": "Provider-independent external integrations."},
        "workflows": {"supported": True, "description": "Persistent workflows and protocols."},
        "research": {"supported": True, "description": "Cross-source research workflows."},
        "coding": {"supported": True, "description": "Repository-level coding and maintenance workflows."},
        "telemetry": {"supported": True, "description": "Request latency and execution telemetry."},
        "system_health": {"supported": True, "description": "Phase 15 health and diagnostics framework."},
        "multi_device": {"supported": False, "description": "Planned client/server architecture."},
        "self_hosted_llm": {"supported": False, "description": "Planned local/custom inference architecture."},
    },
    "integrations": {
        "google": ["gmail", "calendar", "tasks", "contacts"],
        "spotify": ["playback", "search", "device_control"],
        "schwab": ["portfolio", "balances", "positions", "transactions", "market_data"],
        "weather": ["current", "daily_forecast", "hourly_forecast"],
        "github": ["repositories", "commits", "issues", "pull_requests", "workflows"],
        "notion": ["search", "read", "append", "edit"],
    },
    "security": {
        "credential_storage": "Operating-system credential backend/keyring.",
        "voice_identity_is_sole_authorization": False,
        "dangerous_actions_require_explicit_approval": True,
        "brokerage_architecture": "Read-only.",
        "unknown_actions": "Fail closed.",
    },
    "known_limitations": [
        "Multi-device/server operation is not part of the completed V1 foundation.",
        "Local/custom LLM inference is not yet the primary reasoning backend.",
        "Runtime availability may differ from architectural support.",
        "Voice identity does not replace explicit approval for dangerous actions.",
    ],
}

def get_system_manifest() -> dict[str, Any]:
    return deepcopy(SYSTEM_MANIFEST)

def list_capabilities(*, supported_only: bool = False) -> dict[str, dict[str, Any]]:
    capabilities = get_system_manifest()["capabilities"]
    if not supported_only:
        return capabilities
    return {name: value for name, value in capabilities.items() if value.get("supported")}

def get_capability(name: str) -> dict[str, Any] | None:
    normalized = str(name).strip().lower().replace("-", "_").replace(" ", "_")
    value = SYSTEM_MANIFEST["capabilities"].get(normalized)
    return deepcopy(value) if value is not None else None

def capability_supported(name: str) -> bool:
    value = get_capability(name)
    return bool(value and value.get("supported"))

def completed_phase(phase: int) -> bool:
    try:
        number = int(phase)
    except (TypeError, ValueError):
        return False
    return number in SYSTEM_MANIFEST["completed_phases"]
