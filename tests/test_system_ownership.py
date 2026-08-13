from assistant.system.ownership import (
    find_ownership,
    get_ownership,
    list_ownership_records,
)


def test_known_component_ownership():
    record = (
        get_ownership(
            "computer.control"
        )
    )

    assert record is not None
    assert record.phase == 13
    assert record.owner == "Computer Control"
    assert "assistant/computer/" in record.repair_paths


def test_voice_component_ownership():
    record = (
        get_ownership(
            "voice.tts"
        )
    )

    assert record is not None
    assert record.phase == 14
    assert record.risk == "medium"


def test_unknown_component_has_no_owner():
    assert (
        get_ownership(
            "invented.component"
        )
        is None
    )


def test_find_ownership_by_module():
    results = (
        find_ownership(
            "assistant/system/health.py"
        )
    )

    assert any(
        result.component
        == "system.health"

        for result
        in results
    )


def test_ownership_registry_is_populated():
    records = (
        list_ownership_records()
    )

    assert len(
        records
    ) >= 10
