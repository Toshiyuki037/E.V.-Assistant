from pathlib import Path

import assistant.workflows.protocols as protocols


def test_protocol_crud_and_clone(tmp_path, monkeypatch):
    monkeypatch.setattr(protocols, "PROTOCOL_DIR", tmp_path / "protocols")

    p = protocols.create_protocol(
        "test",
        "Test Protocol",
        "Test reusable workflow",
        steps=[],
        default_variables={"location": "Honolulu"},
    )
    assert p["protocol_id"] == "test"
    assert protocols.get_protocol("test")["name"] == "Test Protocol"
    assert len(protocols.list_protocols()) == 1

    protocols.set_protocol_enabled("test", False)
    assert protocols.get_protocol("test")["enabled"] is False

    clone = protocols.clone_protocol("test", "test-copy")
    assert clone["protocol_id"] == "test-copy"
    assert clone["enabled"] is False

    protocols.update_protocol("test-copy", name="Changed")
    assert protocols.get_protocol("test-copy")["name"] == "Changed"

    assert protocols.delete_protocol("test-copy") is True
    assert protocols.delete_protocol("test-copy") is False
