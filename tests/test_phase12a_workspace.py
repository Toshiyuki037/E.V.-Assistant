"""
Phase 12A - Unified Workspace Model Tests
"""

import assistant.workspace.evidence as store

from assistant.workspace.controller import (
    create_entity,
    create_evidence,
    create_relationship,
)

from assistant.workspace.models import (
    ENTITY_FILE,
    ENTITY_REPOSITORY,
    REL_CONTAINS,
    SOURCE_CODE,
)


def patch_directories(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(
        store,
        "WORKSPACE_RUNTIME",
        tmp_path
        / "workspace",
    )

    monkeypatch.setattr(
        store,
        "EVIDENCE_DIRECTORY",
        tmp_path
        / "workspace"
        / "evidence",
    )

    monkeypatch.setattr(
        store,
        "ENTITY_DIRECTORY",
        tmp_path
        / "workspace"
        / "entities",
    )

    monkeypatch.setattr(
        store,
        "RELATIONSHIP_DIRECTORY",
        tmp_path
        / "workspace"
        / "relationships",
    )


def test_create_evidence(
    tmp_path,
    monkeypatch,
):
    patch_directories(
        tmp_path,
        monkeypatch,
    )

    item = create_evidence(
        source_type=SOURCE_CODE,
        source_name="local",
        source_id="assistant/workflows/engine.py",
        title="Workflow Engine",
        content="Persistent workflow execution engine.",
        repository="E.V.-Assistant",
        path="assistant/workflows/engine.py",
    )

    assert item.evidence_id
    assert item.source_type == SOURCE_CODE
    assert item.repository == "E.V.-Assistant"


def test_create_entities_and_relationship(
    tmp_path,
    monkeypatch,
):
    patch_directories(
        tmp_path,
        monkeypatch,
    )

    repo = create_entity(
        entity_type=ENTITY_REPOSITORY,
        name="E.V.-Assistant",
        repository="E.V.-Assistant",
    )

    file_entity = create_entity(
        entity_type=ENTITY_FILE,
        name="engine.py",
        repository="E.V.-Assistant",
        path="assistant/workflows/engine.py",
    )

    relationship = create_relationship(
        source_entity_id=repo.entity_id,
        target_entity_id=file_entity.entity_id,
        relationship_type=REL_CONTAINS,
    )

    assert relationship.source_entity_id == repo.entity_id
    assert relationship.target_entity_id == file_entity.entity_id
    assert relationship.relationship_type == REL_CONTAINS


def test_stable_entity_ids(
    tmp_path,
    monkeypatch,
):
    patch_directories(
        tmp_path,
        monkeypatch,
    )

    first = create_entity(
        entity_type=ENTITY_FILE,
        name="engine.py",
        repository="E.V.-Assistant",
        path="assistant/workflows/engine.py",
    )

    second = create_entity(
        entity_type=ENTITY_FILE,
        name="engine.py",
        repository="E.V.-Assistant",
        path="assistant/workflows/engine.py",
    )

    assert first.entity_id == second.entity_id


def test_cross_source_evidence_can_share_entity(
    tmp_path,
    monkeypatch,
):
    patch_directories(
        tmp_path,
        monkeypatch,
    )

    file_entity = create_entity(
        entity_type=ENTITY_FILE,
        name="engine.py",
        repository="E.V.-Assistant",
        path="assistant/workflows/engine.py",
    )

    local = create_evidence(
        source_type="local_file",
        source_name="workspace",
        source_id="local-engine",
        title="engine.py",
        content="Local source file.",
        repository="E.V.-Assistant",
        path="assistant/workflows/engine.py",
        entity_ids=[
            file_entity.entity_id
        ],
    )

    github = create_evidence(
        source_type="github",
        source_name="github",
        source_id="commit-123",
        title="Workflow engine commit",
        content="Commit modified engine.py.",
        repository="E.V.-Assistant",
        entity_ids=[
            file_entity.entity_id
        ],
    )

    assert (
        file_entity.entity_id
        in local.entity_ids
    )

    assert (
        file_entity.entity_id
        in github.entity_ids
    )
