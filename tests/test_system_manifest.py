from assistant.system.manifest import (
    EVIE_VERSION, capability_supported, completed_phase,
    get_capability, get_system_manifest, list_capabilities,
)

def test_manifest_identity():
    m = get_system_manifest()
    assert m["name"] == "E.V.I.E."
    assert m["version"] == EVIE_VERSION
    assert m["current_phase"] == 15

def test_completed_v1_phases():
    assert all(completed_phase(n) for n in range(1, 15))
    assert not completed_phase(15)

def test_core_capabilities():
    for name in ("voice_input", "memory", "computer_control", "agent", "telemetry"):
        assert capability_supported(name)

def test_future_capabilities_fail_closed():
    assert not capability_supported("multi_device")
    assert not capability_supported("self_hosted_llm")
    assert not capability_supported("invented capability")

def test_normalized_capability_lookup():
    assert get_capability("Computer Control")["supported"] is True

def test_supported_filter():
    caps = list_capabilities(supported_only=True)
    assert "memory" in caps
    assert "multi_device" not in caps

def test_defensive_copy():
    m = get_system_manifest()
    m["name"] = "BROKEN"
    assert get_system_manifest()["name"] == "E.V.I.E."
