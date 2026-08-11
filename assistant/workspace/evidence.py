"""
E.V.I.E. - Workspace Evidence Store

Phase 12A

Purpose:
Persist normalized cross-source workspace evidence and entities.

This is deliberately a simple JSON-backed V1 store.
Later Phase 12 components can add embeddings/indexes without changing
the public evidence model.
"""

from __future__ import annotations

import json

from pathlib import Path

from .models import (
    EvidenceItem,
    WorkspaceEntity,
    WorkspaceRelationship,
    evidence_from_dict,
    evidence_to_dict,
    entity_from_dict,
    entity_to_dict,
    relationship_from_dict,
    relationship_to_dict,
)


PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[2]
)

WORKSPACE_RUNTIME = (
    PROJECT_ROOT
    / "runtime"
    / "workspace"
)

EVIDENCE_DIRECTORY = (
    WORKSPACE_RUNTIME
    / "evidence"
)

ENTITY_DIRECTORY = (
    WORKSPACE_RUNTIME
    / "entities"
)

RELATIONSHIP_DIRECTORY = (
    WORKSPACE_RUNTIME
    / "relationships"
)


def ensure_workspace_runtime():
    for directory in (
        EVIDENCE_DIRECTORY,
        ENTITY_DIRECTORY,
        RELATIONSHIP_DIRECTORY,
    ):

        directory.mkdir(
            parents=True,
            exist_ok=True,
        )


def _safe_name(
    value: str,
):
    return (
        str(
            value
            or ""
        )
        .replace(
            "/",
            "_",
        )
        .replace(
            "\\",
            "_",
        )
        .replace(
            ":",
            "_",
        )
    )


def _write_json(
    path: Path,
    payload: dict,
):
    ensure_workspace_runtime()

    temporary = (
        path.with_suffix(
            path.suffix
            + ".tmp"
        )
    )

    temporary.write_text(
        json.dumps(
            payload,
            indent=2,
            ensure_ascii=False,
            default=str,
        ),
        encoding="utf-8",
    )

    temporary.replace(
        path
    )


def _read_json(
    path: Path,
):
    try:

        value = json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )

    except (
        OSError,
        json.JSONDecodeError,
    ):

        return None

    return (
        value
        if isinstance(
            value,
            dict,
        )
        else None
    )


# ---------------------------------------------------------------------------
# Evidence
# ---------------------------------------------------------------------------

def evidence_path(
    evidence_id: str,
):
    return (
        EVIDENCE_DIRECTORY
        / (
            _safe_name(
                evidence_id
            )
            + ".json"
        )
    )


def save_evidence(
    item: EvidenceItem,
):
    _write_json(
        evidence_path(
            item.evidence_id
        ),
        evidence_to_dict(
            item
        ),
    )

    return item


def load_evidence(
    evidence_id: str,
):
    path = evidence_path(
        evidence_id
    )

    if not path.exists():

        return None

    data = _read_json(
        path
    )

    if data is None:

        return None

    return evidence_from_dict(
        data
    )


def list_evidence():
    ensure_workspace_runtime()

    results = []

    for path in sorted(
        EVIDENCE_DIRECTORY.glob(
            "*.json"
        )
    ):

        data = _read_json(
            path
        )

        if data is None:

            continue

        results.append(
            evidence_from_dict(
                data
            )
        )

    return results


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------

def entity_path(
    entity_id: str,
):
    return (
        ENTITY_DIRECTORY
        / (
            _safe_name(
                entity_id
            )
            + ".json"
        )
    )


def save_entity(
    item: WorkspaceEntity,
):
    _write_json(
        entity_path(
            item.entity_id
        ),
        entity_to_dict(
            item
        ),
    )

    return item


def load_entity(
    entity_id: str,
):
    path = entity_path(
        entity_id
    )

    if not path.exists():

        return None

    data = _read_json(
        path
    )

    if data is None:

        return None

    return entity_from_dict(
        data
    )


def list_entities():
    ensure_workspace_runtime()

    results = []

    for path in sorted(
        ENTITY_DIRECTORY.glob(
            "*.json"
        )
    ):

        data = _read_json(
            path
        )

        if data is None:

            continue

        results.append(
            entity_from_dict(
                data
            )
        )

    return results


# ---------------------------------------------------------------------------
# Relationships
# ---------------------------------------------------------------------------

def relationship_path(
    relationship_id: str,
):
    return (
        RELATIONSHIP_DIRECTORY
        / (
            _safe_name(
                relationship_id
            )
            + ".json"
        )
    )


def save_relationship(
    item: WorkspaceRelationship,
):
    _write_json(
        relationship_path(
            item.relationship_id
        ),
        relationship_to_dict(
            item
        ),
    )

    return item


def load_relationship(
    relationship_id: str,
):
    path = relationship_path(
        relationship_id
    )

    if not path.exists():

        return None

    data = _read_json(
        path
    )

    if data is None:

        return None

    return relationship_from_dict(
        data
    )


def list_relationships():
    ensure_workspace_runtime()

    results = []

    for path in sorted(
        RELATIONSHIP_DIRECTORY.glob(
            "*.json"
        )
    ):

        data = _read_json(
            path
        )

        if data is None:

            continue

        results.append(
            relationship_from_dict(
                data
            )
        )

    return results
