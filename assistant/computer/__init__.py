"""
E.V.I.E. - Computer & Device Control
Phase 13A
"""
from .models import DeviceCapability, DeviceDescriptor, DeviceKind, DeviceRisk
from .registry import clear_device_registry, get_device, list_devices, register_device
from .local_windows import build_local_windows_device
