from assistant.computer.capabilities import get_action_risk
from assistant.computer.controller import describe_devices, ensure_local_device
from assistant.computer.models import DeviceCapability, DeviceRisk
from assistant.computer.registry import clear_device_registry, list_devices

def setup_function():
    clear_device_registry()

def test_local_windows_device_registers_with_core_capabilities():
    device = ensure_local_device()
    assert device.local is True
    assert device.trusted is True
    assert device.supports(DeviceCapability.WINDOWS)
    assert device.supports(DeviceCapability.PROCESSES)
    assert device.supports(DeviceCapability.ACCESSIBILITY)

def test_registry_can_filter_by_capability():
    ensure_local_device()
    devices = list_devices(capability=DeviceCapability.CAMERA)
    assert len(devices) == 1
    assert devices[0].device_id == "local-windows"

def test_unknown_actions_fail_closed():
    assert get_action_risk("unknown.action") == DeviceRisk.HIGH

def test_device_description_is_serializable():
    result = describe_devices()
    assert result
    assert result[0]["device_id"] == "local-windows"
    assert "windows" in result[0]["capabilities"]
