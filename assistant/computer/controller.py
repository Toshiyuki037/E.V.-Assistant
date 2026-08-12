from .local_windows import build_local_windows_device
from .registry import get_device, list_devices, register_device

def ensure_local_device():
    existing = get_device("local-windows")
    if existing is not None:
        return existing
    return register_device(build_local_windows_device())

def describe_devices():
    ensure_local_device()
    return [device.to_dict() for device in list_devices()]
