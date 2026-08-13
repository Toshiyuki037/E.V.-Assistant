"""
E.V.I.E. - Architecture Ownership Map

Phase 15I

Purpose:
    Provides a deterministic map from E.V.I.E. components/capabilities to:
        - owning development phase
        - primary source modules
        - related tests
        - dependencies
        - risk boundary
        - repair scope

This map is read-only metadata.

It prepares the health/diagnostic system for the later self-engineering
bridge without allowing unrestricted source modification.
"""

from __future__ import annotations

from dataclasses import (
    asdict,
    dataclass,
    field,
)

from typing import (
    Any,
)


@dataclass(frozen=True)
class OwnershipRecord:
    component: str

    phase: int

    owner: str

    source_modules: tuple[str, ...] = ()

    tests: tuple[str, ...] = ()

    dependencies: tuple[str, ...] = ()

    risk: str = "medium"

    repair_paths: tuple[str, ...] = ()

    notes: str = ""

    metadata: dict[str, Any] = field(
        default_factory=dict
    )


# ---------------------------------------------------------------------------
# Canonical Ownership Registry
# ---------------------------------------------------------------------------

OWNERSHIP_MAP: dict[
    str,
    OwnershipRecord,
] = {}


def register_ownership(
    record: OwnershipRecord,
):
    key = (
        str(
            record.component
        )
        .strip()
        .lower()
    )

    if not key:
        raise ValueError(
            "Ownership component cannot be empty."
        )

    if record.risk not in {
        "low",
        "medium",
        "high",
    }:
        raise ValueError(
            f"Invalid ownership risk: {record.risk}"
        )

    OWNERSHIP_MAP[
        key
    ] = record

    return record


def get_ownership(
    component: str,
):
    key = (
        str(
            component
            or ""
        )
        .strip()
        .lower()
    )

    return OWNERSHIP_MAP.get(
        key
    )


def ownership_to_dict(
    record: OwnershipRecord,
):
    return asdict(
        record
    )


def list_ownership_records():
    return [
        OWNERSHIP_MAP[
            key
        ]

        for key
        in sorted(
            OWNERSHIP_MAP
        )
    ]


def find_ownership(
    query: str,
):
    normalized = (
        str(
            query
            or ""
        )
        .strip()
        .lower()
    )

    if not normalized:
        return []

    results = []

    for record in list_ownership_records():

        haystack = " ".join(
            [
                record.component,
                record.owner,
                " ".join(
                    record.source_modules
                ),
                " ".join(
                    record.tests
                ),
                record.notes,
            ]
        ).lower()

        if normalized in haystack:
            results.append(
                record
            )

    return results


# ---------------------------------------------------------------------------
# Default V1/V15 Ownership Definitions
# ---------------------------------------------------------------------------

def _register_defaults():
    records = [
        OwnershipRecord(
            component="memory.database",
            phase=2,
            owner="Memory",
            source_modules=(
                "assistant/memory/database.py",
            ),
            tests=(
                "tests/test_phase2_memory.py",
            ),
            dependencies=(
                "sqlite3",
            ),
            risk="medium",
            repair_paths=(
                "assistant/memory/",
            ),
            notes="Persistent SQLite conversation and long-term memory storage.",
        ),
        OwnershipRecord(
            component="memory.embeddings",
            phase=2,
            owner="Memory",
            source_modules=(
                "assistant/memory/embeddings.py",
            ),
            tests=(
                "tests/test_phase2_memory.py",
            ),
            dependencies=(
                "sentence-transformers",
                "numpy",
            ),
            risk="medium",
            repair_paths=(
                "assistant/memory/",
            ),
            notes="Semantic embedding model and embedding backfill.",
        ),
        OwnershipRecord(
            component="memory.reranker",
            phase=2,
            owner="Memory",
            source_modules=(
                "assistant/memory/retriever.py",
            ),
            dependencies=(
                "sentence-transformers",
            ),
            risk="medium",
            repair_paths=(
                "assistant/memory/",
            ),
            notes="CrossEncoder memory reranking and hybrid retrieval.",
        ),
        OwnershipRecord(
            component="tools.registry",
            phase=6,
            owner="Tools",
            source_modules=(
                "assistant/tools/registry.py",
            ),
            tests=(
                "tests/test_phase6_tools.py",
            ),
            risk="high",
            repair_paths=(
                "assistant/tools/",
            ),
            notes="Authoritative action/tool registry and default tool loading.",
        ),
        OwnershipRecord(
            component="agent.runtime",
            phase=7,
            owner="Agent",
            source_modules=(
                "assistant/agent/integration.py",
                "assistant/agent/controller.py",
            ),
            tests=(
                "tests/test_phase7_agent.py",
            ),
            dependencies=(
                "assistant.tools",
            ),
            risk="high",
            repair_paths=(
                "assistant/agent/",
            ),
            notes="Multi-step planning, continuation, execution, and task state.",
        ),
        OwnershipRecord(
            component="browser",
            phase=8,
            owner="Browser",
            source_modules=(
                "assistant/tools/browser.py",
            ),
            dependencies=(
                "playwright",
            ),
            risk="high",
            repair_paths=(
                "assistant/tools/browser.py",
                "assistant/browser/",
            ),
            notes="Structured browser interaction and research.",
        ),
        OwnershipRecord(
            component="integrations.registry",
            phase=9,
            owner="Integrations",
            source_modules=(
                "assistant/integrations/registry.py",
            ),
            tests=(
                "tests/test_phase9_integrations.py",
            ),
            risk="high",
            repair_paths=(
                "assistant/integrations/",
            ),
            notes="Provider/capability registration.",
        ),
        OwnershipRecord(
            component="integrations.accounts",
            phase=9,
            owner="Integrations",
            source_modules=(
                "assistant/integrations/accounts.py",
                "assistant/integrations/connections.py",
                "assistant/integrations/router.py",
            ),
            risk="high",
            repair_paths=(
                "assistant/integrations/",
            ),
            notes="Connected account state and routing.",
        ),
        OwnershipRecord(
            component="integrations.capabilities",
            phase=9,
            owner="Integrations",
            source_modules=(
                "assistant/integrations/capabilities.py",
                "assistant/integrations/router.py",
            ),
            risk="high",
            repair_paths=(
                "assistant/integrations/",
            ),
            notes="Account-aware integration capability availability.",
        ),
        OwnershipRecord(
            component="workflows.runtime",
            phase=11,
            owner="Workflows",
            source_modules=(
                "assistant/workflows/integration.py",
            ),
            risk="high",
            repair_paths=(
                "assistant/workflows/",
            ),
            notes="Persistent multi-step workflow runtime.",
        ),
        OwnershipRecord(
            component="computer.control",
            phase=13,
            owner="Computer Control",
            source_modules=(
                "assistant/computer/integration.py",
                "assistant/computer/integration_planner.py",
                "assistant/computer/integration_runtime.py",
            ),
            tests=(
                "tests/test_phase13_computer_control.py",
            ),
            risk="high",
            repair_paths=(
                "assistant/computer/",
            ),
            notes="Structured Windows computer-control boundary.",
        ),
        OwnershipRecord(
            component="vision",
            phase=5,
            owner="Vision",
            source_modules=(
                "assistant/vision/",
                "assistant/perception/",
            ),
            risk="medium",
            repair_paths=(
                "assistant/vision/",
                "assistant/perception/",
            ),
            notes="Visual understanding and perception fallback.",
        ),
        OwnershipRecord(
            component="voice.stt",
            phase=14,
            owner="Voice",
            source_modules=(
                "assistant/listen.py",
                "assistant/voice/stt_config.py",
            ),
            tests=(
                "tests/test_phase14_english_stt_config.py",
            ),
            dependencies=(
                "faster-whisper",
            ),
            risk="medium",
            repair_paths=(
                "assistant/listen.py",
                "assistant/voice/",
            ),
            notes="Streaming STT, VAD, and transcript finalization.",
        ),
        OwnershipRecord(
            component="voice.tts",
            phase=14,
            owner="Voice",
            source_modules=(
                "assistant/speak.py",
                "assistant/voice/playback.py",
                "assistant/voice/authoritative_speech.py",
            ),
            dependencies=(
                "f5-tts",
                "sounddevice",
                "soundfile",
            ),
            risk="medium",
            repair_paths=(
                "assistant/speak.py",
                "assistant/voice/",
            ),
            notes="Speech synthesis and playback.",
        ),
        OwnershipRecord(
            component="voice.wake",
            phase=14,
            owner="Voice",
            source_modules=(
                "assistant/voice/session.py",
                "assistant/voice/wake.py",
            ),
            risk="medium",
            repair_paths=(
                "assistant/voice/",
            ),
            notes="Wake, standby, and session timeout behavior.",
        ),
        OwnershipRecord(
            component="voice.identity",
            phase=14,
            owner="Voice Security",
            source_modules=(
                "assistant/voice/authentication.py",
                "assistant/voice/voiceprint.py",
            ),
            risk="high",
            repair_paths=(
                "assistant/voice/",
            ),
            notes="Voice identity verification as one authentication signal.",
        ),
        OwnershipRecord(
            component="telemetry",
            phase=14,
            owner="Telemetry",
            source_modules=(
                "assistant/telemetry/reporter.py",
            ),
            risk="low",
            repair_paths=(
                "assistant/telemetry/",
            ),
            notes="Per-request telemetry persistence and latency reporting.",
        ),
        OwnershipRecord(
            component="system.manifest",
            phase=15,
            owner="System",
            source_modules=(
                "assistant/system/manifest.py",
            ),
            tests=(
                "tests/test_system_manifest.py",
            ),
            risk="low",
            repair_paths=(
                "assistant/system/",
            ),
            notes="Authoritative self-awareness manifest.",
        ),
        OwnershipRecord(
            component="system.health",
            phase=15,
            owner="System",
            source_modules=(
                "assistant/system/health.py",
                "assistant/system/component_health.py",
                "assistant/system/failures.py",
                "assistant/system/diagnostic_state.py",
                "assistant/system/performance.py",
                "assistant/system/deep_diagnostics.py",
            ),
            tests=(
                "tests/test_system_health.py",
                "tests/test_system_component_health.py",
                "tests/test_system_failures.py",
                "tests/test_system_performance.py",
                "tests/test_system_deep_diagnostics.py",
            ),
            risk="medium",
            repair_paths=(
                "assistant/system/",
            ),
            notes="Health, diagnostics, performance, and failure state.",
        ),
        OwnershipRecord(
            component="system.maintenance",
            phase=15,
            owner="System",
            source_modules=(
                "assistant/system/maintenance.py",
            ),
            tests=(
                "tests/test_system_maintenance.py",
            ),
            risk="medium",
            repair_paths=(
                "assistant/system/",
            ),
            notes="Safe operational maintenance and recovery.",
        ),
    ]

    for record in records:
        register_ownership(
            record
        )


_register_defaults()
