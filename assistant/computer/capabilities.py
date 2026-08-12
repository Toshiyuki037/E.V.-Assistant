from .models import DeviceRisk

ACTION_RISKS: dict[str, DeviceRisk] = {
    "system.get_state": DeviceRisk.READ,
    "window.list": DeviceRisk.READ,
    "window.foreground": DeviceRisk.READ,
    "process.list": DeviceRisk.READ,
    "clipboard.read": DeviceRisk.READ,
    "audio.list_devices": DeviceRisk.READ,
    "camera.list": DeviceRisk.READ,
    "window.focus": DeviceRisk.LOW,
    "window.move": DeviceRisk.LOW,
    "window.minimize": DeviceRisk.LOW,
    "window.maximize": DeviceRisk.LOW,
    "application.launch": DeviceRisk.LOW,
    "notification.send": DeviceRisk.LOW,
    "audio.set_volume": DeviceRisk.LOW,
    "clipboard.write": DeviceRisk.MEDIUM,
    "filesystem.move": DeviceRisk.MEDIUM,
    "microphone.capture": DeviceRisk.MEDIUM,
    "camera.capture": DeviceRisk.MEDIUM,
    "process.terminate": DeviceRisk.MEDIUM,
    "filesystem.delete": DeviceRisk.HIGH,
    "settings.change": DeviceRisk.HIGH,
    "process.terminate_critical": DeviceRisk.HIGH,
}

def get_action_risk(action: str) -> DeviceRisk:
    return ACTION_RISKS.get(str(action), DeviceRisk.HIGH)
